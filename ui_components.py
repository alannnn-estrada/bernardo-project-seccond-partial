from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QFrame, QAbstractItemView, QSizePolicy, QHeaderView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QBrush
from PySide6.QtWidgets import QDateEdit, QScrollArea, QStyle

try:
    import qtawesome as qta
except ImportError:
    qta = None

from insert import (
    TABLES,
    generate_id,
    get_default_terminal,
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
    REFERENCE_TABLES,
    STATE_OPTIONS,
    TREE_HEADERS,
    build_username_base,
    generate_unique_username,
    is_valid_number,
    is_trip_outdated,
    table_display_values,
    table_record_label,
)


class TicketDialog(QDialog):
    def __init__(self, parent, reservation):
        super().__init__(parent)
        self.reservation = reservation
        self.setWindowTitle("Ticket de Reservación")
        self.setFixedSize(380, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        card = QFrame()
        card.setObjectName("surfaceCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)
        
        title = QLabel("TICKET DE RESERVACIÓN")
        title.setObjectName("heroTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)
        
        cliente = get_display_value("clientes", self.reservation.get("id_cliente", ""))
        viaje_row = get_row("viajes", self.reservation.get("id_viaje", ""))
        origen = get_display_value("lugares", viaje_row.get("id_lugar_origen", "")) if viaje_row else ""
        destino = get_display_value("lugares", viaje_row.get("id_lugar_destino", "")) if viaje_row else ""
        fecha = viaje_row.get("fecha", "") if viaje_row else ""
        horario = viaje_row.get("horario", "") if viaje_row else ""
        asientos = self.reservation.get("asientos", "0")
        costo_asiento = viaje_row.get("costo_asiento", "0") if viaje_row else "0"
        total = self.reservation.get("costo_total", "0")
        
        details = [
            f"ID Reservación: {self.reservation.get('id_reservacion', '')}",
            f"Cliente: {cliente}",
            f"Origen: {origen}",
            f"Destino: {destino}",
            f"Fecha Salida: {fecha} {horario}",
            f"Asientos: {asientos}",
            f"Costo por Asiento: ${costo_asiento}",
            "-" * 30,
            f"TOTAL PAGADO: ${total}",
            f"Estado: {self.reservation.get('estado', '').upper()}"
        ]
        
        for text in details:
            lbl = QLabel(text)
            lbl.setFont(QFont("Consolas", 10))
            if "TOTAL" in text:
                lbl.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
            card_layout.addWidget(lbl)
            
        layout.addWidget(card)
        
        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryAction")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class SearchSelectDialog(QDialog):
    def __init__(self, parent, table_name, title=None, initial_filter=""):
        super().__init__(parent)
        self.result = None
        self.table_name = table_name
        self.filtered_rows = []
        self.setObjectName("dialogWindow")

        self.setWindowTitle(title or f"Seleccionar {table_name}")
        self.setGeometry(0, 0, 560, 430)
        self.setMinimumSize(520, 380)
        self.setup_ui(initial_filter)

    def setup_ui(self, initial_filter):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Título
        title = QLabel(f"Buscar {self.table_name}")
        title.setObjectName("dialogTitle")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(title)

        # Campo de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(f"Escriba para filtrar...")
        self.search_input.setText(initial_filter)
        self.search_input.setObjectName("dialogSearch")
        self.search_input.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search_input)

        # Tabla de resultados
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

        # Botones
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
            if self.table_name == "viajes" and is_trip_outdated(row):
                continue
            label = table_record_label(self.table_name, row)
            if query and query not in label.lower():
                continue
            self.filtered_rows.append(row)
            row_pos = self.table.rowCount()
            self.table.insertRow(row_pos)
            item = QTableWidgetItem(label)
            self.table.setItem(row_pos, 0, item)

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
        self.setGeometry(0, 0, 500, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Scroll area para formulario
        scroll = QScrollArea()
        scroll.setObjectName("dialogScroll")
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_widget.setObjectName("dialogCard")
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(18, 18, 18, 18)

        self.fields = {}
        field_list = FORM_FIELDS.get(self.table_name, [])

        for field_name, field_type in field_list:

            label = QLabel(field_name.replace("_", " ").title())
            label.setObjectName("subtitleText")
            label.setFont(QFont("Segoe UI", 10))
            form_layout.addWidget(label)

            if field_type == "select":
                input_widget = QComboBox()
                ref_table = REFERENCE_TABLES.get(field_name, "")
                if ref_table:
                    id_field = TABLES[ref_table]["id_field"]
                    ref_rows = load_rows(ref_table)
                    input_widget.addItem("-- Seleccionar --", None)
                    for ref_row in ref_rows:
                        label_text = table_record_label(ref_table, ref_row)
                        input_widget.addItem(label_text, ref_row)
                    current_value = self.record.get(field_name, "")
                    if not current_value and self.table_name == "reservaciones" and not self.record:
                        if field_name == "id_usuario":
                            current_value = self.gui_app.current_user.get("id_usuario", "")
                        elif field_name == "id_terminal":
                            current_value = self.gui_app.current_user.get("id_terminal", "")
                    if current_value:
                        for index, ref_row in enumerate(ref_rows, start=1):
                            if ref_row.get(id_field, "") == current_value:
                                input_widget.setCurrentIndex(index)
                                break

            elif field_type == "password":
                input_widget = QLineEdit()
                input_widget.setEchoMode(QLineEdit.EchoMode.Password)
                if field_name == "password_hash" and not self.record:
                    input_widget.setPlaceholderText("Ingrese la contraseña")

            elif field_type == "date":
                input_widget = QDateEdit()
                input_widget.setDisplayFormat("yyyy-MM-dd")
                input_widget.setDate(
                    QDate.fromString(self.record.get(field_name, ""), "yyyy-MM-dd")
                    if self.record.get(field_name)
                    else QDate.currentDate()
                )
                input_widget.setCalendarPopup(True)

            elif field_type == "state":
                input_widget = QComboBox()
                for state in STATE_OPTIONS:
                    input_widget.addItem(state, state)
                if self.record.get(field_name):
                    idx = input_widget.findData(self.record.get(field_name))
                    if idx >= 0:
                        input_widget.setCurrentIndex(idx)

            elif field_type == "number":
                input_widget = QLineEdit()
                input_widget.setPlaceholderText("0")
                if self.record.get(field_name):
                    input_widget.setText(str(self.record.get(field_name, "")))

            elif field_type == "username_auto":
                input_widget = QLineEdit()
                if self.record:
                    input_widget.setText(self.record.get(field_name, ""))
                    input_widget.setReadOnly(True)
                else:
                    input_widget.setPlaceholderText("Se generará automáticamente")
                    input_widget.setReadOnly(True)
                    # Preview de username
                    self.update_username_preview()

            else:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText(field_name)
                if self.record.get(field_name):
                    input_widget.setText(str(self.record.get(field_name, "")))

            self.fields[field_name] = (input_widget, field_type)
            form_layout.addWidget(input_widget)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Botones
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

        layout.addLayout(button_layout)

    def update_username_preview(self):
        """Actualiza preview de usuario generado automáticamente"""
        if self.table_name != "usuarios" or self.record:
            return
        nombre_widget = self.fields.get("nombre", (None, None))[0]
        apellido_widget = self.fields.get("apellido", (None, None))[0]
        username_widget = self.fields.get("username", (None, None))[0]

        if nombre_widget and apellido_widget and username_widget:
            nombre = nombre_widget.text().strip()
            apellido = apellido_widget.text().strip()
            if nombre or apellido:
                base = build_username_base(nombre, apellido)
                unique = generate_unique_username(nombre, apellido, self.record.get("id_usuario", ""))
                username_widget.setText(unique)

    def save_record(self):
        record = {}
        errors = []

        for field_name, (widget, field_type) in self.fields.items():
            if field_type == "select":
                data = widget.currentData()
                if not data:
                    errors.append(f"{field_name} es requerido")
                    continue
                # Obtener ID del objeto seleccionado
                ref_table = REFERENCE_TABLES.get(field_name, "")
                if ref_table:
                    id_field = f"id_{ref_table.rstrip('s')}"
                    record[field_name] = data.get(id_field, "")

            elif field_type == "password":
                value = widget.text().strip()
                if not self.record and not value:
                    errors.append("Contraseña es requerida")
                    continue
                if value:
                    record[field_name] = hash_password(value)
                elif self.record:
                    record[field_name] = self.record.get(field_name, "")

            elif field_type == "date":
                record[field_name] = widget.date().toString("yyyy-MM-dd")

            elif field_type == "state":
                record[field_name] = widget.currentData() or widget.currentText()

            elif field_type == "number":
                value = widget.text().strip()
                if value and not is_valid_number(value):
                    errors.append(f"{field_name} debe ser un número")
                    continue
                record[field_name] = value or "0"

            elif field_type == "username_auto":
                record[field_name] = widget.text().strip() or self.record.get(field_name, "")

            else:
                record[field_name] = widget.text().strip()

        if errors:
            QMessageBox.warning(self, "Validación", "\n".join(errors))
            return

        # Copiar campos de solo lectura
        for field_name, _field_type in FORM_FIELDS.get(self.table_name, []):
            if field_name not in record and field_name in self.record:
                record[field_name] = self.record[field_name]

        self.result = record
        self.accept()

    def _icon(self, icon_name, fallback):
        if qta is not None:
            try:
                return qta.icon(icon_name, color="#e2e8f0")
            except Exception:
                pass
        return self.style().standardIcon(fallback)


class TablePanel(QWidget):
    def __init__(self, parent, gui_app, table_name):
        super().__init__(parent)
        self.gui_app = gui_app
        self.table_name = table_name
        self.rows = []
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

        # Toolbar
        toolbar = QHBoxLayout()

        new_btn = QPushButton("Nuevo")
        new_btn.setObjectName("successAction")
        new_btn.setIcon(self._icon("fa5s.plus-circle", QStyle.StandardPixmap.SP_FileDialogNewFolder))
        new_btn.clicked.connect(self.on_new)
        toolbar.addWidget(new_btn)

        edit_btn = QPushButton("Editar")
        edit_btn.setObjectName("primaryAction")
        edit_btn.setIcon(self._icon("fa5s.edit", QStyle.StandardPixmap.SP_FileDialogDetailedView))
        edit_btn.clicked.connect(self.on_edit)
        toolbar.addWidget(edit_btn)

        delete_btn = QPushButton("Eliminar")
        delete_btn.setObjectName("dangerAction")
        delete_btn.setIcon(self._icon("fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon))
        delete_btn.clicked.connect(self.on_delete)
        toolbar.addWidget(delete_btn)

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setObjectName("warningAction")
        refresh_btn.setIcon(self._icon("fa5s.sync-alt", QStyle.StandardPixmap.SP_BrowserReload))
        refresh_btn.clicked.connect(self.refresh_table)
        toolbar.addWidget(refresh_btn)

        if self.table_name == "reservaciones":
            self.ticket_btn = QPushButton("Ver Ticket")
            self.ticket_btn.setObjectName("primaryAction")
            self.ticket_btn.setIcon(self._icon("fa5s.receipt", QStyle.StandardPixmap.SP_FileIcon))
            self.ticket_btn.clicked.connect(self.show_ticket)
            toolbar.addWidget(self.ticket_btn)
            
        if self.table_name == "clientes":
            self.ver_res_btn = QPushButton("Ver Reservaciones")
            self.ver_res_btn.setObjectName("primaryAction")
            self.ver_res_btn.setIcon(self._icon("fa5s.list-alt", QStyle.StandardPixmap.SP_FileDialogListView))
            self.ver_res_btn.clicked.connect(self.show_client_reservations)
            toolbar.addWidget(self.ver_res_btn)

        toolbar.addStretch()
        surface_layout.addLayout(toolbar)

        # Buscador y Filtro
        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escriba para filtrar en cualquier columna...")
        self.search_input.setObjectName("searchInput")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)
        surface_layout.addLayout(search_layout)

        # Tabla
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

    def refresh_table(self):
        self.table.setSortingEnabled(False)
        self.rows = load_rows(self.table_name)
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
                self.table.setItem(row_pos, col_idx, item)
                if self.table_name == "viajes" and is_trip_outdated(row):
                    item.setForeground(QBrush(QColor("#f87171")))

        if self.table_name == "viajes":
            for row_index, row in enumerate(self.rows):
                if is_trip_outdated(row):
                    for col_index in range(self.table.columnCount()):
                        item = self.table.item(row_index, col_index)
                        if item is not None:
                            item.setForeground(QBrush(QColor("#f87171")))

        self.table.setSortingEnabled(True)
        if hasattr(self, "search_input") and self.search_input.text():
            self.filter_table(self.search_input.text())

    def on_new(self):
        dialog = RecordDialog(self, self.gui_app, self.table_name)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result:
            record = dialog.result

            # Asignar ID y campos auto
            if "id_" + self.table_name.rstrip("s") not in record or not record["id_" + self.table_name.rstrip("s")]:
                record["id_" + self.table_name.rstrip("s")] = generate_id("id_" + self.table_name.rstrip("s"))

            # Auto-assign usuario y terminal para reservaciones si siguen vacíos
            if self.table_name == "reservaciones":
                trip_id = record.get("id_viaje", "")
                trip = get_row("viajes", trip_id)
                if not trip:
                    QMessageBox.warning(self, "Validación", "No existe el viaje seleccionado.")
                    return
                seats = int(float(record.get("asientos", "0") or 0))
                if seats <= 0:
                    QMessageBox.warning(self, "Validación", "La reservación debe tener al menos 1 asiento.")
                    return
                available = get_trip_available_seats(trip)
                if available < seats:
                    QMessageBox.warning(self, "Cupos insuficientes", f"Solo hay {available} cupos disponibles.")
                    return
                if not record.get("id_usuario"):
                    record["id_usuario"] = self.gui_app.current_user.get("id_usuario", "")
                if not record.get("id_terminal"):
                    record["id_terminal"] = self.gui_app.current_user.get("id_terminal", "")
                record["fecha_reservacion"] = datetime.now().strftime("%Y-%m-%d")

            # Validar foreign keys
            if not validate_foreign_keys(self.table_name, record):
                QMessageBox.warning(self, "Validación", "Revise las relaciones seleccionadas.")
                return

            # Reserve cupos si es reservación
            if self.table_name == "reservaciones":
                trip_id = record.get("id_viaje", "")
                seats = int(record.get("asientos", "1"))
                trip = get_row("viajes", trip_id)
                available = get_trip_available_seats(trip) if trip else 0
                if available < seats:
                    QMessageBox.warning(self, "Cupos insuficientes", f"Solo hay {available} cupos disponibles.")
                    return
                if not reserve_trip_seats(trip_id, seats):
                    QMessageBox.warning(self, "Validación", "No se pudo actualizar la disponibilidad del viaje.")
                    return
                costo_asiento = float(trip.get("costo_asiento", "0") if trip.get("costo_asiento") else 0)
                record["costo_total"] = f"{costo_asiento * seats:.2f}"

            self.rows.append(record)
            save_rows(self.table_name, self.rows)
            self.refresh_table()
            QMessageBox.information(self, "Éxito", f"Se agregó nuevo registro a {self.table_name}.")

    def on_edit(self):
        if not self.table.selectedIndexes():
            QMessageBox.information(self, "Selección", "Seleccione un registro para editar.")
            return

        row_idx = self.table.selectedIndexes()[0].row()
        if 0 <= row_idx < len(self.rows):
            record = self.rows[row_idx]
            dialog = RecordDialog(self, self.gui_app, self.table_name, record)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result:
                updated = dialog.result
                # Mantener ID
                for key in record:
                    if key.startswith("id_"):
                        updated[key] = record[key]

                if not validate_foreign_keys(self.table_name, updated):
                    QMessageBox.warning(self, "Validación", "Revise las relaciones seleccionadas.")
                    return

                if self.table_name == "reservaciones":
                    old_trip_id = record.get("id_viaje", "")
                    new_trip_id = updated.get("id_viaje", "")
                    old_seats = int(float(record.get("asientos", "0") or 0))
                    new_seats = int(float(updated.get("asientos", "0") or 0))

                    if new_seats <= 0:
                        QMessageBox.warning(self, "Validación", "La reservación debe tener al menos 1 asiento.")
                        return

                    if old_trip_id == new_trip_id:
                        diff = new_seats - old_seats
                        if diff > 0 and not reserve_trip_seats(new_trip_id, diff):
                            QMessageBox.warning(self, "Validación", "El viaje no tiene cupos suficientes.")
                            return
                        if diff < 0 and not release_trip_seats(new_trip_id, -diff):
                            QMessageBox.warning(self, "Validación", "No se pudieron devolver los cupos al viaje.")
                            return
                    else:
                        release_trip_seats(old_trip_id, old_seats)

                        new_trip = get_row("viajes", new_trip_id)
                        if not new_trip:
                            reserve_trip_seats(old_trip_id, old_seats)
                            QMessageBox.warning(self, "Validación", "No existe el nuevo viaje seleccionado.")
                            return

                        if new_seats > get_trip_available_seats(new_trip):
                            reserve_trip_seats(old_trip_id, old_seats)
                            QMessageBox.warning(self, "Validación", "El nuevo viaje no tiene cupos suficientes.")
                            return

                        if not reserve_trip_seats(new_trip_id, new_seats):
                            reserve_trip_seats(old_trip_id, old_seats)
                            QMessageBox.warning(self, "Validación", "No se pudo reservar el nuevo viaje.")
                            return

                    new_trip_data = get_row("viajes", new_trip_id)
                    if new_trip_data:
                        costo_asiento = float(new_trip_data.get("costo_asiento", "0") if new_trip_data.get("costo_asiento") else 0)
                        updated["costo_total"] = f"{costo_asiento * new_seats:.2f}"

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

    def delete_record(self):
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

        if self.table_name == "viajes":
            trip_id = row.get("id_viaje", "")
            if any(res.get("id_viaje", "") == trip_id for res in load_rows("reservaciones")):
                QMessageBox.warning(self, "Validación", "No se puede eliminar un viaje con reservaciones activas.")
                return

        if self.table_name == "reservaciones":
            seats = int(float(row.get("asientos", "0") or 0))
            if not release_trip_seats(row.get("id_viaje", ""), seats):
                QMessageBox.warning(self, "Validación", "No se pudieron liberar los cupos del viaje, pero se eliminará el registro para evitar bloqueo por datos inconsistentes.")

        id_field = TABLES[self.table_name]["id_field"]
        target_id = row.get(id_field, "")
        rows = [existing for existing in load_rows(self.table_name) if existing.get(id_field, "") != target_id]
        save_rows(self.table_name, rows)
        self.refresh_table()

    def on_delete(self):
        self.delete_record()

    def show_ticket(self):
        row = self.get_selected_row()
        if not row:
            return
        dialog = TicketDialog(self, row)
        dialog.exec()
        
    def show_client_reservations(self):
        row = self.get_selected_row()
        if not row:
            return
        client_id = row.get("id_cliente")
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reservaciones - {row.get('nombre', '')} {row.get('apellido', '')}")
        dialog.setMinimumSize(800, 400)
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        headers = ["Viaje", "Fecha", "Asientos", "Total", "Estado"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        res_rows = load_rows("reservaciones")
        client_res = [r for r in res_rows if r.get("id_cliente") == client_id]
        
        table.setRowCount(len(client_res))
        for r_idx, r in enumerate(client_res):
            viaje = get_display_value("viajes", r.get("id_viaje", ""))
            table.setItem(r_idx, 0, QTableWidgetItem(viaje))
            table.setItem(r_idx, 1, QTableWidgetItem(r.get("fecha_reservacion", "")))
            table.setItem(r_idx, 2, QTableWidgetItem(str(r.get("asientos", ""))))
            table.setItem(r_idx, 3, QTableWidgetItem(f"${r.get('costo_total', '0')}"))
            table.setItem(r_idx, 4, QTableWidgetItem(r.get("estado", "")))
            
        layout.addWidget(table)
        dialog.exec()


