"""
DeepSeek API 客户端 — 余额查询 & 用量获取
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime


DEEPSEEK_BASE = "https://api.deepseek.com"
TIMEOUT = 10


class DeepSeekClient:
    """DeepSeek API 调用封装"""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
        })

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, key: str):
        self._api_key = key.strip()

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    # ── 余额查询 ─────────────────────────────────────────

    def get_balance(self) -> Optional[Dict[str, Any]]:
        """
        查询 DeepSeek 账户余额
        返回: {"total_balance": "12.50", "currency": "CNY", "to_usd": "1.75"} 或 None
        """
        if not self._api_key:
            return None
        try:
            resp = self._session.get(
                f"{DEEPSEEK_BASE}/user/balance",
                headers=self._headers(),
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                infos = data.get("balance_infos", [])
                if infos:
                    info = infos[0]
                    return {
                        "total_balance": info.get("total_balance", "0"),
                        "currency": info.get("currency", "CNY"),
                        "to_usd": info.get("to_usd", "0"),
                    }
            return None
        except requests.RequestException:
            return None

    # ── 模型列表查询 ──────────────────────────────────────

    def list_models(self) -> Optional[list]:
        """获取可用模型列表"""
        if not self._api_key:
            return None
        try:
            resp = self._session.get(
                f"{DEEPSEEK_BASE}/models",
                headers=self._headers(),
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return None
        except requests.RequestException:
            return None

    # ── Chat Completion (用于本地测试 & 记录用量) ──────────

    def chat_completion(
        self,
        model: str = "deepseek-chat",
        messages: Optional[list] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        调用 chat/completions，返回完整的 response + 用量信息
        """
        if not self._api_key:
            return None
        if messages is None:
            messages = [{"role": "user", "content": "Hi"}]
        try:
            resp = self._session.post(
                f"{DEEPSEEK_BASE}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs,
                },
                timeout=TIMEOUT * 3,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.status_code, "message": resp.text}
        except requests.RequestException as e:
            return {"error": "request_failed", "message": str(e)}

    # ── 可用性检测 ────────────────────────────────────────

    def is_available(self) -> bool:
        """检测 API Key 是否有效"""
        return self.get_balance() is not None


def format_balance(balance_info: Optional[Dict]) -> str:
    """格式化余额显示"""
    if not balance_info:
        return "—"
    try:
        amt = float(balance_info.get("total_balance", 0))
        cur = balance_info.get("currency", "CNY")
        return f"{amt:.2f} {cur}"
    except (ValueError, TypeError):
        return "—"
