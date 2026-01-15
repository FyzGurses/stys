from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QSize

from app.ui.styles import Styles, Colors


class PrimaryButton(QPushButton):

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(Styles.button_primary())
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class SecondaryButton(QPushButton):

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(Styles.button_secondary())
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class DangerButton(QPushButton):

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(Styles.button_danger())
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class SuccessButton(QPushButton):

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(Styles.button_success())
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(48)


class IconButton(QPushButton):

    def __init__(self, icon_text: str, parent=None):
        super().__init__(icon_text, parent)
        self.setFixedSize(QSize(48, 48))
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 24px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE};
            }}
        """)


class ZoneButton(QPushButton):

    def __init__(self, text: str, zone: str, parent=None):
        super().__init__(text, parent)
        self.zone = zone
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(60)

        colors = {
            'DIRTY': Colors.DIRTY_ZONE,
            'CLEAN': Colors.CLEAN_ZONE,
            'STERILE': Colors.STERILE_ZONE
        }
        bg_color = colors.get(zone, Colors.SURFACE)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 16px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_color};
                opacity: 0.9;
            }}
        """)
