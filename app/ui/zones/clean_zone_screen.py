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


class CleanZoneScreen(BaseZoneScreen):

    start_inspection = Signal(int)
    pass_inspection = Signal(int)
    fail_inspection = Signal(int, str)
    start_packaging = Signal(int)
    complete_packaging = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__("Temiz Alan", Colors.CLEAN_ZONE, parent)
        self._setup_ui()

    def _setup_ui(self):
        stats = self._create_stats()
        self.add_section(stats)

        inspection_section = self._create_inspection_section()
        self.add_section(inspection_section)

        packaging_section = self._create_packaging_section()
        self.add_section(packaging_section)

    def _create_stats(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(16)

        self.stat_inspect = StatCard("Kontrol", "0", "", Colors.INFO)
        self.stat_packaging = StatCard("Paketleme", "0", "", Colors.WARNING)
        self.stat_ready = StatCard("Hazir", "0", "", Colors.SUCCESS)
        self.stat_failed = StatCard("Basarisiz", "0", "", Colors.DANGER)

        layout.addWidget(self.stat_inspect)
        layout.addWidget(self.stat_packaging)
        layout.addWidget(self.stat_ready)
        layout.addWidget(self.stat_failed)

        return frame

    def _create_inspection_section(self):
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
        title = QLabel("Kontrol Bekleyen")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.inspection_table = DataTable([
            {'key': 'order_number', 'title': 'Is Emri', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'department_name', 'title': 'Bolum', 'width': 150},
            {'key': 'status', 'title': 'Durum', 'width': 100,
             'formatter': lambda v, r: Formatter.status_text(v)},
        ])

        layout.addWidget(self.inspection_table)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        pass_btn = PrimaryButton("Kontrol Gecti")
        pass_btn.clicked.connect(self._on_pass_inspection)

        fail_btn = DangerButton("Basarisiz")
        fail_btn.clicked.connect(self._on_fail_inspection)

        buttons.addStretch()
        buttons.addWidget(pass_btn)
        buttons.addWidget(fail_btn)
        layout.addLayout(buttons)

        return frame

    def _create_packaging_section(self):
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
        title = QLabel("Paketleme Bekleyen")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.packaging_table = DataTable([
            {'key': 'order_number', 'title': 'Is Emri', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'department_name', 'title': 'Bolum', 'width': 150},
            {'key': 'status', 'title': 'Durum', 'width': 100,
             'formatter': lambda v, r: Formatter.status_text(v)},
        ])

        layout.addWidget(self.packaging_table)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        complete_btn = PrimaryButton("Paketleme Tamamla")
        complete_btn.clicked.connect(self._on_complete_packaging)

        buttons.addStretch()
        buttons.addWidget(complete_btn)
        layout.addLayout(buttons)

        return frame

    def _on_pass_inspection(self):
        data = self.inspection_table.get_selected_data()
        if data.get('id'):
            self.pass_inspection.emit(data['id'])

    def _on_fail_inspection(self):
        data = self.inspection_table.get_selected_data()
        if data.get('id'):
            self.fail_inspection.emit(data['id'], "")

    def _on_complete_packaging(self):
        data = self.packaging_table.get_selected_data()
        if data.get('id'):
            self.complete_packaging.emit(data['id'], "WRAP_DOUBLE")

    def update_stats(self, inspect: int, packaging: int, ready: int, failed: int):
        self.stat_inspect.set_value(str(inspect))
        self.stat_packaging.set_value(str(packaging))
        self.stat_ready.set_value(str(ready))
        self.stat_failed.set_value(str(failed))

    def set_inspection_data(self, data: list):
        self.inspection_table.set_data(data)

    def set_packaging_data(self, data: list):
        self.packaging_table.set_data(data)
