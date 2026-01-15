from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.zones.base_zone_screen import BaseZoneScreen
from app.ui.widgets.cards import StatCard
from app.ui.widgets.buttons import PrimaryButton, DangerButton
from app.ui.widgets.tables import DataTable
from app.utils.formatting import Formatter


class SterileZoneScreen(BaseZoneScreen):

    load_sterilizer = Signal(int)
    check_ci = Signal(int)
    check_bi = Signal(int)
    release_item = Signal(int)
    reject_item = Signal(int, str)
    store_item = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__("Steril Alan", Colors.STERILE_ZONE, parent)
        self._setup_ui()

    def _setup_ui(self):
        stats = self._create_stats()
        self.add_section(stats)

        sterilizing_section = self._create_sterilizing_section()
        self.add_section(sterilizing_section)

        pending_release_section = self._create_pending_release_section()
        self.add_section(pending_release_section)

        released_section = self._create_released_section()
        self.add_section(released_section)

    def _create_stats(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(16)

        self.stat_sterilizing = StatCard("Sterilizasyonda", "0", "", Colors.INFO)
        self.stat_pending_ci = StatCard("CI Bekliyor", "0", "", Colors.WARNING)
        self.stat_pending_bi = StatCard("BI Bekliyor", "0", "", Colors.WARNING)
        self.stat_pending_release = StatCard("Onay Bekliyor", "0", "", Colors.SECONDARY)
        self.stat_released = StatCard("Onaylandi", "0", "", Colors.SUCCESS)

        layout.addWidget(self.stat_sterilizing)
        layout.addWidget(self.stat_pending_ci)
        layout.addWidget(self.stat_pending_bi)
        layout.addWidget(self.stat_pending_release)
        layout.addWidget(self.stat_released)

        return frame

    def _create_sterilizing_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)

        header = QHBoxLayout()
        title = QLabel("Sterilizasyonda")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.sterilizing_table = DataTable([
            {'key': 'cycle_number', 'title': 'Cevrim', 'width': 120},
            {'key': 'machine_name', 'title': 'Makine', 'width': 150},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'start_time', 'title': 'Baslangic', 'width': 100,
             'formatter': lambda v, r: Formatter.format_time(v) if v else ''},
            {'key': 'status', 'title': 'Durum', 'width': 100,
             'formatter': lambda v, r: Formatter.status_text(v)},
        ])

        layout.addWidget(self.sterilizing_table)

        return frame

    def _create_pending_release_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)

        header = QHBoxLayout()
        title = QLabel("Onay Bekleyen")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.pending_table = DataTable([
            {'key': 'record_number', 'title': 'Kayit No', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'ci_result', 'title': 'CI', 'width': 80,
             'formatter': lambda v, r: Formatter.status_text(v)},
            {'key': 'bi_result', 'title': 'BI', 'width': 80,
             'formatter': lambda v, r: Formatter.status_text(v)},
            {'key': 'status', 'title': 'Durum', 'width': 120,
             'formatter': lambda v, r: Formatter.status_text(v)},
        ])

        layout.addWidget(self.pending_table)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        ci_btn = PrimaryButton("CI Kontrol")
        ci_btn.clicked.connect(self._on_check_ci)

        bi_btn = PrimaryButton("BI Oku")
        bi_btn.clicked.connect(self._on_check_bi)

        release_btn = PrimaryButton("Onayla")
        release_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.SUCCESS_DARK};
            }}
        """)
        release_btn.clicked.connect(self._on_release)

        reject_btn = DangerButton("Reddet")
        reject_btn.clicked.connect(self._on_reject)

        buttons.addStretch()
        buttons.addWidget(ci_btn)
        buttons.addWidget(bi_btn)
        buttons.addWidget(release_btn)
        buttons.addWidget(reject_btn)
        layout.addLayout(buttons)

        return frame

    def _create_released_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(frame)

        header = QHBoxLayout()
        title = QLabel("Onaylananlar")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.released_table = DataTable([
            {'key': 'record_number', 'title': 'Kayit No', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'released_at', 'title': 'Onay Tarihi', 'width': 120,
             'formatter': lambda v, r: Formatter.format_datetime(v) if v else ''},
            {'key': 'expiry_date', 'title': 'Son Kullanim', 'width': 120,
             'formatter': lambda v, r: Formatter.format_date(v) if v else ''},
            {'key': 'storage_location', 'title': 'Depo', 'width': 100},
        ])

        layout.addWidget(self.released_table)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        store_btn = PrimaryButton("Depola")
        store_btn.clicked.connect(self._on_store)

        buttons.addStretch()
        buttons.addWidget(store_btn)
        layout.addLayout(buttons)

        return frame

    def _on_check_ci(self):
        data = self.pending_table.get_selected_data()
        if data.get('id'):
            self.check_ci.emit(data['id'])

    def _on_check_bi(self):
        data = self.pending_table.get_selected_data()
        if data.get('id'):
            self.check_bi.emit(data['id'])

    def _on_release(self):
        data = self.pending_table.get_selected_data()
        if data.get('id'):
            self.release_item.emit(data['id'])

    def _on_reject(self):
        data = self.pending_table.get_selected_data()
        if data.get('id'):
            self.reject_item.emit(data['id'], "")

    def _on_store(self):
        data = self.released_table.get_selected_data()
        if data.get('id'):
            self.store_item.emit(data['id'], "DEPO-A1")

    def update_stats(self, sterilizing: int, pending_ci: int, pending_bi: int,
                    pending_release: int, released: int):
        self.stat_sterilizing.set_value(str(sterilizing))
        self.stat_pending_ci.set_value(str(pending_ci))
        self.stat_pending_bi.set_value(str(pending_bi))
        self.stat_pending_release.set_value(str(pending_release))
        self.stat_released.set_value(str(released))

    def set_sterilizing_data(self, data: list):
        self.sterilizing_table.set_data(data)

    def set_pending_data(self, data: list):
        self.pending_table.set_data(data)

    def set_released_data(self, data: list):
        self.released_table.set_data(data)
