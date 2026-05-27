"""
本地用量数据记录与统计分析
记录每次 API 调用的 token 用量、延迟、缓存状态等
"""
import sys
import json
import os
import random
import time
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from collections import defaultdict


if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.dirname(sys.executable)
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, "usage_log.json")


# ── 数据模型 ─────────────────────────────────────────────

class UsageRecord:
    """单次 API 调用记录"""

    def __init__(
        self,
        timestamp: str,
        model: str = "deepseek-chat",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cache_hit: bool = False,
        latency_ms: float = 0.0,
        cost: float = 0.0,
        status: str = "success",
    ):
        self.timestamp = timestamp
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.cache_hit = cache_hit
        self.latency_ms = latency_ms
        self.cost = cost
        self.status = status

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cache_hit": self.cache_hit,
            "latency_ms": round(self.latency_ms, 1),
            "cost": round(self.cost, 6),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "UsageRecord":
        return cls(
            timestamp=d["timestamp"],
            model=d.get("model", "deepseek-chat"),
            prompt_tokens=d.get("prompt_tokens", 0),
            completion_tokens=d.get("completion_tokens", 0),
            total_tokens=d.get("total_tokens", 0),
            cache_hit=d.get("cache_hit", False),
            latency_ms=d.get("latency_ms", 0.0),
            cost=d.get("cost", 0.0),
            status=d.get("status", "success"),
        )


# ── 数据管理器 ───────────────────────────────────────────

class DataLogger:
    """本地用量记录 & 统计分析"""

    def __init__(self, filepath: str = DATA_FILE):
        self.filepath = filepath
        self._records: List[UsageRecord] = []
        self._load()

    # ── 读写持久化 ────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._records = [UsageRecord.from_dict(r) for r in data]
            except (json.JSONDecodeError, KeyError):
                self._records = []

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(
                    [r.to_dict() for r in self._records[-10000:]],  # 最多保留 10000 条
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except (OSError, PermissionError):
            pass  # 静默处理文件写入冲突

    # ── 记录写入 ──────────────────────────────────────────

    def add_record(self, record: UsageRecord):
        self._records.append(record)
        self._save()

    def add_record_from_api(
        self,
        response: dict,
        latency_ms: float = 0.0,
        cache_hit: bool = False,
    ):
        """从 API 响应中提取用量并记录"""
        usage = response.get("usage", {})
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            model=response.get("model", "deepseek-chat"),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cache_hit=cache_hit,
            latency_ms=latency_ms,
            cost=usage.get("cost", 0.0),
            status="success",
        )
        self.add_record(record)
        return record

    # ── 查询统计 ──────────────────────────────────────────

    @property
    def records(self) -> List[UsageRecord]:
        return self._records

    def get_records_by_date(self, target_date: date) -> List[UsageRecord]:
        """获取某天的所有记录"""
        result = []
        for r in self._records:
            try:
                d = datetime.fromisoformat(r.timestamp).date()
                if d == target_date:
                    result.append(r)
            except (ValueError, TypeError):
                continue
        return result

    def get_records_by_range(self, start: date, end: date) -> List[UsageRecord]:
        """获取日期范围内的记录"""
        result = []
        for r in self._records:
            try:
                d = datetime.fromisoformat(r.timestamp).date()
                if start <= d <= end:
                    result.append(r)
            except (ValueError, TypeError):
                continue
        return result

    def daily_stats(self, target_date: date) -> dict:
        """某天的汇总统计"""
        records = self.get_records_by_date(target_date)
        if not records:
            return {
                "date": target_date.isoformat(),
                "total_calls": 0,
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "cache_hit_rate": 0.0,
                "total_cost": 0.0,
                "avg_latency_ms": 0.0,
                "models": {},
            }

        total = len(records)
        cache_hits = sum(1 for r in records if r.cache_hit)
        cache_misses = total - cache_hits

        return {
            "date": target_date.isoformat(),
            "total_calls": total,
            "total_tokens": sum(r.total_tokens for r in records),
            "prompt_tokens": sum(r.prompt_tokens for r in records),
            "completion_tokens": sum(r.completion_tokens for r in records),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "cache_hit_rate": (cache_hits / total * 100) if total > 0 else 0,
            "total_cost": sum(r.cost for r in records),
            "avg_latency_ms": sum(r.latency_ms for r in records) / total if total > 0 else 0,
            "models": self._model_stats(records),
        }

    def range_stats(self, start: date, end: date) -> dict:
        """日期范围内每日统计列表"""
        daily = []
        current = start
        while current <= end:
            daily.append(self.daily_stats(current))
            current += timedelta(days=1)
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "daily": daily,
            "summary": self._aggregate_stats(daily),
        }

    def _model_stats(self, records: List[UsageRecord]) -> dict:
        models = defaultdict(lambda: {"calls": 0, "tokens": 0})
        for r in records:
            models[r.model]["calls"] += 1
            models[r.model]["tokens"] += r.total_tokens
        return dict(models)

    def _aggregate_stats(self, daily_list: List[dict]) -> dict:
        return {
            "total_calls": sum(d["total_calls"] for d in daily_list),
            "total_tokens": sum(d["total_tokens"] for d in daily_list),
            "total_cost": sum(d["total_cost"] for d in daily_list),
        }

    # ── 模拟数据（用于无 API Key 时演示） ─────────────────

    def generate_mock_data(self, days: int = 30):
        """生成模拟历史数据用于展示"""
        now = datetime.now()
        models = ["deepseek-chat", "deepseek-coder"]
        records = []

        for d in range(days, 0, -1):
            day = now - timedelta(days=d)
            num_calls = random.randint(5, 30)
            for _ in range(num_calls):
                hour = random.randint(6, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                ts = day.replace(hour=hour, minute=minute, second=second)
                prompt = random.randint(100, 3000)
                completion = random.randint(50, 2000)
                total = prompt + completion
                cache = random.random() < 0.65  # ~65% cache hit rate
                latency = random.gauss(800, 300)
                model = random.choice(models)

                cost = total * 0.000002  # 模拟费率

                records.append(UsageRecord(
                    timestamp=ts.isoformat(),
                    model=model,
                    prompt_tokens=prompt,
                    completion_tokens=completion,
                    total_tokens=total,
                    cache_hit=cache,
                    latency_ms=max(50, latency),
                    cost=cost,
                    status="success",
                ))

        self._records = records
        self._save()

    def get_total_records_count(self) -> int:
        return len(self._records)
