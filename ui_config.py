import re
import unicodedata
from datetime import datetime

from insert import (
    get_display_value,
    get_trip_available_seats,
    get_trip_total_seats,
    load_rows,
)

REFERENCE_TABLES = {
    "id_cliente": "clientes",
    "id_terminal": "terminales",
    "id_lugar_origen": "lugares",
    "id_lugar_destino": "lugares",
    "id_viaje": "viajes",
    "id_usuario": "usuarios",
    "id_rol": "roles",
}

FORM_FIELDS = {
    "roles": [
        ("nombre_rol", "text"),
        ("permisos", "text"),
    ],
    "clientes": [
        ("nombre", "text"),
        ("apellido", "text"),
        ("correo", "text"),
        ("telefono", "text"),
    ],
    "terminales": [
        ("nombre_terminal", "text"),
        ("direccion", "text"),
        ("codigo_postal", "text"),
    ],
    "lugares": [
        ("nombre_lugar", "text"),
        ("codigo_postal", "text"),
    ],
    "viajes": [
        ("id_lugar_origen", "select"),
        ("id_lugar_destino", "select"),
        ("fecha", "date"),
        ("km_recorrer", "text"),
        ("tiempo_estimado_llegada", "text"),
        ("cupos_totales", "text"),
        ("horario", "text"),
        ("costo_asiento", "number"),
    ],
    "usuarios": [
        ("password_hash", "password"),
        ("id_rol", "select"),
        ("id_terminal", "select"),
        ("fecha_contratacion", "date"),
        ("nombre", "text"),
        ("apellido", "text"),
        ("direccion", "text"),
        ("correo", "text"),
        ("numero", "text"),
        ("curp", "text"),
        ("rfc", "text"),
        ("sueldo", "number"),
    ],
    "reservaciones": [
        ("id_usuario", "select"),
        ("id_terminal", "select"),
        ("id_cliente", "select"),
        ("id_viaje", "select"),
        ("fecha_reservacion", "date"),
        ("asientos", "number"),
        ("estado", "state"),
    ],
}

TREE_HEADERS = {
    "roles": ["Rol", "Permisos"],
    "clientes": ["Nombre", "Apellido", "Correo", "Telefono"],
    "terminales": ["Terminal", "Direccion", "CP"],
    "lugares": ["Nombre", "CP"],
    "viajes": ["Origen", "Destino", "Fecha", "Horario", "Km", "Cupos", "Disponibles", "Costo"],
    "usuarios": ["Username", "Rol", "Nombre", "Terminal", "Correo", "Telefono", "Contratacion"],
    "reservaciones": ["Cliente", "Viaje", "Trabajador", "Terminal", "Fecha", "Asientos", "Estado", "Total"],
}

STATE_OPTIONS = ["pendiente", "confirmada", "cancelada"]


def is_valid_number(value):
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False


def normalize_text(value):
    normalized = unicodedata.normalize("NFD", value)
    without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_accents


def build_username_base(nombre, apellido):
    base_name = f"{nombre}.{apellido}".strip(".")
    base_name = normalize_text(base_name).lower()
    base_name = re.sub(r"[^a-z0-9._]", "", base_name)
    base_name = re.sub(r"\.+", ".", base_name).strip(".")
    return base_name or "usuario"


