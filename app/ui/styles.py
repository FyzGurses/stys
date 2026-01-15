class Colors:
    PRIMARY = "#2196F3"
    PRIMARY_DARK = "#1976D2"
    PRIMARY_LIGHT = "#BBDEFB"

    SECONDARY = "#FF9800"
    SECONDARY_DARK = "#F57C00"

    SUCCESS = "#4CAF50"
    SUCCESS_DARK = "#388E3C"

    WARNING = "#FFC107"
    WARNING_DARK = "#FFA000"

    DANGER = "#F44336"
    DANGER_DARK = "#D32F2F"

    INFO = "#00BCD4"
    INFO_DARK = "#0097A7"

    DIRTY_ZONE = "#e74c3c"
    CLEAN_ZONE = "#f39c12"
    STERILE_ZONE = "#27ae60"

    BACKGROUND = "#1a1a2e"
    BACKGROUND_LIGHT = "#16213e"
    SURFACE = "#0f3460"
    SURFACE_LIGHT = "#1f4287"

    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#b0b0b0"
    TEXT_DISABLED = "#666666"

    BORDER = "#333333"
    BORDER_LIGHT = "#444444"


class Styles:

    @staticmethod
    def main_window() -> str:
        return f"""
            QMainWindow {{
                background-color: {Colors.BACKGROUND};
            }}
        """

    @staticmethod
    def container() -> str:
        return f"""
            QWidget {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
            }}
        """

    @staticmethod
    def card() -> str:
        return f"""
            QFrame {{
                background-color: {Colors.SURFACE};
                border-radius: 8px;
                padding: 16px;
            }}
        """

    @staticmethod
    def button_primary() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            QPushButton:disabled {{
                background-color: {Colors.TEXT_DISABLED};
                color: {Colors.TEXT_SECONDARY};
            }}
        """

    @staticmethod
    def button_success() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.SUCCESS_DARK};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        return f"""
            QPushButton {{
                background-color: {Colors.DANGER};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER_DARK};
            }}
        """

    @staticmethod
    def button_secondary() -> str:
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SURFACE};
                border-color: {Colors.PRIMARY};
            }}
        """

    @staticmethod
    def input_field() -> str:
        return f"""
            QLineEdit {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 12px 16px;
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QLineEdit:disabled {{
                background-color: {Colors.BACKGROUND_LIGHT};
                color: {Colors.TEXT_DISABLED};
            }}
        """

    @staticmethod
    def label() -> str:
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 14px;
            }}
        """

    @staticmethod
    def label_title() -> str:
        return f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: 24px;
                font-weight: bold;
            }}
        """

    @staticmethod
    def label_subtitle() -> str:
        return f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 16px;
            }}
        """

    @staticmethod
    def table() -> str:
        return f"""
            QTableWidget {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: 8px;
                gridline-color: {Colors.BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.BACKGROUND_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                padding: 12px;
                border: none;
                font-weight: bold;
            }}
        """

    @staticmethod
    def scrollbar() -> str:
        return f"""
            QScrollBar:vertical {{
                background-color: {Colors.BACKGROUND};
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {Colors.BORDER_LIGHT};
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

    @staticmethod
    def combo_box() -> str:
        return f"""
            QComboBox {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 12px 16px;
                font-size: 14px;
            }}
            QComboBox:focus {{
                border-color: {Colors.PRIMARY};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.PRIMARY};
            }}
        """

    @staticmethod
    def zone_badge(zone: str) -> str:
        colors = {
            'DIRTY': Colors.DIRTY_ZONE,
            'CLEAN': Colors.CLEAN_ZONE,
            'STERILE': Colors.STERILE_ZONE
        }
        bg_color = colors.get(zone, Colors.SURFACE)
        return f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }}
        """

    @staticmethod
    def status_badge(status: str) -> str:
        if status in ['RELEASED', 'COMPLETED', 'PASS']:
            bg = Colors.SUCCESS
        elif status in ['REJECTED', 'FAIL', 'ERROR']:
            bg = Colors.DANGER
        elif status in ['PENDING', 'PENDING_RELEASE', 'PENDING_CI', 'PENDING_BI']:
            bg = Colors.WARNING
        else:
            bg = Colors.INFO

        return f"""
            QLabel {{
                background-color: {bg};
                color: white;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }}
        """
