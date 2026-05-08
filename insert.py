import csv
from datetime import datetime
import hashlib
import io
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_db")

TABLES = {
    "autobuses": {
        "file": "autobuses.txt",
        "id_field": "id_autobus",
        "fields": ["id_autobus", "numero_unidad", "modelo", "capacidad_total", "placa"],
    },
    "rutas": {
        "file": "rutas.txt",
        "id_field": "id_ruta",
        "fields": ["id_ruta", "origen", "destino", "distancia_estimada"],
    },
    "viajes": {
        "file": "viajes.txt",
        "id_field": "id_viaje",
        "fields": ["id_viaje", "id_ruta", "id_autobus", "fecha_salida", "hora_salida", "costo_base", "nombre_cliente", "telefono_cliente", "correo_cliente"],
    },
    "boletos": {
        "file": "boletos.txt",
        "id_field": "id_boleto",
        "fields": ["id_boleto", "id_viaje", "numero_asiento", "costo_final"],
    },
    "empleados": {
        "file": "empleados.txt",
        "id_field": "id_empleado",
        "fields": ["id_empleado", "nombre", "usuario", "contrasena_encriptada"],
    },
    "administrador": {
        "file": "administrador.txt",
        "id_field": "id_admin",
        "fields": ["id_admin", "id_empleado"],
    },
    "accesos": {
        "file": "accesos.txt",
        "id_field": "id_acceso",
        "fields": [
            "id_acceso",
            "id_admin",
            "permiso_altas",
            "permiso_bajas",
            "permiso_modificaciones",
            "interfaz_accedida",
        ],
    },
    "reportes": {
        "file": "reportes.txt",
        "id_field": "id_reporte",
        "fields": ["id_reporte", "id_viaje", "descripcion_incidencia", "fecha_reporte"],
    },
}

FIELD_LABELS = {
    "id_autobus": "ID autobús",
    "id_ruta": "ID ruta",
    "id_viaje": "ID viaje",
    "id_boleto": "ID boleto",
    "id_empleado": "ID empleado",
    "id_admin": "ID administrador",
    "id_acceso": "ID acceso",
    "id_reporte": "ID reporte",
    "nombre_cliente": "Nombre del cliente",
    "telefono_cliente": "Teléfono del cliente",
    "correo_cliente": "Correo del cliente",
    "telefono": "Telefono",
    "numero_unidad": "Número de unidad",
    "modelo": "Modelo",
    "capacidad_total": "Capacidad total",
    "placa": "Placa",
    "origen": "Origen",
    "destino": "Destino",
    "distancia_estimada": "Distancia estimada",
    "fecha_salida": "Fecha de salida (YYYY-MM-DD)",
    "hora_salida": "Hora de salida",
    "costo_base": "Costo base",
    "numero_asiento": "Número de asiento",
    "costo_final": "Costo final",
    "nombre": "Nombre",
    "rol": "Rol",
    "usuario": "Usuario",
    "contrasena_encriptada": "Contraseña encriptada",
    "permiso_altas": "Permiso altas",
    "permiso_bajas": "Permiso bajas",
    "permiso_modificaciones": "Permiso modificaciones",
    "interfaz_accedida": "Interfaz accedida",
    "descripcion_incidencia": "Descripción incidencia",
    "fecha_reporte": "Fecha reporte (YYYY-MM-DD)",
}


REFERENCE_MAP = {
    "viajes": [
        ("id_ruta", "rutas", "id_ruta"),
        ("id_autobus", "autobuses", "id_autobus"),
    ],
    "boletos": [
        ("id_viaje", "viajes", "id_viaje"),
    ],
    "administrador": [("id_empleado", "empleados", "id_empleado")],
    "accesos": [("id_admin", "administrador", "id_admin")],
    "reportes": [("id_viaje", "viajes", "id_viaje")],
}


