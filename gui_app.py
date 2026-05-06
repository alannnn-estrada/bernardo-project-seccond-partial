import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QStyle, QTabWidget, QVBoxLayout, QWidget, QMainWindow

try:
    import qtawesome as qta
except ImportError:
    qta = None

from insert import (
    ensure_data_files,
    get_default_employee,
    get_display_value,
    get_row,
    hash_password,
    load_rows,
    save_rows,
    seed_accesos_if_needed,
    seed_autobuses_if_needed,
    seed_boletos_if_needed,
    seed_clientes_if_needed,
    seed_empleados_if_needed,
    seed_reportes_if_needed,
    seed_rutas_if_needed,
    seed_viajes_if_needed,
    verify_password,
)
from ui_components import TablePanel

TABLE_NAMES = ["clientes", "autobuses", "rutas", "viajes", "boletos", "empleados", "accesos", "reportes"]
TABLE_LABELS = {
    "clientes": "Clientes",
    "autobuses": "Autobuses",
    "rutas": "Rutas",
    "viajes": "Viajes",
    "boletos": "Boletos",
    "empleados": "Empleados",
    "accesos": "Accesos",
    "reportes": "Reportes",
}


class LoginDialog(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("loginPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        root = QFrame()
        root.setObjectName("loginRoot")
        root.setSizePolicy(self.sizePolicy())
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("surfaceCard")
        card.setFixedSize(QSize(460, 380))
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(32, 28, 32, 28)

        title = QLabel("Iniciar Sesión")
        title.setObjectName("heroTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        card_layout.addWidget(title)

        subtitle = QLabel("Sistema de autobuses")
        subtitle.setObjectName("helperText")
        subtitle.setFont(QFont("Segoe UI", 10))
        card_layout.addWidget(subtitle)

        username_label = QLabel("Usuario")
        username_label.setObjectName("subtitleText")
        card_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese el usuario")
        self.username_input.setObjectName("authInput")
        card_layout.addWidget(self.username_input)

        password_label = QLabel("Contraseña")
        password_label.setObjectName("subtitleText")
        card_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese la contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("authInput")
        self.password_input.returnPressed.connect(self.on_login)
        card_layout.addWidget(self.password_input)

        login_btn = QPushButton("Entrar")
        login_btn.setObjectName("primaryAction")
        login_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        login_btn.setIcon(self.get_icon("fa5s.sign-in-alt", QStyle.StandardPixmap.SP_DialogOkButton))
        login_btn.clicked.connect(self.on_login)
        card_layout.addWidget(login_btn)

        hint = QLabel("Admin: admin / admin123 | Usuario: usuario / usuario123")
        hint.setObjectName("helperText")
        hint.setWordWrap(True)
        hint.setFont(QFont("Segoe UI", 9))
        card_layout.addWidget(hint)

        root_layout.addWidget(card)
        layout.addWidget(root)
        self.setWindowTitle("Sistema de Autobuses")

    def get_icon(self, icon_name, fallback):
        return self.parent_app.get_icon(icon_name, fallback)

    def on_login(self):
        username = self.username_input.text().strip().lower()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Campos vacíos", "Ingrese usuario y contraseña.")
            return

        employees = load_rows("empleados")
        employee = next((row for row in employees if row.get("usuario", "").strip().lower() == username), None)
        if not employee or not verify_password(password, employee.get("contrasena_encriptada", "")):
            QMessageBox.critical(self, "Acceso denegado", "Usuario o contraseña incorrectos.")
            self.password_input.clear()
            self.username_input.setFocus()
            return

        access = next((row for row in load_rows("accesos") if row.get("id_empleado", "") == employee.get("id_empleado", "")), None)
        if not access:
            QMessageBox.critical(self, "Acceso denegado", "El empleado no tiene permisos asignados.")
            return

        self.parent_app.login_user(employee, access)


class AgencyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Autobuses")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1200, 700)
        self.load_styles()
        ensure_data_files()
        self.current_employee = None
        self.current_access = None
        self.interface_mode = "user"
        self.main_widget = None
        self.login_widget = None
        self.panels = {}
        self.nav_buttons = []
        self.show_login()

    def get_icon(self, icon_name, fallback):
        if qta is not None:
            try:
                return qta.icon(icon_name, color="#e2e8f0")
            except Exception:
                pass
        return self.style().standardIcon(fallback)

    def load_styles(self):
        try:
            with open("styles.qss", "r", encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except FileNotFoundError:
            self.setStyleSheet("QMainWindow, QWidget { background: #0b0f19; color: #f1f5f9; }")

    def show_login(self):
        if self.main_widget:
            self.main_widget.deleteLater()
            self.main_widget = None
        self.login_widget = LoginDialog(self)
        self.setCentralWidget(self.login_widget)
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.resize(1000, 720)

    def login_user(self, employee, access):
        self.current_employee = employee
        self.current_access = access
        self.interface_mode = "admin" if access.get("interfaz_accedida", "").strip().lower() == "admin" else "user"
        if self.login_widget:
            self.login_widget.deleteLater()
            self.login_widget = None
        self.show_main()

    def show_main(self):
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("topBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        employee_name = self.current_employee.get("nombre", "") if self.current_employee else ""
        mode_label = QLabel(f"Sesión: {employee_name} | Vista: {self.interface_mode.capitalize()}")
        mode_label.setObjectName("pageTitle")
        mode_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(mode_label)
        header_layout.addStretch()

        if self.interface_mode == "admin":
            demo_btn = QPushButton("Cargar Demos")
            demo_btn.setObjectName("successAction")
            demo_btn.setIcon(self.get_icon("fa5s.database", QStyle.StandardPixmap.SP_DialogOpenButton))
            demo_btn.clicked.connect(self.load_demo_data)
            header_layout.addWidget(demo_btn)

        fullscreen_btn = QPushButton("Pantalla completa")
        fullscreen_btn.setObjectName("primaryAction")
        fullscreen_btn.setIcon(self.get_icon("fa5s.expand", QStyle.StandardPixmap.SP_TitleBarMaxButton))
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        header_layout.addWidget(fullscreen_btn)

        logout_btn = QPushButton("Cerrar Sesión")
        logout_btn.setObjectName("dangerAction")
        logout_btn.setIcon(self.get_icon("fa5s.sign-out-alt", QStyle.StandardPixmap.SP_DialogCloseButton))
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)
        main_layout.addWidget(header)

        body = QFrame()
        body.setObjectName("pageSurface")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        brand = QLabel("Sistema de Autobuses")
        brand.setObjectName("panelTitle")
        sidebar_layout.addWidget(brand)

        subtitle = QLabel("Vista básica" if self.interface_mode == "user" else "Vista administrativa")
        subtitle.setObjectName("subtitleText")
        sidebar_layout.addWidget(subtitle)

        self.nav_buttons = []
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        self.tab_widget.tabBar().hide()

        accessible_tables = self.get_accessible_tables()
        icon_map = {
            "clientes": "fa5s.users",
            "autobuses": "fa5s.bus",
            "rutas": "fa5s.route",
            "viajes": "fa5s.bus-alt",
            "boletos": "fa5s.ticket-alt",
            "empleados": "fa5s.user-cog",
            "accesos": "fa5s.lock",
            "reportes": "fa5s.chart-bar",
        }

        for table_name in accessible_tables:
            panel = TablePanel(self.tab_widget, self, table_name, permissions=self.get_table_permissions(table_name))
            tab_index = self.tab_widget.addTab(panel, TABLE_LABELS.get(table_name, table_name.capitalize()))
            self.panels[table_name] = panel

            nav_btn = QPushButton(TABLE_LABELS.get(table_name, table_name.capitalize()))
            nav_btn.setObjectName("sidebarNav")
            nav_btn.setCheckable(True)
            nav_btn.setIcon(self.get_icon(icon_map.get(table_name, "fa5s.circle"), QStyle.StandardPixmap.SP_FileIcon))
            nav_btn.clicked.connect(lambda _checked=False, idx=tab_index: self.tab_widget.setCurrentIndex(idx))
            sidebar_layout.addWidget(nav_btn)
            self.nav_buttons.append(nav_btn)

        sidebar_layout.addStretch(1)
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        self.tab_widget.currentChanged.connect(self.sync_sidebar_state)

        body_layout.addWidget(sidebar)
        body_layout.addWidget(self.tab_widget, 1)
        main_layout.addWidget(body, 1)
        self.setCentralWidget(self.main_widget)
        self.showMaximized()

    def sync_sidebar_state(self, active_index):
        for index, button in enumerate(self.nav_buttons):
            button.setChecked(index == active_index)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def get_accessible_tables(self):
        if self.interface_mode == "admin":
            return TABLE_NAMES
        return ["clientes", "rutas", "viajes", "boletos", "reportes"]

    def get_table_permissions(self, table_name):
        if self.interface_mode == "admin":
            return {"create": True, "edit": True, "delete": True}

        base = {"create": False, "edit": False, "delete": False}
        if table_name == "clientes":
            base["create"] = True
        if table_name == "boletos":
            base["create"] = str(self.current_access.get("permiso_altas", "")).lower() == "true"
        return base

    def load_demo_data(self):
        seed_empleados_if_needed()
        seed_accesos_if_needed()
        seed_clientes_if_needed()
        seed_autobuses_if_needed()
        seed_rutas_if_needed()
        seed_viajes_if_needed()
        seed_boletos_if_needed()
        seed_reportes_if_needed()
        for panel in self.panels.values():
            panel.refresh_table()
        QMessageBox.information(self, "Datos Demo", "Se cargaron los datos demo disponibles.")

    def logout(self):
        self.current_employee = None
        self.current_access = None
        self.interface_mode = "user"
        self.panels.clear()
        self.show_login()


def main():
    app = QApplication(sys.argv)
    window = AgencyGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
