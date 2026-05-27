"""
DeepSeek Dashboard — 主窗口 UI
白色主题 · 配置持久化 · 全新日期选择器
"""
import sys
import json
import os
import math
from datetime import datetime, date, timedelta

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QRectF, QPointF, QSize,
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QPainterPath, QIcon, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QDateEdit, QFrame, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QSplitter, QButtonGroup,
)

from api_client import DeepSeekClient
from data_logger import DataLogger, UsageRecord


# ═══════════════════════════════════════════════════════════════
#  配置文件路径
# ═══════════════════════════════════════════════════════════════

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".deepseek_dashboard")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config() -> dict:
    """读取本地配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict):
    """保存配置到本地文件"""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════
#  配色 — 白色主题
# ═══════════════════════════════════════════════════════════════

COLORS = {
    "bg_main": "#F5F6FA",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F0F2F8",
    "border": "#E8ECF4",
    "border_focus": "#B0C4DE",
    "text_primary": "#1E2A3A",
    "text_secondary": "#5A6C7E",
    "text_muted": "#9AABBF",
    "accent_blue": "#4A7CF7",
    "accent_green": "#34C759",
    "accent_purple": "#8E6CF7",
    "accent_orange": "#F7A035",
    "accent_red": "#FF4757",
    "accent_cyan": "#2ED1B5",
    "gradient_blue_start": "#4A7CF7",
    "gradient_blue_end": "#6C63FF",
    "gradient_green_start": "#34C759",
    "gradient_green_end": "#2ED1B5",
    "gradient_purple_start": "#8E6CF7",
    "gradient_purple_end": "#4A7CF7",
    "chart_line": "#4A7CF7",
    "chart_fill_bottom": "rgba(74, 124, 247, 0.08)",
    "cache_hit": "#34C759",
    "cache_miss": "#FF4757",
    "card_shadow": "rgba(26, 42, 74, 0.08)",
    "card_shadow_hover": "rgba(26, 42, 74, 0.14)",
    "section_title": "#2E4053",
}


# ═══════════════════════════════════════════════════════════════
#  图标绘制函数（程序化生成图标，避免 emoji 渲染问题）
# ═══════════════════════════════════════════════════════════════

def _paint_gear_icon(size: int = 24, color: QColor = None) -> QIcon:
    """绘制齿轮图标（设置按钮用）"""
    if color is None:
        color = QColor("#6B7A8F")
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(color, 2.5))
    p.setBrush(Qt.NoBrush)

    cx, cy = size / 2, size / 2
    r_outer = size * 0.42
    r_inner = size * 0.18

    # 外圈齿轮齿（6个突起）
    for i in range(6):
        angle = i * 60 - 15
        rad = angle * 3.14159 / 180
        x1 = cx + r_outer * 0.75 * math.cos(rad)
        y1 = cy + r_outer * 0.75 * math.sin(rad)
        x2 = cx + r_outer * math.cos(rad)
        y2 = cy + r_outer * math.sin(rad)
        p.drawLine(int(x1), int(y1), int(x2), int(y2))

    # 主圆环
    p.drawEllipse(
        int(cx - r_outer), int(cy - r_outer),
        int(r_outer * 2), int(r_outer * 2),
    )

    # 内圆
    p.drawEllipse(
        int(cx - r_inner), int(cy - r_inner),
        int(r_inner * 2), int(r_inner * 2),
    )

    p.end()
    return QIcon(pixmap)


def _paint_refresh_icon(size: int = 24, color: QColor = None) -> QIcon:
    """绘制刷新图标（刷新按钮用）"""
    if color is None:
        color = QColor("#6B7A8F")
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.Antialiasing)

    cx, cy = size / 2, size / 2
    r = size * 0.35
    pen = QPen(color, 2.5)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    # 弧形箭头（~270度圆弧 + 箭头）
    start_angle = 30 * 16  # 从右上开始
    span_angle = 270 * 16  # 画270度
    p.drawArc(
        int(cx - r), int(cy - r), int(r * 2), int(r * 2),
        start_angle, span_angle,
    )

    # 箭头头部（三角形）
    arrow_size = size * 0.18
    tip_x = cx + r * math.cos(30 * 3.14159 / 180)
    tip_y = cy - r * math.sin(30 * 3.14159 / 180)
    p.setBrush(color)
    p.setPen(Qt.NoPen)

    # 箭头三角形
    arrow_path = QPainterPath()
    arrow_path.moveTo(tip_x, tip_y)
    arrow_path.lineTo(
        tip_x - arrow_size, tip_y - arrow_size * 0.5,
    )
    arrow_path.lineTo(
        tip_x - arrow_size * 0.5, tip_y + arrow_size * 0.3,
    )
    arrow_path.closeSubpath()
    p.drawPath(arrow_path)

    p.end()
    return QIcon(pixmap)


# ═══════════════════════════════════════════════════════════════
#  动效数字标签
# ═══════════════════════════════════════════════════════════════

class AnimatedCounter(QLabel):
    """数字滚动动画标签"""

    def __init__(self, prefix="", suffix="", decimals=0, parent=None):
        super().__init__(parent)
        self._prefix = prefix
        self._suffix = suffix
        self._decimals = decimals
        self._target_value = 0
        self._current_value = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._steps = 30
        self._step_count = 0
        self.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 30px; font-weight: 600;")
        self._update_text(0)

    def set_value(self, value: float, animate: bool = True):
        self._target_value = value
        if not animate:
            self._current_value = value
            self._update_text(value)
            return
        self._current_value = 0
        self._step_count = 0
        self._timer.start(16)

    def _tick(self):
        self._step_count += 1
        progress = min(self._step_count / self._steps, 1.0)
        eased = 1 - (1 - progress) ** 3
        val = self._target_value * eased
        self._current_value = val
        self._update_text(val)
        if progress >= 1.0:
            self._timer.stop()
            self._update_text(self._target_value)

    def _update_text(self, val: float):
        formatted = f"{val:,.{self._decimals}f}"
        self.setText(f"{self._prefix}{formatted}{self._suffix}")


# ═══════════════════════════════════════════════════════════════
#  指标卡片
# ═══════════════════════════════════════════════════════════════

class MetricCard(QFrame):
    """现代化指标卡片 — 渐变左侧条 · 悬浮抬升 · 柔和阴影"""

    def __init__(self, title: str, icon: str, accent_color: str, parent=None):
        super().__init__(parent)
        self._accent = accent_color
        self.setObjectName("metricCard")
        self.setCursor(Qt.PointingHandCursor)
        # CSS 模拟阴影：利用多层 border 实现轻投影 + 左侧装饰条
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background: {COLORS['bg_card']};
                border: none;
                border-left: 4px solid {accent_color};
                border-radius: 16px;
                padding: 22px 22px 18px 20px;
            }}
            QFrame#metricCard:hover {{
                background: {COLORS['bg_card_hover']};
                border-left: 4px solid {accent_color};
            }}
            QFrame#metricCard:hover QLabel#cardTitle {{
                color: {COLORS['text_primary']} !important;
            }}
            QFrame#metricCard:hover QLabel#cardValue {{
                color: {accent_color} !important;
            }}
            QFrame#metricCard:hover QLabel#cardSublabel {{
                color: {COLORS['text_secondary']} !important;
            }}
        """)

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 20, 18)
        layout.setSpacing(8)

        # 图标行（大号图标 + 标题）
        top = QHBoxLayout()
        top.setSpacing(10)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 26px;")
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;"
        )
        top.addWidget(icon_label)
        top.addWidget(title_label)
        top.addStretch()
        layout.addLayout(top)

        # 数值（加大字号）
        self.counter = AnimatedCounter()
        self.counter.setObjectName("cardValue")
        self.counter.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 32px; font-weight: 650; letter-spacing: -0.5px;")

        # 副标签
        self.sublabel = QLabel("")
        self.sublabel.setObjectName("cardSublabel")
        self.sublabel.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11.5px; font-weight: 400;")

        layout.addWidget(self.counter)
        layout.addWidget(self.sublabel)

        # ── 悬浮抬升动画（translate + shadow） ──
        self._hover_anim = QPropertyAnimation(self, b"geometry")
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.OutQuad)
        self._orig_geo = None

    def enterEvent(self, event):
        self._orig_geo = self.geometry()
        g = self.geometry()
        # 向上抬 3px
        self._hover_anim.setStartValue(g)
        self._hover_anim.setEndValue(QRectF(
            g.x(), g.y() - 3, g.width(), g.height()
        ).toRect())
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._orig_geo:
            self._hover_anim.setStartValue(self.geometry())
            self._hover_anim.setEndValue(self._orig_geo)
            self._hover_anim.start()
        super().leaveEvent(event)

    def set_value(self, value: float, suffix: str = "", animate: bool = True):
        self.counter.set_value(value, animate)
        if suffix:
            self.sublabel.setText(suffix)

    def set_text(self, text: str):
        self.counter.setText(text)
        self.counter._current_value = 0
        self.counter._target_value = 0