def is_trip_outdated(row):
    fecha = row.get("fecha", "").strip()
    horario = row.get("horario", "").strip()
    if not fecha:
        return False

    if horario:
        try:
            trip_datetime = datetime.strptime(f"{fecha} {horario}", "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                trip_datetime = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                return False
    else:
        try:
            trip_datetime = datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            return False

    return trip_datetime < datetime.now()


def generate_unique_username(nombre, apellido, exclude_id=None):
    base_name = build_username_base(nombre, apellido)
    users = load_rows("usuarios")
    existing = {
        user.get("username", "").strip().lower()
        for user in users
        if user.get("id_usuario", "") != exclude_id
    }
    if base_name not in existing:
        return base_name

    counter = 1
    while f"{base_name}{counter}" in existing:
        counter += 1
    return f"{base_name}{counter}"


def table_record_label(table_name, row):
    if table_name == "roles":
        return row.get("nombre_rol", "").strip()
    if table_name == "clientes":
        return f"{row.get('nombre', '')} {row.get('apellido', '')} - {row.get('correo', '')}".strip()
    if table_name == "terminales":
        return f"{row.get('nombre_terminal', '')} - {row.get('codigo_postal', '')}".strip()
    if table_name == "lugares":
        return f"{row.get('nombre_lugar', '')} - {row.get('codigo_postal', '')}".strip()
    if table_name == "viajes":
        origen = get_display_value("lugares", row.get("id_lugar_origen", ""))
        destino = get_display_value("lugares", row.get("id_lugar_destino", ""))
        disponibles = get_trip_available_seats(row)
        total = get_trip_total_seats(row)
        if is_trip_outdated(row):
            estado = "FUERA DE HORARIO"
        else:
            estado = "LLENO" if disponibles <= 0 else f"{disponibles}/{total} disponibles"
        return f"{origen} -> {destino} | {row.get('fecha', '')} {row.get('horario', '')} | {estado}".strip()
    if table_name == "usuarios":
        terminal = get_display_value("terminales", row.get("id_terminal", ""))
        nombre = f"{row.get('nombre', '')} {row.get('apellido', '')}".strip()
        return f"{row.get('username', '')} - {nombre} ({terminal})".strip()
    if table_name == "reservaciones":
        cliente = get_display_value("clientes", row.get("id_cliente", ""))
        viaje = get_display_value("viajes", row.get("id_viaje", ""))
        return f"{cliente} | {viaje} | {row.get('estado', '')}".strip()
    return ""


def table_display_values(table_name, row):
    if table_name == "roles":
        return [row.get("nombre_rol", ""), row.get("permisos", "")]
    if table_name == "clientes":
        return [row.get("nombre", ""), row.get("apellido", ""), row.get("correo", ""), row.get("telefono", "")]
    if table_name == "terminales":
        return [row.get("nombre_terminal", ""), row.get("direccion", ""), row.get("codigo_postal", "")]
    if table_name == "lugares":
        return [row.get("nombre_lugar", ""), row.get("codigo_postal", "")]
    if table_name == "viajes":
        total = get_trip_total_seats(row)
        available = get_trip_available_seats(row)
        if is_trip_outdated(row):
            availability_text = "FUERA DE HORARIO"
        else:
            availability_text = "LLENO" if available <= 0 else str(available)
        return [
            get_display_value("lugares", row.get("id_lugar_origen", "")),
            get_display_value("lugares", row.get("id_lugar_destino", "")),
            row.get("fecha", ""),
            row.get("horario", ""),
            row.get("km_recorrer", ""),
            str(total),
            availability_text,
            f"${row.get('costo_asiento', '0')}",
        ]
    if table_name == "usuarios":
        return [
            row.get("username", ""),
            get_display_value("roles", row.get("id_rol", "")),
            f"{row.get('nombre', '')} {row.get('apellido', '')}".strip(),
            get_display_value("terminales", row.get("id_terminal", "")),
            row.get("correo", ""),
            row.get("numero", ""),
            row.get("fecha_contratacion", ""),
        ]
    if table_name == "reservaciones":
        return [
            get_display_value("clientes", row.get("id_cliente", "")),
            get_display_value("viajes", row.get("id_viaje", "")),
            get_display_value("usuarios", row.get("id_usuario", "")),
            get_display_value("terminales", row.get("id_terminal", "")),
            row.get("fecha_reservacion", ""),
            row.get("asientos", ""),
            row.get("estado", ""),
            f"${row.get('costo_total', '0')}",
        ]
    return []
