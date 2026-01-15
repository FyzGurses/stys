from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors


class InfoCard(QFrame):

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self._setup_ui(title, value)

    def _setup_ui(self, title: str, value: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 12px;
        """)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: bold;
        """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class StatCard(QFrame):

    def __init__(self, title: str, value: str, icon: str = "",
                color: str = None, parent=None):
        super().__init__(parent)
        self._setup_ui(title, value, icon, color)

    def _setup_ui(self, title: str, value: str, icon: str, color: str):
        bg_color = color or Colors.SURFACE

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 12px;
            }}
        """)
        self.setMinimumHeight(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)

        left = QVBoxLayout()
        left.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        """)

        left.addWidget(self.value_label)
        left.addWidget(self.title_label)

        layout.addLayout(left)
        layout.addStretch()

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"""
                color: rgba(255, 255, 255, 0.5);
                font-size: 40px;
            """)
            layout.addWidget(icon_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class ItemCard(QFrame):

    clicked = Signal()

    def __init__(self, title: str, subtitle: str = "", status: str = "",
                parent=None):
        super().__init__(parent)
        self._setup_ui(title, subtitle, status)

    def _setup_ui(self, title: str, subtitle: str, status: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                border: 2px solid transparent;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        left = QVBoxLayout()
        left.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
            font-weight: bold;
        """)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 12px;
        """)

        left.addWidget(self.title_label)
        if subtitle:
            left.addWidget(self.subtitle_label)

        layout.addLayout(left)
        layout.addStretch()

        if status:
            self.status_label = QLabel(status)
            self._set_status_style(status)
            layout.addWidget(self.status_label)

    def _set_status_style(self, status: str):
        if status in ['RELEASED', 'COMPLETED', 'PASS']:
            bg = Colors.SUCCESS
        elif status in ['REJECTED', 'FAIL', 'ERROR']:
            bg = Colors.DANGER
        elif 'PENDING' in status:
            bg = Colors.WARNING
        else:
            bg = Colors.INFO

        self.status_label.setStyleSheet(f"""
            background-color: {bg};
            color: white;
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: bold;
        """)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