# ═══════════════════════════════════════════════════════════════
#  Token 用量折线图（QPainter 自绘）
# ═══════════════════════════════════════════════════════════════

class TokenChart(QWidget):
    """带渐变填充的 Token 用量趋势图（适配白色主题）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.setStyleSheet(f"""
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-bottom: 2px solid {COLORS['border']}88;
            border-radius: 16px;
        """)
        self._data: list[tuple[str, float]] = []
        self._animated_progress = 0.0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_in)

    def set_data(self, data: list[tuple[str, float]]):
        self._data = data
        self._animated_progress = 0.0
        self._anim_timer.start(20)
        self.update()

    def _animate_in(self):
        self._animated_progress += 0.04
        if self._animated_progress >= 1.0:
            self._animated_progress = 1.0
            self._anim_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        data = self._data
        if not data:
            painter.setPen(QColor(COLORS["text_muted"]))
            painter.setFont(QFont("Segoe UI", 13))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无数据\n选择一个日期范围开始分析")
            return

        w = self.width()
        h = self.height()
        margin_left = 60
        margin_right = 20
        margin_top = 40
        margin_bottom = 40
        draw_w = w - margin_left - margin_right
        draw_h = h - margin_top - margin_bottom

        values = [v for _, v in data]
        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        # 浅色网格线
        painter.setPen(QPen(QColor(COLORS["border"]), 1))
        for i in range(5):
            y = margin_top + draw_h * i / 4
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))
            val = max_val * (1 - i / 4)
            painter.setPen(QColor(COLORS["text_muted"]))
            painter.setFont(QFont("Segoe UI", 9))
            label = f"{val:,.0f}" if val >= 1000 else f"{val:.0f}"
            painter.drawText(
                int(0), int(y - 8), int(margin_left - 10), 16,
                Qt.AlignRight | Qt.AlignVCenter, label,
            )
            painter.setPen(QPen(QColor(COLORS["border"]), 1))

        # 面积渐变路径
        path = QPainterPath()
        n = len(data)
        progress_n = max(2, int(n * self._animated_progress))
        active_data = data[:progress_n]

        if len(active_data) < 2:
            painter.setPen(QPen(QColor(COLORS["chart_line"]), 2))
            painter.drawText(self.rect(), Qt.AlignCenter, "加载中…")
            painter.end()
            return

        active_n = len(active_data)
        step_x = draw_w / (n - 1) if n > 1 else draw_w

        for i, (label, val) in enumerate(active_data):
            x = margin_left + step_x * i
            y_ratio = val / max_val if max_val > 0 else 0
            y = margin_top + draw_h * (1 - y_ratio)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        last_x = margin_left + step_x * (active_n - 1)
        path.lineTo(last_x, margin_top + draw_h)
        path.lineTo(margin_left, margin_top + draw_h)
        path.closeSubpath()

        # 浅色渐变填充
        grad = QLinearGradient(0, margin_top, 0, margin_top + draw_h)
        grad.setColorAt(0.0, QColor(COLORS["chart_line"]).lighter(140))
        grad.setColorAt(0.4, QColor(COLORS["chart_line"]).lighter(120))
        grad.setColorAt(1.0, QColor(COLORS["chart_line"]).lighter(160))
        grad.setColorAt(1.0, QColor("#4A7CF700"))
        painter.fillPath(path, QBrush(grad))

        # 折线
        line_path = QPainterPath()
        for i, (label, val) in enumerate(active_data):
            x = margin_left + step_x * i
            y_ratio = val / max_val if max_val > 0 else 0
            y = margin_top + draw_h * (1 - y_ratio)
            if i == 0:
                line_path.moveTo(x, y)
            else:
                line_path.lineTo(x, y)
        painter.setPen(QPen(QColor(COLORS["chart_line"]), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(line_path)

        # 数据点
        for i, (label, val) in enumerate(active_data):
            x = margin_left + step_x * i
            y_ratio = val / max_val if max_val > 0 else 0
            y = margin_top + draw_h * (1 - y_ratio)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(COLORS["chart_line"]))
            painter.drawEllipse(QPointF(x, y), 4, 4)

        # X 轴标签
        painter.setPen(QColor(COLORS["text_muted"]))
        painter.setFont(QFont("Segoe UI", 9))
        label_count = min(7, n)
        label_step = max(1, n // label_count)
        for i in range(0, n, label_step):
            x = margin_left + step_x * i
            txt = data[i][0] if i < len(data) else ""
            if len(txt) > 6:
                txt = txt[-5:]
            painter.drawText(
                int(x - 30), int(h - margin_bottom + 8), 60, 16,
                Qt.AlignCenter, txt,
            )

        # 标题
        painter.setPen(QColor(COLORS["section_title"]))
        painter.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        painter.drawText(margin_left, 16, 220, 24, Qt.AlignLeft, "📈 Token 用量趋势")


# ═══════════════════════════════════════════════════════════════
#  缓存分析环形图
# ═══════════════════════════════════════════════════════════════

class DonutChart(QWidget):
    """缓存命中/未命中环形图（适配白色主题）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.setStyleSheet(f"""
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-bottom: 2px solid {COLORS['border']}88;
            border-radius: 16px;
        """)
        self._hit = 65
        self._miss = 35
        self._animated_hit = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)

    def set_data(self, hits: int, misses: int):
        total = hits + misses
        if total == 0:
            hits, misses = 1, 0
            total = 1
        self._hit = hits / total * 100
        self._miss = misses / total * 100
        self._animated_hit = 0
        self._timer.start(20)

    def _animate(self):
        self._animated_hit += 2
        if self._animated_hit >= self._hit:
            self._animated_hit = self._hit
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        side = min(w, h) - 40
        rect = QRectF(
            (w - side) / 2,
            (h - side) / 2 + 10,
            side, side,
        )

        # 背景圆环（浅灰色）
        painter.setPen(QPen(QColor(COLORS["border"]), 20))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect, 0, 360 * 16)

        # Hit 弧
        hit_angle = int(self._animated_hit / 100 * 360 * 16)
        if hit_angle > 0:
            painter.setPen(QPen(QColor(COLORS["cache_hit"]), 20))
            painter.drawArc(rect, 90 * 16, -hit_angle)

        # Miss 弧
        miss_angle = int((100 - self._animated_hit) / 100 * 360 * 16)
        if miss_angle > 0:
            painter.setPen(QPen(QColor(COLORS["cache_miss"]), 20))
            painter.drawArc(rect, 90 * 16, miss_angle)

        # 中心百分比
        rate = self._animated_hit
        painter.setPen(QColor(COLORS["text_primary"]))
        painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{rate:.0f}%")

        # 图例
        painter.setFont(QFont("Segoe UI", 10))
        painter.setPen(QColor(COLORS["cache_hit"]))
        painter.drawText(int(rect.left() - 15), int(rect.bottom() + 25), f"✅ Hit   {self._hit:.0f}%")
        painter.setPen(QColor(COLORS["cache_miss"]))
        painter.drawText(int(rect.left() - 15), int(rect.bottom() + 45), f"❌ Miss  {self._miss:.0f}%")

        # 标题
        painter.setPen(QColor(COLORS["section_title"]))
        painter.setFont(QFont("Inter", 14, QFont.Weight.DemiBold))
        painter.drawText(int(rect.left()), int(rect.top() - 30), 220, 24, Qt.AlignLeft, "💾 缓存命中率")