DISPLAY_FIELDS = {
    "autobuses": ["numero_unidad", "modelo", "capacidad_total", "placa"],
    "rutas": ["origen", "destino", "distancia_estimada"],
    "viajes": ["id_ruta", "id_autobus", "fecha_salida", "hora_salida", "costo_base", "nombre_cliente", "telefono_cliente", "correo_cliente"],
    "boletos": ["id_viaje", "numero_asiento", "costo_final"],
    "empleados": ["nombre", "usuario"],
    "administrador": ["id_empleado"],
    "accesos": ["id_admin", "permiso_altas", "permiso_bajas", "permiso_modificaciones", "interfaz_accedida"],
    "reportes": ["id_viaje", "descripcion_incidencia", "fecha_reporte"],
}


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for table_data in TABLES.values():
        path = os.path.join(DATA_DIR, table_data["file"])
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8"):
                pass

    seed_empleados_if_needed()
    seed_administrador_if_needed()
    seed_accesos_if_needed()
    seed_autobuses_if_needed()
    seed_rutas_if_needed()
    seed_viajes_if_needed()
    seed_boletos_if_needed()
    seed_reportes_if_needed()


def table_path(table_name):
    return os.path.join(DATA_DIR, TABLES[table_name]["file"])


def get_row(table_name, record_id):
    id_field = TABLES[table_name]["id_field"]
    for row in load_rows(table_name):
        if row.get(id_field) == record_id:
            return row
    return None


def get_display_value(table_name, record_id):
    if not record_id:
        return ""

    row = get_row(table_name, record_id)
    if not row:
        return record_id

    if table_name == "autobuses":
        return f"Unidad {row.get('numero_unidad', '')} - {row.get('modelo', '')}".strip(" -")
    if table_name == "rutas":
        return f"{row.get('origen', '')} -> {row.get('destino', '')}".strip()
    if table_name == "viajes":
        ruta = get_display_value("rutas", row.get("id_ruta", ""))
        autobus = get_display_value("autobuses", row.get("id_autobus", ""))
        fecha = row.get("fecha_salida", "")
        hora = row.get("hora_salida", "")
        disponibles = get_trip_available_seats(row)
        total = get_trip_total_seats(row)
        return f"{ruta} | {autobus} | {fecha} {hora} | {disponibles}/{total} asientos".strip()
    if table_name == "boletos":
        viaje = get_display_value("viajes", row.get("id_viaje", ""))
        asiento = row.get("numero_asiento", "")
        cliente = row.get("nombre_cliente", "")
        return f"{cliente} | {viaje} | Asiento {asiento}".strip()
    if table_name == "empleados":
        return f"{row.get('nombre', '')} ({row.get('usuario', '')})".strip()
    if table_name == "administrador":
        empleado = get_display_value("empleados", row.get("id_empleado", ""))
        return f"Admin: {empleado}".strip()
    if table_name == "accesos":
        admin = get_display_value("administrador", row.get("id_admin", ""))
        return f"{admin} | {row.get('interfaz_accedida', '')}".strip()
    if table_name == "reportes":
        viaje = get_display_value("viajes", row.get("id_viaje", ""))
        return f"{viaje} | {row.get('descripcion_incidencia', '')}".strip()
    return record_id


def get_default_employee():
    empleados = load_rows("empleados")
    if empleados:
        admin = next((row for row in empleados if row.get("usuario", "").strip().lower() == "admin"), None)
        return admin or empleados[0]

    default_employee = {
        "id_empleado": generate_id("id_empleado"),
        "nombre": "Administrador",
        "rol": "Admin",
        "usuario": "admin",
        "contrasena_encriptada": hash_password("admin123"),
    }
    save_rows("empleados", [default_employee])
    return default_employee


def get_default_terminal():
    return get_default_employee()


def seed_empleados_if_needed():
    empleados = load_rows("empleados")
    if empleados:
        return

    seed_rows = [
        {
            "id_empleado": generate_id("id_empleado"),
            "nombre": "Administrador",
            "rol": "Admin",
            "usuario": "admin",
            "contrasena_encriptada": hash_password("admin123"),
        },
        {
            "id_empleado": generate_id("id_empleado"),
            "nombre": "Usuario Basico",
            "rol": "Usuario",
            "usuario": "usuario",
            "contrasena_encriptada": hash_password("usuario123"),
        },
    ]
    save_rows("empleados", seed_rows)


def seed_accesos_if_needed():
    accesos = load_rows("accesos")
    if accesos:
        return

    admins = load_rows("administrador")
    if not admins:
        return

    admin = admins[0]
    seed_rows = [
        {
            "id_acceso": generate_id("id_acceso"),
            "id_admin": admin["id_admin"],
            "permiso_altas": "true",
            "permiso_bajas": "true",
            "permiso_modificaciones": "true",
            "interfaz_accedida": "Admin",
        }
    ]
    save_rows("accesos", seed_rows)


