from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Styles, Colors
from app.ui.widgets.inputs import PinInput
from app.ui.widgets.buttons import PrimaryButton, SecondaryButton, DangerButton


class BaseDialog(QDialog):

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
        """)

        self.setMinimumWidth(400)


class ConfirmDialog(BaseDialog):

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(title, parent)
        self._setup_ui(message)

    def _setup_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        cancel_btn = SecondaryButton("Vazgec")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = PrimaryButton("Onayla")
        confirm_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)


class DangerConfirmDialog(BaseDialog):

    def __init__(self, title: str, message: str, confirm_text: str = "Sil",
                parent=None):
        super().__init__(title, parent)
        self._setup_ui(message, confirm_text)

    def _setup_ui(self, message: str, confirm_text: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        warning = QLabel("!")
        warning.setStyleSheet(f"""
            background-color: {Colors.DANGER};
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 16px;
            border-radius: 50%;
        """)
        warning.setFixedSize(60, 60)
        warning.setAlignment(Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(warning, alignment=Qt.AlignCenter)
        layout.addWidget(msg_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(12)

        cancel_btn = SecondaryButton("Vazgec")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = DangerButton(confirm_text)
        confirm_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)


class PinDialog(BaseDialog):

    pin_verified = Signal(str)

    def __init__(self, title: str = "PIN Dogrulama", parent=None):
        super().__init__(title, parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        msg_label = QLabel("Islemi onaylamak icin PIN'inizi girin")
        msg_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
        """)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        self.pin_input = PinInput(4)
        self.pin_input.pin_entered.connect(self._on_pin_entered)
        layout.addWidget(self.pin_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"""
            color: {Colors.DANGER};
            font-size: 14px;
        """)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        cancel_btn = SecondaryButton("Vazgec")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def _on_pin_entered(self, pin: str):
        self.pin_verified.emit(pin)

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()
        self.pin_input.clear()

    def showEvent(self, event):
        super().showEvent(event)
        self.pin_input.setFocus()


class MessageDialog(BaseDialog):

    def __init__(self, title: str, message: str,
                message_type: str = "info", parent=None):
        super().__init__(title, parent)
        self._setup_ui(message, message_type)

    def _setup_ui(self, message: str, message_type: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        icons = {
            'success': ('✓', Colors.SUCCESS),
            'error': ('✗', Colors.DANGER),
            'warning': ('!', Colors.WARNING),
            'info': ('i', Colors.INFO)
        }

        icon_text, icon_color = icons.get(message_type, ('i', Colors.INFO))

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"""
            background-color: {icon_color};
            color: white;
            font-size: 24px;
            font-weight: bold;
            padding: 12px;
            border-radius: 25px;
        """)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: 16px;
        """)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        ok_btn = PrimaryButton("Tamam")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
