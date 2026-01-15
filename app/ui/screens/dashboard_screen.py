from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.widgets.cards import StatCard
from app.ui.widgets.inputs import BarcodeInput
from app.ui.widgets.buttons import PrimaryButton
from app.core.session import current_session


class DashboardScreen(QWidget):

    barcode_scanned = Signal(str)
    zone_selected = Signal(str)
    logout_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        header = self._create_header()
        layout.addLayout(header)

        barcode_section = self._create_barcode_section()
        layout.addWidget(barcode_section)

        stats = self._create_stats_section()
        layout.addLayout(stats)

        zones = self._create_zones_section()
        layout.addWidget(zones)

        layout.addStretch()

    def _create_header(self):
        header = QHBoxLayout()

        left = QVBoxLayout()
        self.welcome_label = QLabel("Hos Geldiniz")
        self.welcome_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 28px;
            font-weight: bold;
        """)

        self.user_label = QLabel("")
        self.user_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 16px;
        """)

        left.addWidget(self.welcome_label)
        left.addWidget(self.user_label)

        logout_btn = PrimaryButton("Cikis")
        logout_btn.setFixedWidth(120)
        logout_btn.clicked.connect(self.logout_requested.emit)

        exit_btn = PrimaryButton("Sistemi Kapat")
        exit_btn.setFixedWidth(140)
        exit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        exit_btn.clicked.connect(self.exit_requested.emit)

        header.addLayout(left)
        header.addStretch()
        header.addWidget(logout_btn)
        header.addWidget(exit_btn)

        return header

    def _create_barcode_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(frame)

        label = QLabel("Hizli Barkod Tarama")
        label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: bold;
        """)

        self.barcode_input = BarcodeInput("Barkod okutun veya yazin...")
        self.barcode_input.barcode_scanned.connect(self.barcode_scanned.emit)

        layout.addWidget(label)
        layout.addWidget(self.barcode_input)

        return frame

    def _create_stats_section(self):
        stats = QGridLayout()
        stats.setSpacing(16)

        self.stat_pending = StatCard("Bekleyen", "0", "", Colors.WARNING)
        self.stat_washing = StatCard("Yikamada", "0", "", Colors.INFO)
        self.stat_sterile = StatCard("Sterilizasyonda", "0", "", Colors.SUCCESS)
        self.stat_ready = StatCard("Hazir", "0", "", Colors.PRIMARY)

        stats.addWidget(self.stat_pending, 0, 0)
        stats.addWidget(self.stat_washing, 0, 1)
        stats.addWidget(self.stat_sterile, 0, 2)
        stats.addWidget(self.stat_ready, 0, 3)

        return stats

    def _create_zones_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 12px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(16)

        label = QLabel("Calisma Alani Secin")
        label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 18px;
            font-weight: bold;
        """)
        layout.addWidget(label)

        zones_layout = QHBoxLayout()
        zones_layout.setSpacing(16)

        dirty_btn = self._create_zone_button("Kirli Alan", "DIRTY", Colors.DIRTY_ZONE)
        clean_btn = self._create_zone_button("Temiz Alan", "CLEAN", Colors.CLEAN_ZONE)
        sterile_btn = self._create_zone_button("Steril Alan", "STERILE", Colors.STERILE_ZONE)

        zones_layout.addWidget(dirty_btn)
        zones_layout.addWidget(clean_btn)
        zones_layout.addWidget(sterile_btn)

        layout.addLayout(zones_layout)

        return frame

    def _create_zone_button(self, text: str, zone: str, color: str):
        btn = PrimaryButton(text)
        btn.setMinimumHeight(80)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        btn.clicked.connect(lambda: self.zone_selected.emit(zone))
        return btn

    def update_user_info(self):
        if current_session.current_user:
            user = current_session.current_user
            self.user_label.setText(f"{user.full_name} - {user.role}")

    def update_stats(self, pending: int, washing: int, sterile: int, ready: int):
        self.stat_pending.set_value(str(pending))
        self.stat_washing.set_value(str(washing))
        self.stat_sterile.set_value(str(sterile))
        self.stat_ready.set_value(str(ready))

    def showEvent(self, event):
        super().showEvent(event)
        self.update_user_info()
        self.barcode_input.setFocus()
