from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import Styles, Colors


class DataTable(QTableWidget):

    row_clicked = Signal(int, dict)
    row_double_clicked = Signal(int, dict)

    def __init__(self, columns: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.columns = columns
        self.data = []
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(Styles.table())
        self.setColumnCount(len(self.columns))

        headers = [col.get('title', '') for col in self.columns]
        self.setHorizontalHeaderLabels(headers)

        header = self.horizontalHeader()
        for i, col in enumerate(self.columns):
            width = col.get('width')
            if width:
                self.setColumnWidth(i, width)
            elif col.get('stretch'):
                header.setSectionResizeMode(i, QHeaderView.Stretch)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)

        self.cellClicked.connect(self._on_cell_clicked)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def set_data(self, data: List[Dict[str, Any]]):
        self.data = data
        self.setRowCount(len(data))

        for row_idx, row_data in enumerate(data):
            for col_idx, col in enumerate(self.columns):
                key = col.get('key', '')
                value = row_data.get(key, '')

                formatter = col.get('formatter')
                if formatter:
                    value = formatter(value, row_data)

                item = QTableWidgetItem(str(value))
                item.setTextAlignment(
                    col.get('align', Qt.AlignLeft | Qt.AlignVCenter)
                )

                self.setItem(row_idx, col_idx, item)

        self.resizeRowsToContents()

    def get_selected_data(self) -> Dict[str, Any]:
        row = self.currentRow()
        if 0 <= row < len(self.data):
            return self.data[row]
        return {}

    def _on_cell_clicked(self, row: int, col: int):
        if 0 <= row < len(self.data):
            self.row_clicked.emit(row, self.data[row])

    def _on_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.data):
            self.row_double_clicked.emit(row, self.data[row])

    def clear_data(self):
        self.data = []
        self.setRowCount(0)

    def add_row(self, row_data: Dict[str, Any]):
        self.data.append(row_data)
        self.set_data(self.data)

    def update_row(self, row: int, row_data: Dict[str, Any]):
        if 0 <= row < len(self.data):
            self.data[row] = row_data
            self.set_data(self.data)

    def remove_row(self, row: int):
        if 0 <= row < len(self.data):
            self.data.pop(row)
            self.set_data(self.data)


class SimpleTable(QTableWidget):

    def __init__(self, headers: List[str], parent=None):
        super().__init__(parent)
        self._setup_ui(headers)

    def _setup_ui(self, headers: List[str]):
        self.setStyleSheet(Styles.table())
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)

        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)

    def add_row(self, values: List[str]):
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            self.setItem(row, col, item)
