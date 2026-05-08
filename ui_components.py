from datetime import datetime

from PySide6.QtCore import QDate, Qt, QRegularExpression
from PySide6.QtGui import QBrush, QColor, QDoubleValidator, QFont, QIntValidator, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QStyle,
)

try:
    import qtawesome as qta
except ImportError:
    qta = None

from insert import (
    TABLES,
    generate_id,
    get_display_value,
    get_row,
    get_trip_available_seats,
    get_trip_total_seats,
    hash_password,
    load_rows,
    release_trip_seats,
    reserve_trip_seats,
    save_rows,
    validate_date,
    validate_foreign_keys,
)
from ui_config import (
    FORM_FIELDS,
    INTERFACE_OPTIONS,
    REFERENCE_TABLES,
    TREE_HEADERS,
    generate_unique_username,
    is_valid_number,
    table_display_values,
    table_record_label,
)

INTEGER_FIELDS = {"telefono", "capacidad_total", "numero_asiento", "distancia_estimada"}
DECIMAL_FIELDS = {"costo_base", "costo_final"}


class TicketDialog(QDialog):
    def __init__(self, parent, boleto):
        super().__init__(parent)
        self.boleto = boleto
        self.setWindowTitle("Boleto de viaje")
        self.setMinimumSize(380, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel("BOLETO DE VIAJE")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        viaje = get_row("viajes", self.boleto.get("id_viaje", ""))
        cliente = viaje.get("nombre_cliente", "") if viaje else ""
        ruta = get_display_value("rutas", viaje.get("id_ruta", "")) if viaje else ""
        autobus = get_display_value("autobuses", viaje.get("id_autobus", "")) if viaje else ""
        salida = f"{viaje.get('fecha_salida', '')} {viaje.get('hora_salida', '')}".strip() if viaje else ""
        asiento = self.boleto.get("numero_asiento", "")
        costo = self.boleto.get("costo_final", "0")

        details = [
            f"ID Boleto: {self.boleto.get('id_boleto', '')}",
            f"Cliente: {cliente}",
            f"Ruta: {ruta}",
            f"Autobus: {autobus}",
            f"Salida: {salida}",
            f"Asiento: {asiento}",
            f"Costo final: ${costo}",
        ]

        for text in details:
            label = QLabel(text)
            label.setFont(QFont("Segoe UI", 10))
            card_layout.addWidget(label)

        layout.addWidget(card)

        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryAction")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class ReportSummaryDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Reporte básico")
        self.setMinimumSize(560, 460)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        title = QLabel("REPORTE BASICO")
        title.setObjectName("dialogTitle")
        card_layout.addWidget(title)

        reportes = load_rows("reportes")
        viajes = load_rows("viajes")
        boletos = load_rows("boletos")

        resumen = [
            f"Reportes registrados: {len(reportes)}",
            f"Viajes registrados: {len(viajes)}",
            f"Boletos emitidos: {len(boletos)}",
        ]
        for line in resumen:
            label = QLabel(line)
            label.setFont(QFont("Segoe UI", 11))
            card_layout.addWidget(label)

        if reportes:
            last_report = reportes[-1]
            incident = QLabel(f"Ultimo reporte: {get_display_value('viajes', last_report.get('id_viaje', ''))}")
            incident.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            card_layout.addWidget(incident)
            description = QLabel(last_report.get("descripcion_incidencia", ""))
            description.setWordWrap(True)
            card_layout.addWidget(description)

        if viajes:
            route_counts = {}
            for viaje in viajes:
                route_label = get_display_value("rutas", viaje.get("id_ruta", ""))
                route_counts[route_label] = route_counts.get(route_label, 0) + 1
            top_route = max(route_counts.items(), key=lambda item: item[1])
            top_label = QLabel(f"Ruta con mas viajes: {top_route[0]} ({top_route[1]})")
            top_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            card_layout.addWidget(top_label)

        layout.addWidget(card)

        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryAction")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class DeletedRecordsDialog(QDialog):
    def __init__(self, parent, table_name):
        super().__init__(parent)
        self.table_name = table_name
        self.setWindowTitle(f"Registros borrados - {table_name}")
        self.setMinimumSize(860, 460)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel(f"REGISTROS BORRADOS: {self.table_name.upper()}")
        title.setObjectName("dialogTitle")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Se muestran los registros eliminados con su fecha y usuario asociado.")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        table = QTableWidget()
        table.setObjectName("dialogTable")
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "Registro", "Eliminado por", "Fecha eliminación"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        layout.addWidget(table)

        deleted_rows = [row for row in load_rows(self.table_name, include_deleted=True) if str(row.get("is_deleted", "")).lower() == "true"]
        table.setRowCount(len(deleted_rows))

        for row_idx, row in enumerate(deleted_rows):
            id_field = TABLES[self.table_name]["id_field"]
            table.setItem(row_idx, 0, QTableWidgetItem(row.get(id_field, "")))
            table.setItem(row_idx, 1, QTableWidgetItem(table_record_label(self.table_name, row)))
            table.setItem(row_idx, 2, QTableWidgetItem(get_display_value("empleados", row.get("deleted_by", "")) if row.get("deleted_by", "") else ""))
            table.setItem(row_idx, 3, QTableWidgetItem(row.get("deleted_at", "")))

        if not deleted_rows:
            table.setRowCount(1)
            empty_item = QTableWidgetItem("No hay registros borrados")
            empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(0, 0, empty_item)
            table.setSpan(0, 0, 1, 4)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryAction")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)