# ═══════════════════════════════════════════════════════════════
#  活动记录表格
# ═══════════════════════════════════════════════════════════════

class ActivityTable(QTableWidget):
    """最近调用记录表格（适配白色主题）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-bottom: 2px solid {COLORS['border']}88;
                border-radius: 16px;
                gridline-color: {COLORS['border']};
                color: {COLORS['text_primary']};
                font-size: 12px;
                padding: 4px;
            }}
            QHeaderView::section {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                padding: 10px 12px 8px 12px;
                font-weight: 600;
                font-size: 11px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }}
            QTableWidget::item {{
                padding: 8px 10px;
                border-bottom: 1px solid {COLORS['border']}55;
            }}
            QTableWidget::item:selected {{
                background: {COLORS['accent_blue']}18;
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:hover {{
                background: {COLORS['bg_card_hover']};
            }}
        """)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["时间", "模型", "Token", "耗时", "缓存"])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)

    def load_records(self, records: list):
        self.setRowCount(len(records))
        for i, r in enumerate(records):
            try:
                dt = datetime.fromisoformat(r.timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                time_str = r.timestamp
            self._set_item(i, 0, time_str)

            self._set_item(i, 1, r.model)

            tokens = r.total_tokens
            token_str = f"{tokens:,}" if tokens >= 1000 else str(tokens)
            item = QTableWidgetItem(token_str)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 2, item)

            latency_str = f"{r.latency_ms:.0f}ms"
            item = QTableWidgetItem(latency_str)
            item.setTextAlignment(Qt.AlignCenter)
            self.setItem(i, 3, item)

            cache_icon = "✅" if r.cache_hit else "❌"
            cache_text = "Hit" if r.cache_hit else "Miss"
            item = QTableWidgetItem(f"{cache_icon} {cache_text}")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(COLORS["cache_hit"] if r.cache_hit else COLORS["cache_miss"]))
            self.setItem(i, 4, item)

    def _set_item(self, row: int, col: int, text: str):
        item = QTableWidgetItem(text)
        self.setItem(row, col, item)