def seed_administrador_if_needed():
    if load_rows("administrador"):
        return

    empleados = load_rows("empleados")
    if not empleados:
        return

    admin = next((row for row in empleados if row.get("usuario", "").strip().lower() == "admin"), empleados[0])
    seed_rows = [
        {
            "id_admin": generate_id("id_admin"),
            "id_empleado": admin["id_empleado"],
        }
    ]
    save_rows("administrador", seed_rows)


def seed_autobuses_if_needed():
    if load_rows("autobuses"):
        return
    save_rows(
        "autobuses",
        [
            {
                "id_autobus": generate_id("id_autobus"),
                "numero_unidad": "A-01",
                "modelo": "Irizar i6",
                "capacidad_total": "40",
                "placa": "ABC-123",
            },
            {
                "id_autobus": generate_id("id_autobus"),
                "numero_unidad": "A-02",
                "modelo": "Volvo 9700",
                "capacidad_total": "45",
                "placa": "XYZ-456",
            },
        ],
    )


def seed_rutas_if_needed():
    if load_rows("rutas"):
        return
    save_rows(
        "rutas",
        [
            {
                "id_ruta": generate_id("id_ruta"),
                "origen": "Monterrey",
                "destino": "Saltillo",
                "distancia_estimada": "85",
            },
            {
                "id_ruta": generate_id("id_ruta"),
                "origen": "Monterrey",
                "destino": "Tampico",
                "distancia_estimada": "500",
            },
        ],
    )


def seed_viajes_if_needed():
    if load_rows("viajes"):
        return
    rutas = load_rows("rutas")
    autobuses = load_rows("autobuses")
    if not rutas or not autobuses:
        return
    save_rows(
        "viajes",
        [
            {
                "id_viaje": generate_id("id_viaje"),
                "id_ruta": rutas[0]["id_ruta"],
                "id_autobus": autobuses[0]["id_autobus"],
                "fecha_salida": "2026-05-10",
                "hora_salida": "08:00",
                "costo_base": "150.00",
                "nombre_cliente": "",
                "telefono_cliente": "",
                "correo_cliente": "",
            },
            {
                "id_viaje": generate_id("id_viaje"),
                "id_ruta": rutas[1]["id_ruta"],
                "id_autobus": autobuses[1]["id_autobus"],
                "fecha_salida": "2026-05-11",
                "hora_salida": "15:30",
                "costo_base": "280.00",
                "nombre_cliente": "",
                "telefono_cliente": "",
                "correo_cliente": "",
            },
        ],
    )


def seed_boletos_if_needed():
    if load_rows("boletos"):
        return
    viajes = load_rows("viajes")
    if not viajes:
        return
    save_rows(
        "boletos",
        [
            {
                "id_boleto": generate_id("id_boleto"),
                "id_viaje": viajes[0]["id_viaje"],
                "numero_asiento": "1",
                "costo_final": viajes[0].get("costo_base", "0"),
            }
        ],
    )


def seed_reportes_if_needed():
    if load_rows("reportes"):
        return
    viajes = load_rows("viajes")
    if not viajes:
        return
    save_rows(
        "reportes",
        [
            {
                "id_reporte": generate_id("id_reporte"),
                "id_viaje": viajes[0]["id_viaje"],
                "descripcion_incidencia": "Sin incidentes",
                "fecha_reporte": datetime.now().strftime("%Y-%m-%d"),
            }
        ],
    )


seed_terminales_if_needed = seed_autobuses_if_needed
seed_reservaciones_if_needed = seed_boletos_if_needed


def get_trip_total_seats(row):
    if not row:
        return 0

    if row.get("id_autobus"):
        autobus = get_row("autobuses", row.get("id_autobus", ""))
        if autobus:
            try:
                return int(float(autobus.get("capacidad_total", "0") or 0))
            except (TypeError, ValueError):
                return 0

    raw_value = row.get("capacidad_total", row.get("cupos_totales", row.get("numero_asientos", "0")))
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return 0


def get_trip_available_seats(row):
    total = get_trip_total_seats(row)
    if total <= 0:
        return 0

    trip_id = row.get("id_viaje", "")
    if not trip_id:
        return total

    booked = sum(1 for boleto in load_rows("boletos") if boleto.get("id_viaje", "") == trip_id)
    return max(0, total - booked)


