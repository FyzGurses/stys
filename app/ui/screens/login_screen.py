from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Colors
from app.ui.widgets.inputs import BarcodeInput, PinInput
from app.ui.widgets.buttons import PrimaryButton, SecondaryButton


class LoginScreen(QWidget):

    login_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.badge_number = ""
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 16px;
                padding: 32px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(24)

        title = QLabel("Sterilizasyon Takip Sistemi")
        title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 24px;
            font-weight: bold;
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Giris yapmak icin kartinizi okutun")
        subtitle.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: 14px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        self.barcode_input = BarcodeInput("Kart numarasi...")
        self.barcode_input.barcode_scanned.connect(self._on_badge_scanned)

        self.pin_container = QWidget()
        self.pin_container.hide()
        pin_layout = QVBoxLayout(self.pin_container)
        pin_layout.setSpacing(16)

        pin_label = QLabel("PIN'inizi girin")
        pin_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 14px;")
        pin_label.setAlignment(Qt.AlignCenter)

        self.pin_input = PinInput(4)
        self.pin_input.pin_entered.connect(self._on_pin_entered)

        self.user_label = QLabel("")
        self.user_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 12px;")
        self.user_label.setAlignment(Qt.AlignCenter)

        login_btn = PrimaryButton("Giris")
        login_btn.setMinimumHeight(48)
        login_btn.clicked.connect(self._on_login_clicked)

        back_btn = SecondaryButton("Geri")
        back_btn.clicked.connect(self._reset)

        pin_layout.addWidget(pin_label)
        pin_layout.addWidget(self.pin_input)
        pin_layout.addWidget(self.user_label)
        pin_layout.addWidget(login_btn)
        pin_layout.addWidget(back_btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-size: 14px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.barcode_input)
        card_layout.addWidget(self.pin_container)
        card_layout.addWidget(self.error_label)

        layout.addWidget(card)

    def _on_badge_scanned(self, badge: str):
        self.badge_number = badge
        self.barcode_input.hide()
        self.pin_container.show()
        self.user_label.setText(f"Kart: {badge}")
        self.pin_input.setFocus()

    def _on_pin_entered(self, pin: str):
        self.login_requested.emit(self.badge_number, pin)

    def _on_login_clicked(self):
        pin = self.pin_input.get_pin()
        if pin and self.badge_number:
            self.login_requested.emit(self.badge_number, pin)

    def _reset(self):
        self.badge_number = ""
        self.pin_container.hide()
        self.barcode_input.show()
        self.barcode_input.clear()
        self.barcode_input.setFocus()
        self.pin_input.clear()
        self.error_label.hide()

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
        self.pin_input.clear()

    def showEvent(self, event):
        super().showEvent(event)
        self._reset()
