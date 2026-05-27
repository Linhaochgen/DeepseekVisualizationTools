"""
DeepSeek Dashboard — 桌面监控应用入口
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard import MainWindow, APP_VERSION
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QLinearGradient, QBrush, QPalette


def _create_app_icon() -> QIcon:
    """生成一个简单的应用图标（蓝色渐变 D 字母）"""
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # 圆形渐变背景
    grad = QLinearGradient(0, 0, 128, 128)
    grad.setColorAt(0.0, QColor("#4A7CF7"))
    grad.setColorAt(1.0, QColor("#6C63FF"))
    painter.setBrush(QBrush(grad))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(0, 0, 128, 128, 28, 28)

    # 字母 D
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Inter", 64, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(0, 0, 128, 128, Qt.AlignCenter, "D")

    painter.end()
    return QIcon(pixmap)


def main():
    # 高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Dashboard")
    app.setApplicationDisplayName(f"DeepSeek 仪表板 {APP_VERSION}")
    app.setOrganizationName("DeepSeek Dashboard")
    app.setWindowIcon(_create_app_icon())
    app.setStyle("Fusion")

    # 强制浅色调色板（根治背景色问题）
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F5F6FA"))
    palette.setColor(QPalette.WindowText, QColor("#1E2A3A"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#F0F2F8"))
    palette.setColor(QPalette.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ToolTipText, QColor("#1E2A3A"))
    palette.setColor(QPalette.Text, QColor("#1E2A3A"))
    palette.setColor(QPalette.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ButtonText, QColor("#1E2A3A"))
    palette.setColor(QPalette.BrightText, QColor("#FF4757"))
    palette.setColor(QPalette.Highlight, QColor("#4A7CF7"))
    palette.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.Link, QColor("#4A7CF7"))
    palette.setColor(QPalette.LinkVisited, QColor("#8E6CF7"))
    app.setPalette(palette)

    # 全局字体
    font = QFont("Inter", 10)
    font.setWeight(QFont.Weight.Normal)
    app.setFont(font)

    window = MainWindow()
    window.setWindowIcon(_create_app_icon())
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