def set_trip_seats(trip_id, delta):
    trip = get_row("viajes", trip_id)
    if not trip:
        return False

    total = get_trip_total_seats(trip)
    available = get_trip_available_seats(trip)
    if delta < 0 and available + delta < 0:
        return False
    if delta > 0 and available + delta > total:
        return False
    return True


def trip_is_full(trip_row):
    return get_trip_available_seats(trip_row) <= 0


def normalize_trip_row(row):
    normalized = dict(row)
    normalized.setdefault("id_ruta", "")
    normalized.setdefault("id_autobus", "")
    normalized.setdefault("fecha_salida", "")
    normalized.setdefault("hora_salida", "")
    normalized.setdefault("costo_base", "0")
    return normalized


def migrate_legacy_trip_rows():
    return


def apply_trip_capacity_change(trip_id, seats_delta):
    return set_trip_seats(trip_id, seats_delta)


def reserve_trip_seats(trip_id, seats):
    return set_trip_seats(trip_id, -seats)


def release_trip_seats(trip_id, seats):
    return set_trip_seats(trip_id, seats)


def parse_line(line):
    row = {}
    parts = next(csv.reader([line.strip()], skipinitialspace=True), [])
    current_key = None
    for part in parts:
        chunk = part.strip()
        if not chunk:
            continue

        if "=" in chunk:
            key, value = chunk.split("=", 1)
            current_key = key.strip()
            row[current_key] = value.strip()
            continue

        # Soporta valores legados con comas sin comillas (ej. permisos=roles,clientes,...).
        if current_key:
            row[current_key] = f"{row[current_key]},{chunk}"
    return row


def serialize_row(row, fields):
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="")
    writer.writerow([f"{field}={row.get(field, '')}" for field in fields])
    return buffer.getvalue()


def load_rows(table_name, include_deleted=False):
    path = table_path(table_name)
    rows = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            row = parse_line(line)
            if not row:
                continue
            # Excluir registros marcados como borrados (soft delete) a menos que se soliciten
            if not include_deleted and str(row.get("is_deleted", "")).lower() == "true":
                continue
            rows.append(row)
    return rows


def save_rows(table_name, rows):
    base_fields = TABLES[table_name]["fields"]
    # Añadir campos de soft-delete al serializar (si no existen ya)
    extra_fields = [f for f in ("is_deleted", "deleted_at", "deleted_by") if f not in base_fields]
    fields = base_fields + extra_fields
    path = table_path(table_name)
    with open(path, "w", encoding="utf-8") as file:
        for row in rows:
            file.write(serialize_row(row, fields) + "\n")


def generate_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def hash_password(password, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex
    digest = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password, stored_password_hash):
    if not stored_password_hash or "$" not in stored_password_hash:
        return False

    salt, expected_digest = stored_password_hash.split("$", 1)
    current_digest = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
    return current_digest == expected_digest


def choose_table():
    print("\nTablas disponibles:")
    print("1. autobuses")
    print("2. rutas")
    print("3. viajes")
    print("4. boletos")
    print("5. empleados")
    print("6. administrador")
    print("7. accesos")
    print("8. reportes")

    option = input("Seleccione tabla: ").strip()
    mapping = {
        "1": "autobuses",
        "2": "rutas",
        "3": "viajes",
        "4": "boletos",
        "5": "empleados",
        "6": "administrador",
        "7": "accesos",
        "8": "reportes",
    }
    return mapping.get(option)


def validate_number(value, field_name):
    if value == "":
        return True
    try:
        float(value)
    except ValueError:
        print(f"El campo {field_name} debe ser numerico.")
        return False
    return True


def validate_date(value, field_name):
    if value == "":
        return True
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        print(f"El campo {field_name} debe tener formato YYYY-MM-DD.")
        return False
    return True


def id_exists(table_name, id_field, record_id):
    rows = load_rows(table_name)
    return any(row.get(id_field) == record_id for row in rows)


def validate_foreign_keys(table_name, row):
    for field_name, ref_table, ref_field in REFERENCE_MAP.get(table_name, []):
        if not id_exists(ref_table, ref_field, row.get(field_name, "")):
            print(f"No existe el valor indicado para {field_name}.")
            return False

    return True


