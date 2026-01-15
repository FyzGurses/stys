from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

from app.ui.styles import Styles, Colors
from app.utils.formatting import Formatter


class StatusBadge(QLabel):

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str):
        self.status = status
        self.setText(Formatter.status_text(status))
        self.setStyleSheet(Styles.status_badge(status))
        self.setAlignment(Qt.AlignCenter)


class ZoneBadge(QLabel):

    def __init__(self, zone: str, parent=None):
        super().__init__(parent)
        self.set_zone(zone)

    def set_zone(self, zone: str):
        self.zone = zone
        self.setText(Formatter.zone_text(zone))
        self.setStyleSheet(Styles.zone_badge(zone))
        self.setAlignment(Qt.AlignCenter)


class PriorityBadge(QLabel):

    def __init__(self, priority: int, parent=None):
        super().__init__(parent)
        self.set_priority(priority)

    def set_priority(self, priority: int):
        self.priority = priority

        if priority >= 3:
            bg = Colors.DANGER
            text = "ACIL"
        elif priority == 2:
            bg = Colors.WARNING
            text = "YUKSEK"
        elif priority == 1:
            bg = Colors.INFO
            text = "NORMAL"
        else:
            bg = Colors.TEXT_DISABLED
            text = "DUSUK"

        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: white;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)


class CountBadge(QLabel):

    def __init__(self, count: int = 0, parent=None):
        super().__init__(parent)
        self.set_count(count)

    def set_count(self, count: int):
        self.count = count
        self.setText(str(count))

        if count > 0:
            self.show()
            bg = Colors.DANGER if count > 10 else Colors.PRIMARY
        else:
            self.hide()
            bg = Colors.PRIMARY

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 12px;
                font-weight: bold;
                min-width: 20px;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)