# ═══════════════════════════════════════════════════════════════
#  主窗口
# ═══════════════════════════════════════════════════════════════
#  设置对话框
# ═══════════════════════════════════════════════════════════════

APP_VERSION = "v1.0.0"
GITHUB_URL = "https://github.com/Linhaochgen/DeepseekVisualizationTools"


class SettingsDialog(QDialog):
    """设置对话框 — API Key 管理 + 关于页面"""

    def __init__(self, parent=None, current_key: str = ""):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 设置")
        self.setFixedSize(540, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['bg_card']};
                border-radius: 20px;
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-family: "Inter", "PingFang SC", "Microsoft YaHei UI", sans-serif;
            }}
            QPushButton {{
                border-radius: 8px;
                padding: 7px 16px;
                font-size: 12.5px;
                font-weight: 500;
            }}
            QLineEdit {{
                background: {COLORS['bg_main']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12.5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['accent_blue']};
            }}
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {COLORS['text_muted']};
                border: none;
                padding: 10px 28px;
                font-size: 13px;
                font-weight: 500;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {COLORS['accent_blue']};
                border-bottom: 2px solid {COLORS['accent_blue']};
            }}
            QTabBar::tab:hover {{
                color: {COLORS['text_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # Tab 切换
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_api_tab(current_key), "🔑  API Key")
        self.tabs.addTab(self._build_about_tab(), "📖  关于")
        layout.addWidget(self.tabs)

    def _build_api_tab(self, current_key: str) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 16, 10, 10)
        layout.setSpacing(14)

        # 说明
        note = QLabel("输入你的 DeepSeek API Key 以查看余额和使用数据。\nKey 会安全保存在本地配置文件中，下次自动加载。")
        note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.6;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # Key 输入
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        if current_key:
            self.key_input.setText(current_key)
        self.key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("API Key:"))
        layout.addWidget(self.key_input)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_save_key = QPushButton("💾 保存 Key")
        self.btn_save_key.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_blue']};
                color: white;
            }}
            QPushButton:hover {{ background: #5B8AF8; }}
        """)
        btn_row.addWidget(self.btn_save_key)

        self.btn_clear_key = QPushButton("🗑️ 清除 Key")
        self.btn_clear_key.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg_main']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
            }}
            QPushButton:hover {{
                background: {COLORS['accent_red']}15;
                border-color: {COLORS['accent_red']}66;
                color: {COLORS['accent_red']};
            }}
        """)
        btn_row.addWidget(self.btn_clear_key)

        self.key_status = QLabel("")
        self.key_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        btn_row.addWidget(self.key_status)
        btn_row.addStretch()

        layout.addLayout(btn_row)
        layout.addStretch()

        return tab

    def _build_about_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 10)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)

        # 应用名称
        name = QLabel("🔮 DeepSeek Dashboard")
        name.setStyleSheet("font-size: 22px; font-weight: 600; color: #1A2332;")
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        # 版本号
        ver = QLabel(f"版本 {APP_VERSION}")
        ver.setStyleSheet(f"font-size: 13px; color: {COLORS['text_muted']};")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)

        layout.addSpacing(6)

        # 描述
        desc = QLabel("美观灵动的 DeepSeek API 用量监控桌面工具\n实时追踪 Token 消耗、缓存命中率与调用记录")
        desc.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']}; line-height: 1.6;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(10)

        # GitHub 链接
        gh = QLabel(f'<a href="{GITHUB_URL}" style="color: {COLORS["accent_blue"]}; text-decoration: none;">🌐 GitHub 仓库 →</a>')
        gh.setOpenExternalLinks(True)
        gh.setAlignment(Qt.AlignCenter)
        gh.setStyleSheet("font-size: 13px;")
        layout.addWidget(gh)

        layout.addSpacing(12)

        # ── 打赏作者区域 ──
        donate_title = QLabel("☕ 打赏作者")
        donate_title.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLORS['text_primary']};")
        donate_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(donate_title)

        donate_note = QLabel("如果这个工具对你有帮助，欢迎扫码打赏 ☕")
        donate_note.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']};")
        donate_note.setAlignment(Qt.AlignCenter)
        layout.addWidget(donate_note)

        # 打赏二维码（本地图片，大尺寸便于扫码）
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(__file__)
        qr_path = os.path.join(base, "pictures", "reward.jpg")
        qr_label = QLabel()
        qr_label.setFixedSize(300, 300)
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet(f"""
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 12px;
        """)
        if os.path.exists(qr_path):
            pixmap = QPixmap(qr_path)
            # 直接展示原图，不缩放，用 scroll 或撑满
            if pixmap.width() > 280 or pixmap.height() > 280:
                scaled = pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaled = pixmap
            qr_label.setPixmap(scaled)
        else:
            qr_label.setText("🧧\n二维码图片未找到\n请放入 pictures/ 目录")
            qr_label.setStyleSheet(f"font-size: 11px; color: {COLORS['text_muted']}; background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 16px; padding: 12px;")

        qr_wrap = QHBoxLayout()
        qr_wrap.addStretch()
        qr_wrap.addWidget(qr_label)
        qr_wrap.addStretch()
        layout.addLayout(qr_wrap)

        layout.addStretch()

        # 底部版权
        footer = QLabel("")
        footer.setStyleSheet(f"font-size: 10px; color: {COLORS['text_muted']};")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

        return tab

    def get_key(self) -> str:
        return self.key_input.text().strip()


# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """DeepSeek Dashboard 主窗口 — 白色主题 · 配置持久化 · 全新日期选择器"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔮 DeepSeek Dashboard")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # 核心组件
        self.api_client = DeepSeekClient()
        self.data_logger = DataLogger()

        # 自动生成模拟数据
        self.data_logger.generate_mock_data(days=30)

        # 加载已保存的 API Key
        self._saved_config = load_config()
        saved_key = self._saved_config.get("api_key", "")
        if saved_key:
            self.api_client.api_key = saved_key

        # 全局样式
        self._setup_global_style()

        # 构建 UI
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(28, 18, 28, 24)
        self._main_layout.setSpacing(16)

        self._build_header()
        self._build_metric_cards()
        self._build_date_picker()      # ← 全新日期选择器
        self._build_charts_and_table()

        # 定时刷新
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_balance)
        self._refresh_timer.start(60000)

        # 初始加载
        self._refresh_balance()
        self._refresh_usage()

        # ✨ 入场动效：卡片递进透明度动画
        QTimer.singleShot(100, lambda: self._animate_entrance())

    def _animate_entrance(self):
        """卡片递进入场：依次弹出"""
        cards = [
            self.card_balance,
            self.card_tokens,
            self.card_calls,
            self.card_cache,
        ]
        for i, card in enumerate(cards):
            QTimer.singleShot(80 * i, lambda c=card: self._fade_in_card(c))

    def _fade_in_card(self, card):
        """单卡片弹入动效（透明度 0→1 + 抬升）"""
        card.setGraphicsEffect(None)
        # 设置初始位移
        anim = QPropertyAnimation(card, b"geometry")
        g = card.geometry()
        start = QRectF(g.x(), g.y() + 12, g.width(), g.height()).toRect()
        anim.setStartValue(start)
        anim.setEndValue(g)
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.OutBack)
        anim.start()

    # ── 全局样式（白色主题） ────────────────────────────────

    def _setup_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {COLORS['bg_main']};
            }}
            /* ── 全局字体 ── */
            QWidget {{
                color: {COLORS['text_primary']};
                font-family: "Inter", "PingFang SC", "Microsoft YaHei UI", "Segoe UI", -apple-system, sans-serif;
                font-size: 13px;
                font-weight: 450;
            }}
            QFrame#metricCard {{
                background: {COLORS['bg_card']};
            }}
            QTableWidget, QTableWidget QWidget,
            QHeaderView, QHeaderView::section {{
                background: {COLORS['bg_card']};
            }}
            QSplitter {{
                background: transparent;
            }}
            QSplitter::handle {{
                background: {COLORS['border']};
            }}

            /* ── 主按钮：渐变 + 悬浮上移动画 ── */
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_blue_start']},
                    stop:1 {COLORS['gradient_blue_end']});
                color: white;
                border: none;
                border-radius: 12px;
                padding: 9px 24px;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5B8AF8,
                    stop:1 #7C78FF);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3A6CE0,
                    stop:1 #5B55E0);
            }}

            /* ── 图标按钮（设置/刷新）：圆角一致 ── */
            QPushButton#iconBtn {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QPushButton#iconBtn:hover {{
                background: {COLORS['bg_card_hover']};
                border: 1px solid {COLORS['accent_blue']}88;
                color: {COLORS['accent_blue']};
            }}

            /* ── 日期预设胶囊按钮 ── */
            QPushButton#presetBtn {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 20px;
                padding: 7px 20px;
                font-size: 12.5px;
                font-weight: 500;
            }}
            QPushButton#presetBtn:hover {{
                background: {COLORS['bg_card_hover']};
                border: 1px solid {COLORS['accent_blue']}88;
                color: {COLORS['accent_blue']};
            }}
            QPushButton#presetBtn:checked {{
                background: {COLORS['accent_blue']}12;
                border: 1px solid {COLORS['accent_blue']};
                color: {COLORS['accent_blue']};
                font-weight: 600;
            }}

            /* ── 输入框 ── */
            QLineEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 12px;
                padding: 9px 16px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLORS['accent_blue']};
                background: {COLORS['bg_card']};
            }}

            QDateEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1.5px solid {COLORS['border']};
                border-radius: 10px;
                padding: 7px 14px;
                font-size: 12px;
                min-width: 100px;
            }}
            QDateEdit:focus {{
                border: 1.5px solid {COLORS['accent_blue']};
            }}
            QDateEdit::drop-down {{
            QLineEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['accent_blue']};
                background: {COLORS['bg_card']};
            }}
            QDateEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                min-width: 100px;
            }}
            QDateEdit:focus {{
                border: 1px solid {COLORS['accent_blue']};
            }}
            QDateEdit::drop-down {{
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

    # ── 顶部标题栏 ──────────────────────────────────────────

    def _build_header(self):
        header = QWidget()
        header.setMaximumHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🔮  DeepSeek Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #1A2332; letter-spacing: -0.5px; background: transparent;")
        layout.addWidget(title)

        layout.addStretch()

        # API Key 输入
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入 DeepSeek API Key…")
        self.api_key_input.setMaximumWidth(360)
        self.api_key_input.setEchoMode(QLineEdit.Password)

        # 如果有保存的 key，显示占位提示
        saved_key = self._saved_config.get("api_key", "")
        if saved_key:
            masked = saved_key[:8] + "…" + saved_key[-4:]
            self.api_key_input.setPlaceholderText(f"已保存: {masked}")

        layout.addWidget(self.api_key_input)

        self.btn_set_key = QPushButton("✓ 连接")
        self.btn_set_key.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_blue_start']},
                    stop:1 {COLORS['gradient_blue_end']});
                color: white;
                border-radius: 12px;
                padding: 9px 20px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)
        self.btn_set_key.clicked.connect(self._set_api_key)
        layout.addWidget(self.btn_set_key)

        # 会话提示标签
        self.key_status = QLabel("")
        self.key_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        layout.addWidget(self.key_status)

        # 设置按钮
        self.btn_settings = QPushButton()
        self.btn_settings.setObjectName("iconBtn")
        self.btn_settings.setFixedSize(42, 38)
        self.btn_settings.setToolTip("设置")
        self.btn_settings.setIcon(_paint_gear_icon(20))
        self.btn_settings.setIconSize(QSize(20, 20))
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)

        # 刷新按钮
        self.btn_refresh = QPushButton()
        self.btn_refresh.setObjectName("iconBtn")
        self.btn_refresh.setFixedSize(42, 38)
        self.btn_refresh.setToolTip("刷新数据")
        self.btn_refresh.setIcon(_paint_refresh_icon(20))
        self.btn_refresh.setIconSize(QSize(20, 20))
        self.btn_refresh.clicked.connect(self._full_refresh)
        layout.addWidget(self.btn_refresh)

        self._main_layout.addWidget(header)

        # 分割线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E8ECF400, stop:0.5 {COLORS['border']}, stop:1 #E8ECF400); max-height: 1px; border: none;")
        self._main_layout.addWidget(divider)

    # ── 指标卡片 ────────────────────────────────────────────

    def _build_metric_cards(self):
        grid = QHBoxLayout()
        grid.setSpacing(14)

        self.card_balance = MetricCard("账户余额", "💰", COLORS["accent_blue"])
        self.card_balance.setMinimumWidth(200)
        grid.addWidget(self.card_balance)

        self.card_tokens = MetricCard("今日 Token 用量", "📝", COLORS["accent_green"])
        self.card_tokens.setMinimumWidth(200)
        grid.addWidget(self.card_tokens)

        self.card_calls = MetricCard("调用次数", "📞", COLORS["accent_purple"])
        self.card_calls.setMinimumWidth(200)
        grid.addWidget(self.card_calls)

        self.card_cache = MetricCard("缓存命中率", "💾", COLORS["accent_cyan"])
        self.card_cache.setMinimumWidth(200)
        grid.addWidget(self.card_cache)

        self._main_layout.addLayout(grid)

    # ── 全新日期选择器 ──────────────────────────────────────

    def _build_date_picker(self):
        """
        重新设计的日期选择器：
        - 预设快捷按钮：今日 / 近7天 / 近30天 / 自定义
        - 只有选「自定义」才显示完整的日期输入框
        - 选中状态有高亮反馈
        """
        ctrl = QWidget()
        ctrl.setMaximumHeight(50)
        layout = QHBoxLayout(ctrl)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 图标
        icon = QLabel("📅")
        icon.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(icon)

        # 预设按钮组
        self.date_btn_group = QButtonGroup(self)
        self.date_btn_group.setExclusive(True)

        presets = [
            ("today",     "今日"),
            ("week",      "近 7 天"),
            ("month",     "近 30 天"),
            ("custom",    "自定义"),
        ]

        for key, label in presets:
            btn = QPushButton(label)
            btn.setObjectName("presetBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            self.date_btn_group.addButton(btn, len(self.date_btn_group.buttons()))
            btn._preset_key = key
            layout.addWidget(btn)

        # 选中「近7天」为默认
        self.date_btn_group.buttons()[1].setChecked(True)

        # 分隔线
        sep = QLabel(" ")
        sep.setStyleSheet(f"color: {COLORS['border']}; font-size: 14px;")
        layout.addWidget(sep)

        # 自定义日期区域（默认隐藏）
        self.custom_date_widget = QWidget()
        custom_layout = QHBoxLayout(self.custom_date_widget)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(6)

        self.date_start = QDateEdit()
        self.date_start.setDate(date.today() - timedelta(days=7))
        self.date_start.setCalendarPopup(True)
        self.date_start.setStyleSheet(f"""
            QDateEdit {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                min-width: 110px;
            }}
            QDateEdit:focus {{ border: 1px solid {COLORS['accent_blue']}; }}
        """)
        custom_layout.addWidget(QLabel("从"))
        custom_layout.addWidget(self.date_start)

        self.date_end = QDateEdit()
        self.date_end.setDate(date.today())
        self.date_end.setCalendarPopup(True)
        self.date_end.setStyleSheet(self.date_start.styleSheet())
        custom_layout.addWidget(QLabel("到"))
        custom_layout.addWidget(self.date_end)

        self.custom_date_widget.setVisible(False)
        layout.addWidget(self.custom_date_widget)

        # 查询按钮
        self.btn_query = QPushButton("🔍 查询")
        self.btn_query.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['gradient_blue_start']},
                    stop:1 {COLORS['gradient_blue_end']});
                color: white;
                border-radius: 12px;
                padding: 9px 24px;
                font-weight: 600;
                font-size: 13px;
                letter-spacing: 0.3px;
            }}
            QPushButton:hover {{ background: #5B8AF8; }}
        """)
        self.btn_query.clicked.connect(self._refresh_usage)
        layout.addWidget(self.btn_query)

        layout.addStretch()

        # 状态提示
        self.status_label = QLabel("✅ 就绪")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 连接信号：点击预设按钮时切换日期区域可见性
        self.date_btn_group.buttonClicked.connect(self._on_date_preset_clicked)

        self._main_layout.addWidget(ctrl)

    def _on_date_preset_clicked(self, button):
        """预设按钮点击：切换自定义日期区 + 自动查询"""
        key = button._preset_key
        today = date.today()

        # 显示/隐藏自定义日期区
        if key == "custom":
            self.custom_date_widget.setVisible(True)
        else:
            self.custom_date_widget.setVisible(False)
            # 自动设置日期范围
            if key == "today":
                self._cached_start = today
                self._cached_end = today
            elif key == "week":
                self._cached_start = today - timedelta(days=7)
                self._cached_end = today
            elif key == "month":
                self._cached_start = today - timedelta(days=30)
                self._cached_end = today
            # 自动刷新
            self._refresh_usage()

    # ── 图表区域 ────────────────────────────────────────────

    def _build_charts_and_table(self):
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {COLORS['border']};
                border-radius: 1px;
                margin: 4px 0;
            }}
        """)

        # 上部分：Token 图表 + 环形图
        top_row = QWidget()
        top_layout = QHBoxLayout(top_row)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(14)

        self.token_chart = TokenChart()
        top_layout.addWidget(self.token_chart, stretch=3)

        self.donut = DonutChart()
        top_layout.addWidget(self.donut, stretch=1)

        splitter.addWidget(top_row)

        # 下部分：活动表格
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(6)

        table_title = QLabel("📋 最近调用记录")
        table_title.setStyleSheet(f"color: {COLORS['section_title']}; font-size: 15px; font-weight: 600; letter-spacing: 0.3px; padding-left: 4px;")
        bottom_layout.addWidget(table_title)

        self.activity_table = ActivityTable()
        bottom_layout.addWidget(self.activity_table)

        splitter.addWidget(bottom)
        splitter.setSizes([400, 300])

        self._main_layout.addWidget(splitter, stretch=1)

    # ── API Key 处理（自动保存） ────────────────────────────

    def _set_api_key(self):
        key = self.api_key_input.text().strip()
        if key:
            self.api_client.api_key = key
            # 保存到配置文件
            config = load_config()
            config["api_key"] = key
            save_config(config)
            self._saved_config = config

            # 更新占位提示
            masked = key[:8] + "…" + key[-4:]
            self.api_key_input.setPlaceholderText(f"已保存: {masked}")
            self.api_key_input.clear()
            self.api_key_input.setFocus()

            self.key_status.setText("🔑 已保存 ✓")
            self.key_status.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 11px;")

            self._refresh_balance()
            self._refresh_usage()
        else:
            self.key_status.setText("⚠️ 请输入 API Key")
            self.key_status.setStyleSheet(f"color: {COLORS['accent_orange']}; font-size: 11px;")

    # ── 打开设置对话框 ──────────────────────────────────────

    def _open_settings(self):
        dialog = SettingsDialog(
            self,
            current_key=self.api_client.api_key or self._saved_config.get("api_key", ""),
        )
        # 保存按钮
        dialog.btn_save_key.clicked.connect(lambda: self._settings_save_key(dialog))
        dialog.btn_clear_key.clicked.connect(lambda: self._settings_clear_key(dialog))
        dialog.exec()

    def _settings_save_key(self, dialog: SettingsDialog):
        key = dialog.get_key()
        if key:
            self.api_client.api_key = key
            config = load_config()
            config["api_key"] = key
            save_config(config)
            self._saved_config = config
            # 更新主界面占位提示
            masked = key[:8] + "…" + key[-4:]
            self.api_key_input.setPlaceholderText(f"已保存: {masked}")
            dialog.key_status.setText("✅ Key 已保存")
            dialog.key_status.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 11px;")
            self._refresh_balance()
            self._refresh_usage()
        else:
            dialog.key_status.setText("⚠️ 请输入有效的 API Key")
            dialog.key_status.setStyleSheet(f"color: {COLORS['accent_orange']}; font-size: 11px;")

    def _settings_clear_key(self, dialog: SettingsDialog):
        self.api_client.api_key = ""
        save_config({})
        self._saved_config = {}
        self.api_key_input.setPlaceholderText("输入 DeepSeek API Key…")
        dialog.key_input.clear()
        dialog.key_status.setText("🗑️ Key 已清除")
        dialog.key_status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self.card_balance.set_text("— 未连接 —")
        self._refresh_usage()

    # ── 数据刷新 ────────────────────────────────────────────

    def _refresh_balance(self):
        balance = self.api_client.get_balance()
        if balance:
            try:
                amt = float(balance.get("total_balance", 0))
                cur = balance.get("currency", "CNY")
                self.card_balance.set_value(amt, f"余额 · {cur}")
                self.card_balance.counter._update_text(amt)
            except (ValueError, TypeError):
                self.card_balance.set_text("—")
        else:
            if self.api_client.api_key:
                self.card_balance.set_text("获取失败")
            else:
                self.card_balance.set_text("— 未连接 —")

    def _refresh_usage(self):
        # 确定日期范围
        checked_btn = self.date_btn_group.checkedButton()
        if checked_btn:
            key = checked_btn._preset_key
        else:
            key = "week"

        today = date.today()

        if key == "custom":
            start = self.date_start.date().toPython()
            end = self.date_end.date().toPython()
        elif key == "today":
            start = end = today
        elif key == "month":
            start = today - timedelta(days=30)
            end = today
        else:  # week
            start = today - timedelta(days=7)
            end = today

        self._cached_start = start
        self._cached_end = end

        # 获取数据
        daily_records = self.data_logger.get_records_by_range(start, end)
        daily = self.data_logger.range_stats(start, end)

        # ── 更新昨日至今的今日统计 ──
        today_stats = self.data_logger.daily_stats(today)
        self.card_tokens.set_value(today_stats["total_tokens"], "tokens today")
        self.card_calls.set_value(today_stats["total_calls"], "calls today")

        cache_rate = today_stats["cache_hit_rate"]
        self.card_cache.set_value(cache_rate, "% hit rate")

        # ── 更新 Token 趋势图 ──
        chart_data = []
        for d in daily["daily"]:
            if d["total_calls"] > 0 or d["total_tokens"] > 0:
                label = d["date"][-5:]
                chart_data.append((label, d["total_tokens"]))
            else:
                label = d["date"][-5:]
                chart_data.append((label, 0))

        if chart_data:
            self.token_chart.set_data(chart_data)

        # ── 更新环形图 ──
        total_hits = sum(d["cache_hits"] for d in daily["daily"])
        total_misses = sum(d["cache_misses"] for d in daily["daily"])
        if total_hits + total_misses > 0:
            self.donut.set_data(total_hits, total_misses)

        # ── 更新活动记录表 ──
        # 按时间倒序排列，取最近 100 条
        sorted_records = sorted(
            daily_records,
            key=lambda r: r.timestamp,
            reverse=True,
        )[:100]
        self.activity_table.load_records(sorted_records)

        # ── 状态栏 ──
        summary = daily["summary"]
        self.status_label.setText(
            f"📊 {start.isoformat()} ~ {end.isoformat()}  |  "
            f"共 {summary['total_calls']} 次调用  |  "
            f"{summary['total_tokens']:,} tokens  |  "
            f"${summary['total_cost']:.4f}"
        )

    def _full_refresh(self):
        """全面刷新"""
        self._refresh_balance()
        self._refresh_usage()
        self.status_label.setText(self.status_label.text().replace("就绪", "已刷新"))


# ═══════════════════════════════════════════════════════════════
#  应用入口
# ═══════════════════════════════════════════════════════════════

def run():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    app.setApplicationName("DeepSeek Dashboard")
    app.setOrganizationName("DeepSeek")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
