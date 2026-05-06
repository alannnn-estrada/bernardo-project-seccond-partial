import re
import unicodedata

from insert import get_display_value, load_rows

REFERENCE_TABLES = {
    "id_cliente": "clientes",
    "id_autobus": "autobuses",
    "id_ruta": "rutas",
    "id_viaje": "viajes",
    "id_empleado": "empleados",
}

FORM_FIELDS = {
    "clientes": [
        ("nombre_completo", "text"),
        ("telefono", "number"),
        ("email", "text"),
    ],
    "autobuses": [
        ("numero_unidad", "text"),
        ("modelo", "text"),
        ("capacidad_total", "number"),
        ("placa", "text"),
    ],
    "rutas": [
        ("origen", "text"),
        ("destino", "text"),
        ("distancia_estimada", "number"),
    ],
    "viajes": [
        ("id_ruta", "select"),
        ("id_autobus", "select"),
        ("fecha_salida", "date"),
        ("hora_salida", "text"),
        ("costo_base", "number"),
    ],
    "boletos": [
        ("id_viaje", "select"),
        ("id_cliente", "select"),
        ("numero_asiento", "number"),
        ("costo_final", "auto_number"),
    ],
    "empleados": [
        ("nombre", "text"),
        ("rol", "text"),
        ("usuario", "username_auto"),
        ("contrasena_encriptada", "password"),
    ],
    "accesos": [
        ("id_empleado", "select"),
        ("permiso_altas", "bool"),
        ("permiso_bajas", "bool"),
        ("permiso_modificaciones", "bool"),
        ("interfaz_accedida", "interface"),
    ],
    "reportes": [
        ("id_viaje", "select"),
        ("descripcion_incidencia", "text"),
        ("fecha_reporte", "date"),
    ],
}

TREE_HEADERS = {
    "clientes": ["Nombre completo", "Telefono", "Email"],
    "autobuses": ["Unidad", "Modelo", "Capacidad", "Placa"],
    "rutas": ["Origen", "Destino", "Distancia"],
    "viajes": ["Ruta", "Autobus", "Fecha", "Hora", "Costo base"],
    "boletos": ["Viaje", "Cliente", "Asiento", "Costo final"],
    "empleados": ["Nombre", "Rol", "Usuario"],
    "accesos": ["Empleado", "Altas", "Bajas", "Modificaciones", "Interfaz"],
    "reportes": ["Viaje", "Incidencia", "Fecha"],
}

INTERFACE_OPTIONS = ["Usuario", "Admin"]


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


def build_username_base(nombre, apellido=""):
    base_name = f"{nombre}.{apellido}".strip(".")
    base_name = normalize_text(base_name).lower()
    base_name = re.sub(r"[^a-z0-9._]", "", base_name)
    base_name = re.sub(r"\.+", ".", base_name).strip(".")
    return base_name or "usuario"


def generate_unique_username(nombre, apellido="", exclude_id=None):
    base_name = build_username_base(nombre, apellido)
    empleados = load_rows("empleados")
    existing = {
        empleado.get("usuario", "").strip().lower()
        for empleado in empleados
        if empleado.get("id_empleado", "") != exclude_id
    }
    if base_name not in existing:
        return base_name

    counter = 1
    while f"{base_name}{counter}" in existing:
        counter += 1
    return f"{base_name}{counter}"


def table_record_label(table_name, row):
    if table_name == "clientes":
        return f"{row.get('nombre_completo', '')} - {row.get('telefono', '')}".strip(" -")
    if table_name == "autobuses":
        return f"{row.get('numero_unidad', '')} | {row.get('modelo', '')} | {row.get('placa', '')}".strip(" |")
    if table_name == "rutas":
        return f"{row.get('origen', '')} -> {row.get('destino', '')} | {row.get('distancia_estimada', '')} km".strip()
    if table_name == "viajes":
        return f"{get_display_value('rutas', row.get('id_ruta', ''))} | {get_display_value('autobuses', row.get('id_autobus', ''))} | {row.get('fecha_salida', '')} {row.get('hora_salida', '')}".strip()
    if table_name == "boletos":
        return f"{get_display_value('clientes', row.get('id_cliente', ''))} | {get_display_value('viajes', row.get('id_viaje', ''))} | Asiento {row.get('numero_asiento', '')}".strip()
    if table_name == "empleados":
        return f"{row.get('nombre', '')} - {row.get('usuario', '')} ({row.get('rol', '')})".strip()
    if table_name == "accesos":
        return f"{get_display_value('empleados', row.get('id_empleado', ''))} | {row.get('interfaz_accedida', '')}".strip()
    if table_name == "reportes":
        return f"{get_display_value('viajes', row.get('id_viaje', ''))} | {row.get('descripcion_incidencia', '')}".strip()
    return ""


def table_display_values(table_name, row):
    if table_name == "clientes":
        return [row.get("nombre_completo", ""), row.get("telefono", ""), row.get("email", "")]
    if table_name == "autobuses":
        return [row.get("numero_unidad", ""), row.get("modelo", ""), row.get("capacidad_total", ""), row.get("placa", "")]
    if table_name == "rutas":
        return [row.get("origen", ""), row.get("destino", ""), row.get("distancia_estimada", "")]
    if table_name == "viajes":
        return [
            get_display_value("rutas", row.get("id_ruta", "")),
            get_display_value("autobuses", row.get("id_autobus", "")),
            row.get("fecha_salida", ""),
            row.get("hora_salida", ""),
            f"${row.get('costo_base', '0')}",
        ]
    if table_name == "boletos":
        return [
            get_display_value("viajes", row.get("id_viaje", "")),
            get_display_value("clientes", row.get("id_cliente", "")),
            row.get("numero_asiento", ""),
            f"${row.get('costo_final', '0')}",
        ]
    if table_name == "empleados":
        return [row.get("nombre", ""), row.get("rol", ""), row.get("usuario", "")]
    if table_name == "accesos":
        def yn(value):
            return "Sí" if str(value).lower() == "true" else "No"

        return [
            get_display_value("empleados", row.get("id_empleado", "")),
            yn(row.get("permiso_altas", "")),
            yn(row.get("permiso_bajas", "")),
            yn(row.get("permiso_modificaciones", "")),
            row.get("interfaz_accedida", ""),
        ]
    if table_name == "reportes":
        return [
            get_display_value("viajes", row.get("id_viaje", "")),
            row.get("descripcion_incidencia", ""),
            row.get("fecha_reporte", ""),
        ]
    return []
