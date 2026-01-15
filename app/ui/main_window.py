from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox, QApplication
from PySide6.QtCore import Qt

from app.ui.styles import Styles
from app.ui.screens import LoginScreen, DashboardScreen, ZoneSelectorScreen
from app.ui.zones import DirtyZoneScreen, CleanZoneScreen, SterileZoneScreen
from app.services import AuthService
from app.services.zones import DirtyZoneService, CleanZoneService, SterileZoneService
from app.core.session import current_session


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.auth_service = AuthService()
        self.dirty_service = DirtyZoneService()
        self.clean_service = CleanZoneService()
        self.sterile_service = SterileZoneService()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("Sterilizasyon Takip Sistemi")
        self.setStyleSheet(Styles.main_window())
        self.showFullScreen()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_screen = LoginScreen()
        self.dashboard_screen = DashboardScreen()
        self.zone_selector = ZoneSelectorScreen()
        self.dirty_zone = DirtyZoneScreen()
        self.clean_zone = CleanZoneScreen()
        self.sterile_zone = SterileZoneScreen()

        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.dashboard_screen)
        self.stack.addWidget(self.zone_selector)
        self.stack.addWidget(self.dirty_zone)
        self.stack.addWidget(self.clean_zone)
        self.stack.addWidget(self.sterile_zone)

        self.stack.setCurrentWidget(self.login_screen)

    def _connect_signals(self):
        self.login_screen.login_requested.connect(self._on_login)

        self.dashboard_screen.logout_requested.connect(self._on_logout)
        self.dashboard_screen.zone_selected.connect(self._on_zone_selected)
        self.dashboard_screen.barcode_scanned.connect(self._on_barcode_scanned)
        self.dashboard_screen.exit_requested.connect(self._on_exit)

        self.zone_selector.zone_selected.connect(self._on_zone_selected)
        self.zone_selector.back_requested.connect(self._show_dashboard)

        self.dirty_zone.back_requested.connect(self._show_dashboard)
        self.dirty_zone.receive_item.connect(self._on_receive_item)
        self.dirty_zone.barcode_scanned.connect(self._on_barcode_scanned)

        self.clean_zone.back_requested.connect(self._show_dashboard)
        self.clean_zone.pass_inspection.connect(self._on_pass_inspection)
        self.clean_zone.fail_inspection.connect(self._on_fail_inspection)
        self.clean_zone.complete_packaging.connect(self._on_complete_packaging)
        self.clean_zone.barcode_scanned.connect(self._on_barcode_scanned)

        self.sterile_zone.back_requested.connect(self._show_dashboard)
        self.sterile_zone.release_item.connect(self._on_release_item)
        self.sterile_zone.reject_item.connect(self._on_reject_item)
        self.sterile_zone.barcode_scanned.connect(self._on_barcode_scanned)

    def _on_login(self, badge: str, pin: str):
        success, message, user_data = self.auth_service.authenticate_with_pin(badge, pin)
        if success:
            self._show_dashboard()
        else:
            self.login_screen.show_error(message)

    def _on_logout(self):
        self.auth_service.logout()
        self.stack.setCurrentWidget(self.login_screen)

    def _on_exit(self):
        reply = QMessageBox.question(
            self, "Cikis",
            "Uygulamayi kapatmak istediginize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.auth_service.logout()
            QApplication.quit()

    def _show_dashboard(self):
        self.dashboard_screen.update_user_info()
        self._update_dashboard_stats()
        self.stack.setCurrentWidget(self.dashboard_screen)

    def _update_dashboard_stats(self):
        pending = len(self.dirty_service.get_pending_items())
        washing = len(self.dirty_service.get_washing_items())
        sterile = 0
        ready = 0
        self.dashboard_screen.update_stats(pending, washing, sterile, ready)

    def _on_zone_selected(self, zone: str):
        if zone == "DIRTY":
            self._load_dirty_zone()
            self.stack.setCurrentWidget(self.dirty_zone)
        elif zone == "CLEAN":
            self._load_clean_zone()
            self.stack.setCurrentWidget(self.clean_zone)
        elif zone == "STERILE":
            self._load_sterile_zone()
            self.stack.setCurrentWidget(self.sterile_zone)

    def _load_dirty_zone(self):
        pending = self.dirty_service.get_pending_items()
        washing = self.dirty_service.get_washing_items()
        washed = self.dirty_service.get_washed_items()

        self.dirty_zone.update_stats(len(pending), len(washing), len(washed))
        self.dirty_zone.set_pending_data(pending)
        self.dirty_zone.set_washing_data(washing)

    def _load_clean_zone(self):
        inspection = self.clean_service.get_pending_inspection()
        packaging = self.clean_service.get_pending_packaging()
        packaged = self.clean_service.get_packaged_items()
        failed = self.clean_service.get_failed_items()

        self.clean_zone.update_stats(len(inspection), len(packaging),
                                      len(packaged), len(failed))
        self.clean_zone.set_inspection_data(inspection)
        self.clean_zone.set_packaging_data(packaging)

    def _load_sterile_zone(self):
        sterilizing = self.sterile_service.get_sterilizing_items()
        pending = self.sterile_service.get_pending_release_items()
        released = self.sterile_service.get_released_items()

        self.sterile_zone.update_stats(len(sterilizing), 0, 0,
                                        len(pending), len(released))
        self.sterile_zone.set_sterilizing_data(sterilizing)
        self.sterile_zone.set_pending_data(pending)
        self.sterile_zone.set_released_data(released)

    def _on_barcode_scanned(self, barcode: str):
        pass

    def _on_receive_item(self):
        pass

    def _on_pass_inspection(self, order_id: int):
        success, msg = self.clean_service.pass_inspection(order_id)
        if success:
            self._load_clean_zone()
        else:
            self._show_error(msg)

    def _on_fail_inspection(self, order_id: int, reason: str):
        success, msg = self.clean_service.fail_inspection(order_id, reason or "Kontrol basarisiz")
        if success:
            self._load_clean_zone()
        else:
            self._show_error(msg)

    def _on_complete_packaging(self, order_id: int, packaging_type: str):
        success, msg = self.clean_service.complete_packaging(order_id, packaging_type)
        if success:
            self._load_clean_zone()
        else:
            self._show_error(msg)

    def _on_release_item(self, record_id: int):
        success, msg = self.sterile_service.release_item(record_id)
        if success:
            self._load_sterile_zone()
        else:
            self._show_error(msg)

    def _on_reject_item(self, record_id: int, reason: str):
        success, msg = self.sterile_service.reject_item(record_id, reason or "Reddedildi")
        if success:
            self._load_sterile_zone()
        else:
            self._show_error(msg)

    def _show_error(self, message: str):
        QMessageBox.warning(self, "Hata", message)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.stack.currentWidget() != self.login_screen:
                self._show_dashboard()
        super().keyPressEvent(event)
