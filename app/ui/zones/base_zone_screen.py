from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.widgets.buttons import PrimaryButton, SecondaryButton
from app.ui.widgets.inputs import BarcodeInput


class BaseZoneScreen(QWidget):

    back_requested = Signal()
    barcode_scanned = Signal(str)

    def __init__(self, zone_name: str, zone_color: str, parent=None):
        super().__init__(parent)
        self.zone_name = zone_name
        self.zone_color = zone_color
        self._setup_base_ui()

    def _setup_base_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        header = self._create_header()
        layout.addWidget(header)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setSpacing(16)
        self.content_layout.setContentsMargins(24, 24, 24, 24)

        barcode_section = self._create_barcode_section()
        self.content_layout.addWidget(barcode_section)

        self.main_content = QWidget()
        self.main_layout = QVBoxLayout(self.main_content)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.addWidget(self.main_content)

        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        layout.addWidget(scroll)

    def _create_header(self):
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {self.zone_color};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        back_btn = SecondaryButton("< Geri")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: white;
                border: 2px solid rgba(255,255,255,0.5);
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255,255,255,0.1);
            }}
        """)
        back_btn.clicked.connect(self.back_requested.emit)

        title = QLabel(self.zone_name)
        title.setStyleSheet("""
            color: white;
            font-size: 22px;
            font-weight: bold;
        """)

        layout.addWidget(back_btn)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addSpacing(100)

        return header

    def _create_barcode_section(self):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        layout = QHBoxLayout(frame)

        self.barcode_input = BarcodeInput("Barkod okutun...")
        self.barcode_input.barcode_scanned.connect(self.barcode_scanned.emit)

        layout.addWidget(self.barcode_input)

        return frame

    def add_section(self, widget: QWidget):
        self.main_layout.addWidget(widget)

    def showEvent(self, event):
        super().showEvent(event)
        self.barcode_input.setFocus()