def validate_unique_username(new_username, current_user_id=None):
    username = new_username.strip().lower()
    if not username:
        print("El usuario no puede estar vacio.")
        return False

    empleados = load_rows("empleados")
    for empleado in empleados:
        existing_username = empleado.get("usuario", "").strip().lower()
        existing_id = empleado.get("id_empleado", "")
        if existing_username == username and existing_id != current_user_id:
            print("Ese usuario ya existe. Elija otro.")
            return False
    return True


def prompt_row(table_name, current_row=None):
    fields = TABLES[table_name]["fields"]
    id_field = TABLES[table_name]["id_field"]

    row = {} if current_row is None else dict(current_row)

    if current_row is None:
        row[id_field] = generate_id(id_field)

    for field in fields:
        if field == id_field:
            continue

        while True:
            label = FIELD_LABELS.get(field, field)
            current_value = row.get(field, "")

            if field == "contrasena_encriptada":
                if current_row is None:
                    plain_password = input("Contrasena: ").strip()
                    if plain_password == "":
                        print("La contrasena no puede estar vacia.")
                        continue
                    value = hash_password(plain_password)
                else:
                    plain_password = input("Contrasena [dejar vacio para mantener]: ").strip()
                    if plain_password == "":
                        value = current_value
                    else:
                        value = hash_password(plain_password)
            else:
                if current_row is None:
                    value = input(f"{label}: ").strip()
                else:
                    value = input(f"{label} [{current_value}]: ").strip()
                    if value == "":
                        value = current_value

            if field in {"telefono", "capacidad_total", "distancia_estimada", "costo_base", "numero_asiento", "costo_final"} and not validate_number(value, field):
                continue
            if field in {"fecha_salida", "fecha_reporte"} and not validate_date(value, field):
                continue

            row[field] = value
            break

    return row


def insert_record():
    table_name = choose_table()
    if not table_name:
        print("Tabla invalida.")
        return

    new_row = prompt_row(table_name)
    if new_row is None:
        return

    if table_name == "empleados" and not validate_unique_username(new_row.get("usuario", "")):
        return

    if table_name == "viajes" and not new_row.get("id_ruta"):
        print("El viaje requiere una ruta.")
        return

    if table_name == "viajes" and not new_row.get("id_autobus"):
        print("El viaje requiere un autobus.")
        return

    if table_name == "boletos":
        trip_id = new_row.get("id_viaje", "")
        seat_number = new_row.get("numero_asiento", "").strip()
        trip = get_row("viajes", trip_id)
        if not trip:
            print("No existe el viaje seleccionado.")
            return
        if not seat_number:
            print("El boleto debe incluir un numero de asiento.")
            return
        if any(b.get("id_viaje", "") == trip_id and b.get("numero_asiento", "") == seat_number for b in load_rows("boletos")):
            print("Ese asiento ya fue asignado para este viaje.")
            return
        available = get_trip_available_seats(trip)
        if available <= 0:
            print("El viaje esta lleno.")
            return
        new_row["costo_final"] = trip.get("costo_base", "0")

    if table_name == "reportes" and not new_row.get("descripcion_incidencia"):
        print("La descripcion del reporte no puede estar vacia.")
        return

    if not validate_foreign_keys(table_name, new_row):
        return

    rows = load_rows(table_name)
    rows.append(new_row)
    save_rows(table_name, rows)

    id_field = TABLES[table_name]["id_field"]
    print(f"Registro agregado en {table_name} con {id_field}: {new_row[id_field]}")


