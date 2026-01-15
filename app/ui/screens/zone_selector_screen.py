from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.widgets.buttons import PrimaryButton, SecondaryButton


class ZoneSelectorScreen(QWidget):

    zone_selected = Signal(str)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(32)

        title = QLabel("Calisma Alani Secin")
        title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 32px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(24)

        dirty = self._create_zone_card(
            "Kirli Alan",
            "Kabul ve Yikama",
            "DIRTY",
            Colors.DIRTY_ZONE
        )
        clean = self._create_zone_card(
            "Temiz Alan",
            "Kontrol ve Paketleme",
            "CLEAN",
            Colors.CLEAN_ZONE
        )
        sterile = self._create_zone_card(
            "Steril Alan",
            "Sterilizasyon ve Depolama",
            "STERILE",
            Colors.STERILE_ZONE
        )

        zones_layout.addWidget(dirty)
        zones_layout.addWidget(clean)
        zones_layout.addWidget(sterile)

        layout.addLayout(zones_layout)

        back_btn = SecondaryButton("Geri")
        back_btn.setFixedWidth(200)
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignCenter)

    def _create_zone_card(self, title: str, desc: str, zone: str, color: str):
        card = QFrame()
        card.setFixedSize(280, 320)
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border: 4px solid white;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: white;
            font-size: 24px;
            font-weight: bold;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        desc_label = QLabel(desc)
        desc_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        """)
        desc_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        card.mousePressEvent = lambda e: self.zone_selected.emit(zone)

        return card
