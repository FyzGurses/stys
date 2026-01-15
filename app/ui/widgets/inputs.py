from PySide6.QtWidgets import QLineEdit, QHBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Styles, Colors


class BarcodeInput(QLineEdit):

    barcode_scanned = Signal(str)

    def __init__(self, placeholder: str = "Barkod okutun...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(Styles.input_field())
        self.setMinimumHeight(56)
        self.setAlignment(Qt.AlignCenter)

        font = self.font()
        font.setPointSize(18)
        self.setFont(font)

        self.returnPressed.connect(self._on_enter)

    def _on_enter(self):
        barcode = self.text().strip()
        if barcode:
            self.barcode_scanned.emit(barcode)
            self.clear()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.selectAll()


class PinInput(QWidget):

    pin_entered = Signal(str)

    def __init__(self, length: int = 4, parent=None):
        super().__init__(parent)
        self.length = length
        self.digits = []

        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        for i in range(length):
            digit = QLineEdit()
            digit.setMaxLength(1)
            digit.setFixedSize(56, 64)
            digit.setAlignment(Qt.AlignCenter)
            digit.setEchoMode(QLineEdit.Password)
            digit.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {Colors.SURFACE};
                    color: {Colors.TEXT_PRIMARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: 8px;
                    font-size: 24px;
                    font-weight: bold;
                }}
                QLineEdit:focus {{
                    border-color: {Colors.PRIMARY};
                }}
            """)

            digit.textChanged.connect(lambda text, idx=i: self._on_digit_changed(idx, text))
            self.digits.append(digit)
            layout.addWidget(digit)

    def _on_digit_changed(self, index: int, text: str):
        if text and index < self.length - 1:
            self.digits[index + 1].setFocus()

        pin = self.get_pin()
        if len(pin) == self.length:
            self.pin_entered.emit(pin)

    def get_pin(self) -> str:
        return ''.join(d.text() for d in self.digits)

    def clear(self):
        for digit in self.digits:
            digit.clear()
        self.digits[0].setFocus()

    def setFocus(self):
        self.digits[0].setFocus()


class SearchInput(QLineEdit):

    def __init__(self, placeholder: str = "Ara...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(44)
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 22px;
                padding: 8px 20px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """)


class NumericInput(QLineEdit):

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(Styles.input_field())
        self.setAlignment(Qt.AlignRight)

    def keyPressEvent(self, event):
        if event.text().isdigit() or event.key() in [
            Qt.Key_Backspace, Qt.Key_Delete, Qt.Key_Left, Qt.Key_Right
        ]:
            super().keyPressEvent(event)