def update_record():
    table_name = choose_table()
    if not table_name:
        print("Tabla invalida.")
        return

    id_field = TABLES[table_name]["id_field"]
    record_id = input(f"Ingrese {id_field} a modificar: ").strip()

    rows = load_rows(table_name)

    for index, row in enumerate(rows):
        if row.get(id_field) == record_id:
            print("Deje vacio para mantener valor actual.")
            original_row = dict(row)
            updated_row = prompt_row(table_name, row)

            if updated_row is None:
                return

            if table_name == "empleados":
                current_user_id = row.get("id_empleado")
                if not validate_unique_username(updated_row.get("usuario", ""), current_user_id):
                    return

            if table_name == "viajes" and not updated_row.get("id_ruta"):
                print("El viaje requiere una ruta.")
                return

            if table_name == "viajes" and not updated_row.get("id_autobus"):
                print("El viaje requiere un autobus.")
                return

            if table_name == "boletos":
                trip_id = updated_row.get("id_viaje", "")
                seat_number = updated_row.get("numero_asiento", "").strip()
                trip = get_row("viajes", trip_id)
                if not trip:
                    print("No existe el viaje seleccionado.")
                    return
                if not seat_number:
                    print("El boleto debe incluir un numero de asiento.")
                    return
                if any(
                    boleto.get("id_boleto", "") != record_id
                    and boleto.get("id_viaje", "") == trip_id
                    and boleto.get("numero_asiento", "") == seat_number
                    for boleto in load_rows("boletos")
                ):
                    print("Ese asiento ya fue asignado para este viaje.")
                    return
                updated_row["costo_final"] = trip.get("costo_base", "0")

            if not validate_foreign_keys(table_name, updated_row):
                return

            rows[index] = updated_row
            save_rows(table_name, rows)
            print("Registro modificado correctamente.")
            return

    print("No se encontro un registro con ese ID.")


def delete_record():
    table_name = choose_table()
    if not table_name:
        print("Tabla invalida.")
        return

    id_field = TABLES[table_name]["id_field"]
    record_id = input(f"Ingrese {id_field} a eliminar: ").strip()

    rows = load_rows(table_name)
    target_row = next((row for row in rows if row.get(id_field) == record_id), None)
    filtered_rows = [row for row in rows if row.get(id_field) != record_id]

    if len(filtered_rows) == len(rows):
        print("No se encontro un registro con ese ID.")
        return

    save_rows(table_name, filtered_rows)
    print("Registro eliminado correctamente.")


def print_table(table_name):
    rows = load_rows(table_name)
    fields = TABLES[table_name]["fields"]

    if not rows:
        print(f"No hay registros en {table_name}.")
        return

    widths = {field: max(len(field), *(len(row.get(field, "")) for row in rows)) for field in fields}

    header = " | ".join(field.ljust(widths[field]) for field in fields)
    separator = "-+-".join("-" * widths[field] for field in fields)

    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(row.get(field, "").ljust(widths[field]) for field in fields))


def view_records():
    table_name = choose_table()
    if not table_name:
        print("Tabla invalida.")
        return
    print_table(table_name)


def seed_viajes():
    viajes = load_rows("viajes")
    if viajes:
        print("La tabla viajes ya tiene datos. Seeder omitido.")
        return

    rutas = load_rows("rutas")
    autobuses = load_rows("autobuses")

    if not rutas or not autobuses:
        print("Cargue rutas y autobuses para generar viajes de ejemplo.")
        return

    seed_rows = [
        {
            "id_viaje": generate_id("id_viaje"),
            "id_ruta": rutas[0]["id_ruta"],
            "id_autobus": autobuses[0]["id_autobus"],
            "fecha_salida": "2026-05-10",
            "hora_salida": "08:00",
            "costo_base": "150.00",
        },
        {
            "id_viaje": generate_id("id_viaje"),
            "id_ruta": rutas[1 % len(rutas)]["id_ruta"],
            "id_autobus": autobuses[1 % len(autobuses)]["id_autobus"],
            "fecha_salida": "2026-05-11",
            "hora_salida": "15:30",
            "costo_base": "280.00",
        },
    ]

    save_rows("viajes", seed_rows)
    print("Seeder de viajes cargado correctamente.")


def main():
    ensure_data_files()

    while True:
        print("\nSeleccione una opcion:")
        print("1. Insertar registro")
        print("2. Modificar registro")
        print("3. Eliminar registro")
        print("4. Ver tabla")
        print("5. Cargar seeders basicos")
        print("0. Salir")

        option = input("Opcion: ").strip()

        if option == "1":
            insert_record()
        elif option == "2":
            update_record()
        elif option == "3":
            delete_record()
        elif option == "4":
            view_records()
        elif option == "5":
            seed_empleados_if_needed()
            seed_administrador_if_needed()
            seed_accesos_if_needed()
            seed_autobuses_if_needed()
            seed_rutas_if_needed()
            seed_viajes_if_needed()
            seed_boletos_if_needed()
            seed_reportes_if_needed()
        elif option == "0":
            print("Saliendo...")
            break
        else:
            print("Opcion invalida.")


if __name__ == "__main__":
    main()
