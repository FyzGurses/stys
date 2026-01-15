from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.zones.base_zone_screen import BaseZoneScreen
from app.ui.widgets.cards import StatCard, ItemCard
from app.ui.widgets.buttons import PrimaryButton
from app.ui.widgets.tables import DataTable
from app.utils.formatting import Formatter


class DirtyZoneScreen(BaseZoneScreen):

    receive_item = Signal()
    start_washing = Signal(int)
    complete_washing = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Kirli Alan", Colors.DIRTY_ZONE, parent)
        self._setup_ui()

    def _setup_ui(self):
        stats = self._create_stats()
        self.add_section(stats)

        actions = self._create_actions()
        self.add_section(actions)

        pending_section = self._create_pending_section()
        self.add_section(pending_section)

        washing_section = self._create_washing_section()
        self.add_section(washing_section)

    def _create_stats(self):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: transparent;")

        layout = QHBoxLayout(frame)
        layout.setSpacing(16)

        self.stat_pending = StatCard("Bekleyen", "0", "", Colors.WARNING)
        self.stat_washing = StatCard("Yikamada", "0", "", Colors.INFO)
        self.stat_washed = StatCard("Yikandi", "0", "", Colors.SUCCESS)

        layout.addWidget(self.stat_pending)
        layout.addWidget(self.stat_washing)
        layout.addWidget(self.stat_washed)

        return frame

    def _create_actions(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QHBoxLayout(frame)

        receive_btn = PrimaryButton("Yeni Urun Kabul")
        receive_btn.clicked.connect(self.receive_item.emit)

        layout.addWidget(receive_btn)
        layout.addStretch()

        return frame

    def _create_pending_section(self):
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
        title = QLabel("Bekleyen Urunler")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.pending_table = DataTable([
            {'key': 'order_number', 'title': 'Is Emri', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'department_name', 'title': 'Bolum', 'width': 150},
            {'key': 'received_at', 'title': 'Kabul', 'width': 100,
             'formatter': lambda v, r: Formatter.format_datetime(v) if v else ''},
        ])
        self.pending_table.row_double_clicked.connect(
            lambda row, data: self.start_washing.emit(data.get('id', 0))
        )

        layout.addWidget(self.pending_table)

        return frame

    def _create_washing_section(self):
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
        title = QLabel("Yikamada")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self.washing_table = DataTable([
            {'key': 'order_number', 'title': 'Is Emri', 'width': 120},
            {'key': 'item_name', 'title': 'Urun', 'stretch': True},
            {'key': 'machine_name', 'title': 'Makine', 'width': 150},
            {'key': 'status', 'title': 'Durum', 'width': 100,
             'formatter': lambda v, r: Formatter.status_text(v)},
        ])
        self.washing_table.row_double_clicked.connect(
            lambda row, data: self.complete_washing.emit(data.get('id', 0))
        )

        layout.addWidget(self.washing_table)

        return frame

    def update_stats(self, pending: int, washing: int, washed: int):
        self.stat_pending.set_value(str(pending))
        self.stat_washing.set_value(str(washing))
        self.stat_washed.set_value(str(washed))

    def set_pending_data(self, data: list):
        self.pending_table.set_data(data)

    def set_washing_data(self, data: list):
        self.washing_table.set_data(data)