class SearchSelectDialog(QDialog):
    def __init__(self, parent, table_name, title=None, initial_filter=""):
        super().__init__(parent)
        self.result = None
        self.table_name = table_name
        self.filtered_rows = []
        self.setObjectName("dialogWindow")
        self.setWindowTitle(title or f"Seleccionar {table_name}")
        self.setMinimumSize(520, 380)
        self.setup_ui(initial_filter)

    def setup_ui(self, initial_filter):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel(f"Buscar {self.table_name}")
        title.setObjectName("dialogTitle")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escriba para filtrar...")
        self.search_input.setText(initial_filter)
        self.search_input.setObjectName("dialogSearch")
        self.search_input.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setObjectName("dialogTable")
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(["Resultados"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.doubleClicked.connect(self.accept)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryAction")
        cancel_btn.setIcon(self._icon("fa5s.times", QStyle.StandardPixmap.SP_DialogCancelButton))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        select_btn = QPushButton("Seleccionar")
        select_btn.setObjectName("primaryAction")
        select_btn.setIcon(self._icon("fa5s.check", QStyle.StandardPixmap.SP_DialogOkButton))
        select_btn.clicked.connect(self.accept)
        button_layout.addWidget(select_btn)

        layout.addLayout(button_layout)
        self.refresh_list()
        self.search_input.setFocus()

    def refresh_list(self):
        query = self.search_input.text().strip().lower()
        rows = load_rows(self.table_name)
        self.filtered_rows = []
        self.table.setRowCount(0)

        for row in rows:
            label = table_record_label(self.table_name, row)
            if query and query not in label.lower():
                continue
            self.filtered_rows.append(row)
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            self.table.setItem(row_pos, 0, QTableWidgetItem(label))

        if self.filtered_rows:
            self.table.selectRow(0)
        else:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem("No hay registros disponibles")
            empty_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(0, 0, empty_item)

    def _icon(self, icon_name, fallback):
        if qta is not None:
            try:
                return qta.icon(icon_name, color="#e2e8f0")
            except Exception:
                pass
        return self.style().standardIcon(fallback)

    def accept(self):
        if not self.filtered_rows:
            QMessageBox.information(self, "Selección", "No hay registros disponibles.")
            return
        if not self.table.selectedIndexes():
            QMessageBox.information(self, "Selección", "Seleccione un elemento de la lista.")
            return
        selection = self.table.selectedIndexes()[0].row()
        if 0 <= selection < len(self.filtered_rows):
            self.result = self.filtered_rows[selection]
        super().accept()


class RecordDialog(QDialog):
    def __init__(self, parent, gui_app, table_name, record=None):
        super().__init__(parent)
        self.gui_app = gui_app
        self.table_name = table_name
        self.record = record or {}
        self.result = None
        self.setObjectName("dialogWindow")
        title = f"{'Editar' if record else 'Nuevo'} {table_name}"
        self.setWindowTitle(title)
        self.resize(560, min(860, 160 + len(FORM_FIELDS.get(self.table_name, [])) * 92))
        self.fields = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        main_card = QFrame()
        main_card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(main_card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)

        self._pending_username_update = False

        for field_name, field_type in FORM_FIELDS.get(self.table_name, []):
            label = QLabel(field_name.replace("_", " ").title())
            label.setObjectName("subtitleText")
            label.setFont(QFont("Segoe UI", 10))
            form_layout.addWidget(label)

            input_widget = self._build_field(field_name, field_type)
            self.fields[field_name] = (input_widget, field_type)
            if hasattr(input_widget, '_internal_combo') and input_widget._internal_combo:
                self.fields[field_name] = (input_widget._internal_combo, field_type)
            form_layout.addWidget(input_widget)

        if self.table_name == "empleados" and not self.record:
            nombre_widget = self.fields.get("nombre", (None, None))[0]
            rol_widget = self.fields.get("rol", (None, None))[0]
            if nombre_widget:
                nombre_widget.textChanged.connect(self.update_username_preview)
            if rol_widget:
                rol_widget.textChanged.connect(self.update_username_preview)
            self.update_username_preview()

        if self.table_name == "boletos":
            viaje_widget = self.fields.get("id_viaje", (None, None))[0]
            asiento_widget = self.fields.get("numero_asiento", (None, None))[0]
            costo_widget = self.fields.get("costo_final", (None, None))[0]
            if viaje_widget and costo_widget:
                if hasattr(viaje_widget, '_is_boleto_viaje'):
                    viaje_widget.currentIndexChanged.connect(lambda: self.update_boleto_preview())
                    viaje_widget.activated.connect(lambda: self.update_boleto_preview())
            if asiento_widget and asiento_widget.objectName() != "dialogCard":
                asiento_widget.textChanged.connect(lambda: self.update_boleto_preview())
            self.update_boleto_preview()

        scroll.setWidget(scroll_widget)
        card_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("secondaryAction")
        cancel_btn.setIcon(self._icon("fa5s.times", QStyle.StandardPixmap.SP_DialogCancelButton))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.setObjectName("successAction")
        save_btn.setIcon(self._icon("fa5s.save", QStyle.StandardPixmap.SP_DialogSaveButton))
        save_btn.clicked.connect(self.save_record)
        button_layout.addWidget(save_btn)

        card_layout.addLayout(button_layout)
        main_layout.addWidget(main_card)

    def showEvent(self, event):
        super().showEvent(event)
        if self.table_name == "boletos":
            self.update_boleto_preview()


    def _build_field(self, field_name, field_type):
        current_value = self.record.get(field_name, "")

        if field_type == "select":
            ref_table = REFERENCE_TABLES.get(field_name, "")
            
            # Sección eliminada: id_cliente ya no existe en boletos (datos del cliente ahora en viajes)
            # if field_name == "id_cliente" and self.table_name == "boletos":
            #     (Código anterior referencia tabla clientes eliminada)
            
            widget = QComboBox()
            widget.addItem("-- Seleccionar --", None)
            
            if field_name == "id_viaje" and self.table_name == "boletos":
                widget._is_boleto_viaje = True
            
            if ref_table:
                id_field = TABLES[ref_table]["id_field"]
                ref_rows = load_rows(ref_table)
                for ref_row in ref_rows:
                    widget.addItem(table_record_label(ref_table, ref_row), ref_row)
                if current_value:
                    for index, ref_row in enumerate(ref_rows, start=1):
                        if ref_row.get(id_field, "") == current_value:
                            widget.setCurrentIndex(index)
                            break
            return widget

        if field_type == "auto_number":
            widget = QLineEdit()
            widget.setReadOnly(True)
            widget.setPlaceholderText("Se calculará automáticamente")
            widget.setText(str(current_value))
            return widget

        if field_type == "password":
            widget = QLineEdit()
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            if not self.record:
                widget.setPlaceholderText("Ingrese la contraseña")
            return widget

        if field_type == "date":
            widget = QDateEdit()
            widget.setDisplayFormat("yyyy-MM-dd")
            widget.setCalendarPopup(True)
            if current_value:
                widget.setDate(QDate.fromString(current_value, "yyyy-MM-dd"))
            else:
                widget.setDate(QDate.currentDate())
            return widget

        if field_type == "bool":
            widget = QCheckBox()
            widget.setChecked(str(current_value).lower() in {"true", "1", "si", "sí", "yes"})
            return widget

        if field_type == "interface":
            widget = QComboBox()
            widget.addItems(INTERFACE_OPTIONS)
            if current_value:
                idx = widget.findText(current_value)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            return widget

        widget = QLineEdit()
        widget.setText(str(current_value))
        widget.setPlaceholderText(field_name)

        if field_name in INTEGER_FIELDS:
            widget.setValidator(QIntValidator(0, 999999999, widget))
        elif field_name in DECIMAL_FIELDS:
            validator = QDoubleValidator(0.0, 999999999.99, 2, widget)
            validator.setNotation(QDoubleValidator.Notation.StandardNotation)
            widget.setValidator(validator)

        if field_type == "username_auto":
            if self.record:
                widget.setReadOnly(True)
            else:
                widget.setReadOnly(True)
                widget.setPlaceholderText("Se generará automáticamente")
        return widget

    def update_username_preview(self):
        if self.table_name != "empleados" or self.record:
            return
        nombre_widget = self.fields.get("nombre", (None, None))[0]
        rol_widget = self.fields.get("rol", (None, None))[0]
        username_widget = self.fields.get("usuario", (None, None))[0]
        if not (nombre_widget and rol_widget and username_widget):
            return

        nombre = nombre_widget.text().strip()
        rol = rol_widget.text().strip()
        username_widget.setText(generate_unique_username(nombre, rol, self.record.get("id_empleado", "")))

    def update_boleto_preview(self):
        if self.table_name != "boletos":
            return
        
        viaje_widget = self.fields.get("id_viaje", (None, None))[0]
        asiento_widget = self.fields.get("numero_asiento", (None, None))[0]
        costo_widget = self.fields.get("costo_final", (None, None))[0]
        
        if not viaje_widget or not costo_widget:
            return
        
        try:
            trip = viaje_widget.currentData()
            if not trip:
                costo_widget.setText("")
                return
            
            costo_base = float(trip.get("costo_base", "0"))
            cantidad = 1
            
            if asiento_widget:
                try:
                    cantidad = float(asiento_widget.text().strip() or "1")
                    if cantidad <= 0:
                        cantidad = 1
                except (ValueError, AttributeError):
                    cantidad = 1
            
            costo_total = costo_base * cantidad
            
            old_readonly = costo_widget.isReadOnly()
            costo_widget.setReadOnly(False)
            costo_widget.setText(f"{costo_total:.2f}")
            costo_widget.setReadOnly(old_readonly)
        except Exception:
            pass


    # FUNCIÓN DESHABILITADA: _quick_create_cliente ya no se usa (tabla clientes eliminada)
    # Los clientes ahora se manejan como datos dentro de los viajes
    # def _quick_create_cliente(self, combo):
    #     ... (código completo comentado para referencia futura)

    def _icon(self, icon_name, fallback):
        if qta is not None:
            try:
                return qta.icon(icon_name, color="#e2e8f0")
            except Exception:
                pass
        return self.style().standardIcon(fallback)

    def save_record(self):
        record = {}
        errors = []

        for field_name, (widget, field_type) in self.fields.items():
            if field_type == "select":
                data = widget.currentData()
                if not data:
                    errors.append(f"{field_name} es requerido")
                    continue
                ref_table = REFERENCE_TABLES.get(field_name, "")
                if ref_table:
                    id_field = TABLES[ref_table]["id_field"]
                    record[field_name] = data.get(id_field, "")

            elif field_type == "password":
                value = widget.text().strip()
                if not self.record and not value:
                    errors.append("Contraseña es requerida")
                    continue
                record[field_name] = hash_password(value) if value else self.record.get(field_name, "")

            elif field_type == "date":
                record[field_name] = widget.date().toString("yyyy-MM-dd")

            elif field_type == "bool":
                record[field_name] = "true" if widget.isChecked() else "false"

            elif field_type == "interface":
                record[field_name] = widget.currentText().strip()

            elif field_type == "number":
                value = widget.text().strip()
                if value and not is_valid_number(value):
                    errors.append(f"{field_name} debe ser un número")
                    continue
                record[field_name] = value or "0"

            elif field_type == "username_auto":
                record[field_name] = widget.text().strip() or self.record.get(field_name, "")

            elif field_type == "auto_number":
                trip_widget = self.fields.get("id_viaje", (None, None))[0]
                asiento_widget = self.fields.get("numero_asiento", (None, None))[0]
                trip = trip_widget.currentData() if trip_widget else None
                
                costo_base = float(trip.get("costo_base", "0")) if trip else 0.0
                cantidad = 1.0
                
                if asiento_widget:
                    try:
                        cantidad = float(asiento_widget.text().strip() or "1")
                        if cantidad <= 0:
                            cantidad = 1.0
                    except (ValueError, AttributeError):
                        cantidad = 1.0
                
                costo_total = costo_base * cantidad
                record[field_name] = f"{costo_total:.2f}"


            else:
                record[field_name] = widget.text().strip()

        if errors:
            QMessageBox.warning(self, "Validación", "\n".join(errors))
            return

        for field_name, _field_type in FORM_FIELDS.get(self.table_name, []):
            if field_name not in record and field_name in self.record:
                record[field_name] = self.record[field_name]

        self.result = record
        self.accept()


class TablePanel(QWidget):
    def __init__(self, parent, gui_app, table_name, permissions=None):
        super().__init__(parent)
        self.gui_app = gui_app
        self.table_name = table_name
        self.permissions = permissions or {}
        self.rows = []
        self.show_deleted = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)

        surface = QFrame()
        surface.setObjectName("surfaceCard")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setSpacing(12)
        surface_layout.setContentsMargins(16, 16, 16, 16)

        toolbar = QHBoxLayout()

        if self.permissions.get("create", False):
            new_btn = QPushButton("Nuevo")
            new_btn.setObjectName("successAction")
            new_btn.setIcon(self._icon("fa5s.plus-circle", QStyle.StandardPixmap.SP_FileDialogNewFolder))
            new_btn.clicked.connect(self.on_new)
            toolbar.addWidget(new_btn)

        if self.permissions.get("edit", False):
            edit_btn = QPushButton("Editar")
            edit_btn.setObjectName("primaryAction")
            edit_btn.setIcon(self._icon("fa5s.edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
            edit_btn.clicked.connect(self.on_edit)
            toolbar.addWidget(edit_btn)

        if self.permissions.get("delete", False):
            delete_btn = QPushButton("Eliminar")
            delete_btn.setObjectName("dangerAction")
            delete_btn.setIcon(self._icon("fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon))
            delete_btn.clicked.connect(self.on_delete)
            toolbar.addWidget(delete_btn)

        deleted_btn = QPushButton("Ver borrados")
        deleted_btn.setObjectName("secondaryAction")
        deleted_btn.setIcon(self._icon("fa5s.history", QStyle.StandardPixmap.SP_FileDialogListView))
        deleted_btn.clicked.connect(self.show_deleted_records)
        toolbar.addWidget(deleted_btn)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setObjectName("warningAction")
        refresh_btn.setIcon(self._icon("fa5s.sync-alt", QStyle.StandardPixmap.SP_BrowserReload))
        refresh_btn.clicked.connect(self.refresh_table)
        toolbar.addWidget(refresh_btn)

        if self.table_name == "boletos":
            ticket_btn = QPushButton("Ver Boleto")
            ticket_btn.setObjectName("primaryAction")
            ticket_btn.setIcon(self._icon("fa5s.receipt", QStyle.StandardPixmap.SP_FileIcon))
            ticket_btn.clicked.connect(self.show_ticket)
            toolbar.addWidget(ticket_btn)

        if self.table_name == "reportes":
            report_btn = QPushButton("Reporte")
            report_btn.setObjectName("warningAction")
            report_btn.setIcon(self._icon("fa5s.chart-bar", QStyle.StandardPixmap.SP_FileDialogInfoView))
            report_btn.clicked.connect(self.show_report_summary)
            toolbar.addWidget(report_btn)

        toolbar.addStretch()
        surface_layout.addLayout(toolbar)

        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escriba para filtrar en cualquier columna...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)

        self.show_deleted_checkbox = QCheckBox("Mostrar borrados")
        self.show_deleted_checkbox.setObjectName("subtitleText")
        self.show_deleted_checkbox.stateChanged.connect(self.toggle_deleted_rows)
        search_layout.addWidget(self.show_deleted_checkbox)
        surface_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setObjectName("recordsTable")
        headers = TREE_HEADERS.get(self.table_name, [])
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table.setSortingEnabled(True)
        surface_layout.addWidget(self.table)

        layout.addWidget(surface)
        self.refresh_table()

    def _icon(self, icon_name, fallback):
        if qta is not None:
            try:
                return qta.icon(icon_name, color="#e2e8f0")
            except Exception:
                pass
        return self.style().standardIcon(fallback)

    def filter_table(self, text):
        query = text.lower().strip()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def toggle_deleted_rows(self, state):
        self.show_deleted = state == Qt.CheckState.Checked.value
        self.refresh_table()

    def show_deleted_records(self):
        dialog = DeletedRecordsDialog(self, self.table_name)
        dialog.exec()

    def refresh_table(self):
        self.table.setSortingEnabled(False)
        self.rows = load_rows(self.table_name, include_deleted=self.show_deleted)
        self.table.setRowCount(0)

        if not self.rows:
            self.table.setRowCount(1)
            message = QTableWidgetItem("No hay registros disponibles")
            message.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(0, 0, message)
            self.table.setSpan(0, 0, 1, max(1, len(TREE_HEADERS.get(self.table_name, []))))
            return

        for row in self.rows:
            values = table_display_values(self.table_name, row)
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if str(row.get("is_deleted", "")).lower() == "true":
                    item.setForeground(QBrush(QColor("#94a3b8")))
                    item.setToolTip(f"Eliminado por: {row.get('deleted_by', '')} | Fecha: {row.get('deleted_at', '')}")
                self.table.setItem(row_pos, col_idx, item)

        self.table.setSortingEnabled(True)
        if hasattr(self, "search_input") and self.search_input.text():
            self.filter_table(self.search_input.text())

    def _is_referenced(self, table_name, record_id):
        if table_name == "rutas":
            return any(viaje.get("id_ruta", "") == record_id for viaje in load_rows("viajes"))
        if table_name == "autobuses":
            return any(viaje.get("id_autobus", "") == record_id for viaje in load_rows("viajes"))
        if table_name == "viajes":
            return any(boleto.get("id_viaje", "") == record_id for boleto in load_rows("boletos")) or any(reporte.get("id_viaje", "") == record_id for reporte in load_rows("reportes"))
        if table_name == "empleados":
            return any(acceso.get("id_empleado", "") == record_id for acceso in load_rows("accesos"))
        return False

    def on_new(self):
        dialog = RecordDialog(self, self.gui_app, self.table_name)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result:
            return

        record = dialog.result
        id_field = TABLES[self.table_name]["id_field"]
        if id_field and not record.get(id_field):
            record[id_field] = generate_id(id_field)

        if self.table_name == "empleados":
            record["usuario"] = record.get("usuario", "") or generate_unique_username(record.get("nombre", ""), record.get("rol", ""), record.get(id_field, ""))
            if not record.get("contrasena_encriptada"):
                record["contrasena_encriptada"] = hash_password("1234")

        if self.table_name == "viajes":
            if not get_row("rutas", record.get("id_ruta", "")):
                QMessageBox.warning(self, "Validación", "No existe la ruta seleccionada.")
                return
            if not get_row("autobuses", record.get("id_autobus", "")):
                QMessageBox.warning(self, "Validación", "No existe el autobus seleccionado.")
                return

        if self.table_name == "boletos":
            trip = get_row("viajes", record.get("id_viaje", ""))
            if not trip:
                QMessageBox.warning(self, "Validación", "No existe el viaje seleccionado.")
                return
            if int(float(get_trip_available_seats(trip))) <= 0:
                QMessageBox.warning(self, "Validación", "El viaje no tiene asientos disponibles.")
                return
            if any(boleto.get("id_viaje", "") == record.get("id_viaje", "") and boleto.get("numero_asiento", "") == record.get("numero_asiento", "") for boleto in load_rows("boletos")):
                QMessageBox.warning(self, "Validación", "Ese asiento ya fue asignado para este viaje.")
                return
            record["costo_final"] = trip.get("costo_base", "0")

        if self.table_name == "accesos" and not record.get("id_empleado"):
            QMessageBox.warning(self, "Validación", "Seleccione un empleado.")
            return

        if not validate_foreign_keys(self.table_name, record):
            QMessageBox.warning(self, "Validación", "Revise las relaciones seleccionadas.")
            return

        self.rows.append(record)
        save_rows(self.table_name, self.rows)
        self.refresh_table()
        if self.table_name == "boletos":
            dialog = TicketDialog(self, record)
            dialog.exec()
        QMessageBox.information(self, "Éxito", f"Se agregó nuevo registro a {self.table_name}.")

    def on_edit(self):
        if not self.table.selectedIndexes():
            QMessageBox.information(self, "Selección", "Seleccione un registro para editar.")
            return

        row_idx = self.table.selectedIndexes()[0].row()
        if not (0 <= row_idx < len(self.rows)):
            return

        record = self.rows[row_idx]
        dialog = RecordDialog(self, self.gui_app, self.table_name, record)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result:
            return

        updated = dialog.result
        id_field = TABLES[self.table_name]["id_field"]
        updated[id_field] = record[id_field]

        if self.table_name == "empleados":
            updated["usuario"] = updated.get("usuario", "") or generate_unique_username(updated.get("nombre", ""), updated.get("rol", ""), record.get(id_field, ""))

        if self.table_name == "boletos":
            trip = get_row("viajes", updated.get("id_viaje", ""))
            if not trip:
                QMessageBox.warning(self, "Validación", "No existe el viaje seleccionado.")
                return
            if any(
                boleto.get("id_boleto", "") != record[id_field]
                and boleto.get("id_viaje", "") == updated.get("id_viaje", "")
                and boleto.get("numero_asiento", "") == updated.get("numero_asiento", "")
                for boleto in load_rows("boletos")
            ):
                QMessageBox.warning(self, "Validación", "Ese asiento ya fue asignado para este viaje.")
                return
            updated["costo_final"] = trip.get("costo_base", "0")

        if self.table_name == "viajes":
            if not get_row("rutas", updated.get("id_ruta", "")):
                QMessageBox.warning(self, "Validación", "No existe la ruta seleccionada.")
                return
            if not get_row("autobuses", updated.get("id_autobus", "")):
                QMessageBox.warning(self, "Validación", "No existe el autobus seleccionado.")
                return

        if not validate_foreign_keys(self.table_name, updated):
            QMessageBox.warning(self, "Validación", "Revise las relaciones seleccionadas.")
            return

        self.rows[row_idx] = updated
        save_rows(self.table_name, self.rows)
        self.refresh_table()
        QMessageBox.information(self, "Éxito", "Registro actualizado.")

    def get_selected_row(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selección", "Seleccione un registro.")
            return None

        row_idx = selected_rows[0].row()
        if 0 <= row_idx < len(self.rows):
            return self.rows[row_idx]
        return None

    def on_delete(self):
        row = self.get_selected_row()
        if not row:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar",
            "¿Desea eliminar el registro seleccionado?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        id_field = TABLES[self.table_name]["id_field"]
        target_id = row.get(id_field, "")
        if self._is_referenced(self.table_name, target_id):
            QMessageBox.warning(self, "Validación", "No se puede eliminar porque tiene registros relacionados.")
            return

        # Soft delete: marcar registro en lugar de eliminar físicamente
        rows = load_rows(self.table_name, include_deleted=True)
        for existing in rows:
            if existing.get(id_field, "") == target_id:
                existing["is_deleted"] = "true"
                existing["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                existing["deleted_by"] = self.gui_app.current_employee.get("id_empleado", "") if self.gui_app.current_employee else ""
                break
        save_rows(self.table_name, rows)
        self.refresh_table()

    def show_ticket(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = TicketDialog(self, row)
        dialog.exec()

    def show_report_summary(self):
        dialog = ReportSummaryDialog(self)
        dialog.exec()
