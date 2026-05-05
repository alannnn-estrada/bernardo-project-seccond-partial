import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox,
    QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QStyle
from PySide6.QtGui import QFont

try:
    import qtawesome as qta
except ImportError:
    qta = None

from insert import (
    ensure_data_files,
    generate_id,
    get_default_terminal,
    get_display_value,
    hash_password,
    load_rows,
    save_rows,
    seed_reservaciones_if_needed,
    seed_terminales_if_needed,
    seed_viajes,
    verify_password,
)
from ui_components import TablePanel


TABLE_NAMES = ["roles", "clientes", "terminales", "lugares", "viajes", "usuarios", "reservaciones"]

TABLE_LABELS = {
    "roles": "Roles",
    "clientes": "Clientes",
    "terminales": "Terminales",
    "lugares": "Lugares",
    "viajes": "Viajes",
    "usuarios": "Usuarios",
    "reservaciones": "Reservaciones",
}


class LoginDialog(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent_app = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(24, 24, 24, 24)

        # Fondo
        central = QFrame()
        central.setObjectName("loginRoot")
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card de login
        card = QFrame()
        card.setObjectName("surfaceCard")
        card.setFixedSize(QSize(440, 360))
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(32, 28, 32, 28)

        # Titulo
        title = QLabel("Iniciar Sesión")
        title.setObjectName("heroTitle")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        card_layout.addWidget(title)

        # Username
        username_label = QLabel("Usuario:")
        username_label.setObjectName("subtitleText")
        username_label.setFont(QFont("Segoe UI", 11))
        card_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingrese el usuario")
        self.username_input.setObjectName("authInput")
        card_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Contraseña:")
        password_label.setObjectName("subtitleText")
        password_label.setFont(QFont("Segoe UI", 11))
        card_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingrese la contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("authInput")
        self.password_input.returnPressed.connect(self.on_login)
        card_layout.addWidget(self.password_input)

        # Botón login
        login_btn = QPushButton("Entrar")
        login_btn.setObjectName("primaryAction")
        login_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        login_btn.setIcon(self.get_icon("fa5s.sign-in-alt", QStyle.StandardPixmap.SP_DialogOkButton))
        login_btn.clicked.connect(self.on_login)
        card_layout.addWidget(login_btn)

        # Hint
        hint = QLabel("Usuario: admin | Contraseña: admin123")
        hint.setObjectName("helperText")
        hint.setFont(QFont("Segoe UI", 9))
        card_layout.addWidget(hint)

        central_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(central)
        layout.addStretch(1)

        self.setWindowTitle("Agencia de Viajes")

    def get_icon(self, icon_name, fallback):
        return self.parent_app.get_icon(icon_name, fallback)

    def on_login(self):
        username = self.username_input.text().strip().lower()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Campos vacíos", "Ingrese usuario y contraseña.")
            return

        users = load_rows("usuarios")
        user = next((row for row in users if row.get("username", "").strip().lower() == username), None)

        if not user or not verify_password(password, user.get("password_hash", "")):
            QMessageBox.critical(self, "Acceso denegado", "Usuario o contraseña incorrectos.")
            self.password_input.clear()
            self.username_input.setFocus()
            return

        if not user.get("id_terminal"):
            default_terminal = get_default_terminal()
            user["id_terminal"] = default_terminal.get("id_terminal", "")
            for index, row in enumerate(users):
                if row.get("id_usuario", "") == user.get("id_usuario", ""):
                    users[index] = user
                    break
            save_rows("usuarios", users)

        self.parent_app.login_user(user)


class AgencyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agencia de Viajes - Sistema de Reservas")
        self.setGeometry(100, 100, 1400, 800)
        self.setMinimumSize(1200, 700)

        # Cargar estilos
        self.load_styles()

        # Inicializar datos
        ensure_data_files()
        seed_terminales_if_needed()
        self.ensure_default_admin_user()

        self.current_user = None
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
        """Carga los estilos personalizados QSS"""
        try:
            with open("styles.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0f172a;
                }
                QTabWidget::pane {
                    border: 1px solid #243044;
                    background-color: #111827;
                }
                QTabBar::tab {
                    background-color: #1e293b;
                    color: #cbd5e1;
                    padding: 10px 16px;
                    margin-right: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #111827;
                    color: #f8fafc;
                }
            """)

    def ensure_default_admin_user(self):
        users = load_rows("usuarios")
        if any(user.get("username", "").strip().lower() == "admin" for user in users):
            return

        default_terminal = get_default_terminal()
        admin_row = {
            "id_usuario": generate_id("id_usuario"),
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "id_rol": "rol_admin",
            "id_terminal": default_terminal.get("id_terminal", ""),
            "fecha_contratacion": datetime.now().strftime("%Y-%m-%d"),
            "nombre": "Admin",
            "apellido": "Sistema",
            "direccion": "",
            "correo": "",
            "numero": "",
            "curp": "",
            "rfc": "",
            "sueldo": "",
        }
        users.append(admin_row)
        save_rows("usuarios", users)

    def show_login(self):
        if self.main_widget:
            self.main_widget.deleteLater()
            self.main_widget = None

        self.login_widget = LoginDialog(self)
        self.setCentralWidget(self.login_widget)
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.resize(1000, 700)

    def login_user(self, user):
        self.current_user = user
        if self.login_widget:
            self.login_widget.deleteLater()
            self.login_widget = None
        self.show_main()

    def show_main(self):
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("topBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Información de sesión
        terminal_name = get_display_value("terminales", self.current_user.get("id_terminal", ""))
        session_text = f"Sesión: {self.current_user.get('username', '')} | Terminal: {terminal_name}"
        session_label = QLabel(session_text)
        session_label.setObjectName("pageTitle")
        session_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        header_layout.addWidget(session_label)

        header_layout.addStretch()

        # Botones
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

        brand = QLabel("Agencia de Viajes")
        brand.setObjectName("panelTitle")
        sidebar_layout.addWidget(brand)

        subtitle = QLabel("Panel de Control")
        subtitle.setObjectName("subtitleText")
        sidebar_layout.addWidget(subtitle)

        self.nav_buttons = []

        # Tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        self.tab_widget.tabBar().hide()

        accessible_tables = self.get_accessible_tables()
        icon_map = {
            "roles": "fa5s.user-shield",
            "clientes": "fa5s.users",
            "terminales": "fa5s-building",
            "lugares": "fa5s.map-marker-alt",
            "viajes": "fa5s.route",
            "usuarios": "fa5s.user-cog",
            "reservaciones": "fa5s.ticket-alt",
        }

        for table_name in accessible_tables:
            panel = TablePanel(self.tab_widget, self, table_name)
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

    def is_admin_user(self):
        return self.current_user.get("username", "").strip().lower() == "admin"

    def get_accessible_tables(self):
        if self.is_admin_user():
            return TABLE_NAMES

        from insert import get_row
        id_rol = self.current_user.get("id_rol", "").strip()
        if not id_rol:
            return []

        rol = get_row("roles", id_rol)
        if not rol:
            return []

        permisos = rol.get("permisos", "").strip()
        if not permisos:
            return []

        allowed = {name.strip() for name in permisos.split(",") if name.strip()}
        return [table_name for table_name in TABLE_NAMES if table_name in allowed]



    def load_demo_data(self):
        seed_terminales_if_needed()
        seed_viajes()
        seed_reservaciones_if_needed()
        for panel in self.panels.values():
            panel.refresh_table()
        QMessageBox.information(self, "Datos Demo", "Se cargaron los datos demo disponibles.")

    def logout(self):
        self.current_user = None
        self.panels.clear()
        self.show_login()


def main():
    app = QApplication(sys.argv)
    
    import os
    style_path = os.path.join(os.path.dirname(__file__), "styles.qss")
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"No se pudo cargar el archivo QSS: {e}")

    window = AgencyGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
