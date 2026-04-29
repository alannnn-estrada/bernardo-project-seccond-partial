from datetime import datetime
import hashlib
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_db")

TABLES = {
    "roles": {
        "file": "roles.txt",
        "id_field": "id_rol",
        "fields": ["id_rol", "nombre_rol", "permisos"],
    },
    "clientes": {
        "file": "clientes.txt",
        "id_field": "id_cliente",
        "fields": ["id_cliente", "nombre", "apellido", "correo", "telefono"],
    },
    "terminales": {
        "file": "terminales.txt",
        "id_field": "id_terminal",
        "fields": ["id_terminal", "nombre_terminal", "direccion", "codigo_postal"],
    },
    "lugares": {
        "file": "lugares.txt",
        "id_field": "id_lugar",
        "fields": ["id_lugar", "nombre_lugar", "codigo_postal"],
    },
    "viajes": {
        "file": "viajes.txt",
        "id_field": "id_viaje",
        "fields": [
            "id_viaje",
            "id_lugar_origen",
            "id_lugar_destino",
            "fecha",
            "km_recorrer",
            "tiempo_estimado_llegada",
            "cupos_totales",
            "cupos_disponibles",
            "horario",
            "costo_asiento",
        ],
    },
    "usuarios": {
        "file": "usuarios.txt",
        "id_field": "id_usuario",
        "fields": [
            "id_usuario",
            "username",
            "password_hash",
            "id_rol",
            "id_terminal",
            "fecha_contratacion",
            "nombre",
            "apellido",
            "direccion",
            "correo",
            "numero",
            "curp",
            "rfc",
            "sueldo",
        ],
    },
    "reservaciones": {
        "file": "reservaciones.txt",
        "id_field": "id_reservacion",
        "fields": [
            "id_reservacion",
            "id_cliente",
            "id_viaje",
            "id_usuario",
            "id_terminal",
            "fecha_reservacion",
            "asientos",
            "estado",
            "costo_total",
        ],
    },
}

FIELD_LABELS = {
    "id_cliente": "ID cliente",
    "id_lugar": "ID lugar",
    "id_terminal": "ID terminal",
    "id_viaje": "ID viaje",
    "id_reservacion": "ID reservacion",
    "id_usuario": "ID usuario",
    "username": "Username",
    "password_hash": "Contrasena",
    "nombre": "Nombre",
    "apellido": "Apellido",
    "correo": "Correo",
    "telefono": "Telefono",
    "nombre_lugar": "Nombre del lugar",
    "codigo_postal": "Codigo postal",
    "id_lugar_origen": "ID lugar origen",
    "id_lugar_destino": "ID lugar destino",
    "fecha": "Fecha (YYYY-MM-DD)",
    "km_recorrer": "Km a recorrer",
    "tiempo_estimado_llegada": "Tiempo estimado de llegada",
    "cupos_totales": "Cupos totales",
    "cupos_disponibles": "Cupos disponibles",
    "horario": "Horario",
    "fecha_contratacion": "Fecha de contratacion (YYYY-MM-DD)",
    "direccion": "Direccion",
    "numero": "Numero",
    "curp": "CURP",
    "rfc": "RFC",
    "sueldo": "Sueldo",
    "id_rol": "ID Rol",
    "nombre_terminal": "Nombre de la terminal",
    "estado": "Estado",
    "fecha_reservacion": "Fecha de reservacion (YYYY-MM-DD)",
    "nombre_rol": "Nombre del rol",
    "permisos": "Permisos",
    "costo_asiento": "Costo por Asiento",
    "costo_total": "Costo Total",
}


REFERENCE_MAP = {
    "viajes": [
        ("id_lugar_origen", "lugares", "id_lugar"),
        ("id_lugar_destino", "lugares", "id_lugar"),
    ],
    "usuarios": [("id_terminal", "terminales", "id_terminal"), ("id_rol", "roles", "id_rol")],
    "reservaciones": [
        ("id_cliente", "clientes", "id_cliente"),
        ("id_viaje", "viajes", "id_viaje"),
        ("id_usuario", "usuarios", "id_usuario"),
        ("id_terminal", "terminales", "id_terminal"),
    ],
}


DISPLAY_FIELDS = {
    "roles": ["nombre_rol", "permisos"],
    "clientes": ["nombre", "apellido", "correo", "telefono"],
    "terminales": ["nombre_terminal", "direccion", "codigo_postal"],
    "lugares": ["nombre_lugar", "codigo_postal"],
    "viajes": ["id_lugar_origen", "id_lugar_destino", "fecha", "horario", "cupos_disponibles", "costo_asiento"],
    "usuarios": ["username", "id_rol", "id_terminal", "nombre", "apellido", "correo"],
    "reservaciones": ["id_cliente", "id_viaje", "id_usuario", "id_terminal", "fecha_reservacion", "estado", "costo_total"],
}


def ensure_data_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    for table_data in TABLES.values():
        path = os.path.join(DATA_DIR, table_data["file"])
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8"):
                pass

    seed_roles_if_needed()
    ensure_default_terminal_exists()
    ensure_users_have_terminal()
    migrate_legacy_trip_rows()


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

    if table_name == "roles":
        return row.get("nombre_rol", record_id)
    if table_name == "clientes":
        return f"{row.get('nombre', '')} {row.get('apellido', '')}".strip()
    if table_name == "terminales":
        return row.get("nombre_terminal", record_id)
    if table_name == "lugares":
        return row.get("nombre_lugar", record_id)
    if table_name == "viajes":
        origen = get_display_value("lugares", row.get("id_lugar_origen", ""))
        destino = get_display_value("lugares", row.get("id_lugar_destino", ""))
        fecha = row.get("fecha", "")
        horario = row.get("horario", "")
        disponibles = get_trip_available_seats(row)
        total = get_trip_total_seats(row)
        estado = "LLENO" if disponibles <= 0 else f"Disponibles {disponibles}/{total}"
        return f"{origen} -> {destino} | {fecha} {horario} | {estado}".strip()
    if table_name == "usuarios":
        nombre = f"{row.get('nombre', '')} {row.get('apellido', '')}".strip()
        terminal = get_display_value("terminales", row.get("id_terminal", ""))
        return f"{nombre} ({terminal})".strip()
    if table_name == "reservaciones":
        cliente = get_display_value("clientes", row.get("id_cliente", ""))
        viaje = get_display_value("viajes", row.get("id_viaje", ""))
        estado = row.get("estado", "")
        return f"{cliente} | {viaje} | {estado}".strip()
    return record_id


def get_default_terminal():
    terminales = load_rows("terminales")
    if terminales:
        return terminales[0]

    default_terminal = {
        "id_terminal": generate_id("id_terminal"),
        "nombre_terminal": "Terminal Central",
        "direccion": "Sin direccion",
        "codigo_postal": "00000",
    }
    save_rows("terminales", [default_terminal])
    return default_terminal


def ensure_default_terminal_exists():
    get_default_terminal()


def ensure_users_have_terminal():
    default_terminal = get_default_terminal()
    users = load_rows("usuarios")
    changed = False

    for user in users:
        if not user.get("id_terminal"):
            user["id_terminal"] = default_terminal["id_terminal"]
            changed = True

    if changed:
        save_rows("usuarios", users)


def seed_roles_if_needed():
    roles = load_rows("roles")
    if roles:
        return

    seed_rows = [
        {
            "id_rol": "rol_admin",
            "nombre_rol": "Administrador",
            "permisos": "roles,clientes,terminales,lugares,viajes,usuarios,reservaciones",
        },
        {
            "id_rol": "rol_recep",
            "nombre_rol": "Recepcionista",
            "permisos": "clientes,reservaciones,viajes,lugares",
        },
        {
            "id_rol": "rol_coord",
            "nombre_rol": "Coordinador",
            "permisos": "viajes,lugares,terminales",
        },
    ]
    save_rows("roles", seed_rows)


def seed_terminales_if_needed():
    terminales = load_rows("terminales")
    if terminales:
        return

    seed_rows = [
        {
            "id_terminal": generate_id("id_terminal"),
            "nombre_terminal": "Terminal Norte",
            "direccion": "Av. Principal 100",
            "codigo_postal": "64000",
        },
        {
            "id_terminal": generate_id("id_terminal"),
            "nombre_terminal": "Terminal Sur",
            "direccion": "Av. Central 200",
            "codigo_postal": "64100",
        },
    ]
    save_rows("terminales", seed_rows)
    ensure_users_have_terminal()


def seed_reservaciones_if_needed():
    if load_rows("reservaciones"):
        return

    clientes = load_rows("clientes")
    viajes = load_rows("viajes")
    usuarios = load_rows("usuarios")
    terminales = load_rows("terminales")

    if not clientes or not viajes or not usuarios or not terminales:
        return

    default_terminal_id = terminales[0]["id_terminal"]
    seed_rows = [
        {
            "id_reservacion": generate_id("id_reservacion"),
            "id_cliente": clientes[0]["id_cliente"],
            "id_viaje": viajes[0]["id_viaje"],
            "id_usuario": usuarios[0]["id_usuario"],
            "id_terminal": default_terminal_id,
            "fecha_reservacion": datetime.now().strftime("%Y-%m-%d"),
            "asientos": "1",
            "estado": "confirmada",
        }
    ]
    save_rows("reservaciones", seed_rows)


def get_trip_total_seats(row):
    raw_value = row.get("cupos_totales", row.get("numero_asientos", "0"))
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return 0


def get_trip_available_seats(row):
    raw_value = row.get("cupos_disponibles", "")
    if raw_value == "":
        return get_trip_total_seats(row)
    try:
        return int(float(raw_value))
    except (TypeError, ValueError):
        return 0


def set_trip_seats(trip_id, delta):
    trips = load_rows("viajes")
    for trip in trips:
        if trip.get("id_viaje") == trip_id:
            available = get_trip_available_seats(trip)
            total = get_trip_total_seats(trip)
            new_available = available + delta
            if new_available < 0 or new_available > total:
                return False
            trip["cupos_totales"] = str(total)
            trip["cupos_disponibles"] = str(new_available)
            save_rows("viajes", trips)
            return True
    return False


def trip_is_full(trip_row):
    return get_trip_available_seats(trip_row) <= 0


def normalize_trip_row(row):
    normalized = dict(row)
    total = get_trip_total_seats(normalized)
    available = get_trip_available_seats(normalized)
    if total <= 0:
        total = available if available > 0 else 0
    if available > total:
        available = total
    normalized["cupos_totales"] = str(total)
    normalized["cupos_disponibles"] = str(available)
    normalized.pop("id_cliente", None)
    normalized.pop("numero_asientos", None)
    return normalized


def migrate_legacy_trip_rows():
    trips = load_rows("viajes")
    if not trips:
        return

    migrated = []
    changed = False
    for trip in trips:
        normalized = normalize_trip_row(trip)
        if normalized != trip:
            changed = True
        migrated.append(normalized)

    if changed:
        save_rows("viajes", migrated)


def apply_trip_capacity_change(trip_id, seats_delta):
    return set_trip_seats(trip_id, seats_delta)


def reserve_trip_seats(trip_id, seats):
    return set_trip_seats(trip_id, -seats)


def release_trip_seats(trip_id, seats):
    return set_trip_seats(trip_id, seats)


def parse_line(line):
    row = {}
    parts = [part.strip() for part in line.strip().split(",") if part.strip()]
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            row[key.strip()] = value.strip()
    return row


def serialize_row(row, fields):
    return ",".join(f"{field}={row.get(field, '')}" for field in fields)


def load_rows(table_name):
    path = table_path(table_name)
    rows = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            row = parse_line(line)
            if row:
                rows.append(row)
    return rows


def save_rows(table_name, rows):
    fields = TABLES[table_name]["fields"]
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
    print("1. clientes")
    print("2. terminales")
    print("3. lugares")
    print("4. viajes")
    print("5. usuarios")
    print("6. reservaciones")
    print("7. roles")

    option = input("Seleccione tabla: ").strip()
    mapping = {
        "1": "clientes",
        "2": "terminales",
        "3": "lugares",
        "4": "viajes",
        "5": "usuarios",
        "6": "reservaciones",
        "7": "roles",
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
        print("El username no puede estar vacio.")
        return False

    users = load_rows("usuarios")
    for user in users:
        existing_username = user.get("username", "").strip().lower()
        existing_id = user.get("id_usuario", "")
        if existing_username == username and existing_id != current_user_id:
            print("Ese username ya existe. Elija otro.")
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
        if table_name == "viajes" and field == "cupos_disponibles":
            continue

        while True:
            label = FIELD_LABELS.get(field, field)
            current_value = row.get(field, "")

            if field == "password_hash":
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

            if field in {"km_recorrer", "cupos_totales", "cupos_disponibles", "sueldo", "costo_asiento", "costo_total"} and not validate_number(value, field):
                continue
            if field in {"fecha", "fecha_contratacion"} and not validate_date(value, field):
                continue

            row[field] = value
            break

    if table_name == "viajes":
        if current_row is None:
            row["cupos_disponibles"] = row.get("cupos_totales", "0")
        else:
            old_total = get_trip_total_seats(current_row)
            old_available = get_trip_available_seats(current_row)
            occupied = max(0, old_total - old_available)
            new_total = get_trip_total_seats(row)
            if new_total < occupied:
                print("Los cupos totales no pueden ser menores a las reservaciones ya hechas.")
                return None
            row["cupos_disponibles"] = str(new_total - occupied)

    return row


def insert_record():
    table_name = choose_table()
    if not table_name:
        print("Tabla invalida.")
        return

    new_row = prompt_row(table_name)
    if new_row is None:
        return

    if table_name == "usuarios" and not validate_unique_username(new_row.get("username", "")):
        return

    if table_name == "viajes" and int(float(new_row.get("cupos_totales", "0") or 0)) <= 0:
        print("Los cupos totales deben ser mayores a cero.")
        return

    if table_name == "reservaciones":
        trip_id = new_row.get("id_viaje", "")
        requested_seats = int(float(new_row.get("asientos", "0") or 0))
        trip = get_row("viajes", trip_id)
        if not trip:
            print("No existe el viaje seleccionado.")
            return
        available = get_trip_available_seats(trip)
        if requested_seats <= 0:
            print("La reservacion debe incluir al menos 1 asiento.")
            return
        if requested_seats > available:
            print("El viaje esta lleno o no cuenta con suficientes cupos.")
            return

    if table_name == "viajes":
        new_row = normalize_trip_row(new_row)

    if not validate_foreign_keys(table_name, new_row):
        return

    rows = load_rows(table_name)
    rows.append(new_row)
    save_rows(table_name, rows)

    if table_name == "reservaciones":
        if not reserve_trip_seats(new_row["id_viaje"], int(float(new_row.get("asientos", "0") or 0))):
            print("No se pudo actualizar la disponibilidad del viaje.")
            rows = [row for row in rows if row.get("id_reservacion") != new_row.get("id_reservacion")]
            save_rows(table_name, rows)
            return

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

            if table_name == "usuarios":
                current_user_id = row.get("id_usuario")
                if not validate_unique_username(updated_row.get("username", ""), current_user_id):
                    return

            if table_name == "viajes" and int(float(updated_row.get("cupos_totales", "0") or 0)) <= 0:
                print("Los cupos totales deben ser mayores a cero.")
                return

            if table_name == "viajes":
                updated_row = normalize_trip_row(updated_row)

            if table_name == "reservaciones":
                old_trip_id = original_row.get("id_viaje", "")
                new_trip_id = updated_row.get("id_viaje", "")
                old_seats = int(float(original_row.get("asientos", "0") or 0))
                new_seats = int(float(updated_row.get("asientos", "0") or 0))

                if new_seats <= 0:
                    print("La reservacion debe incluir al menos 1 asiento.")
                    return

                if old_trip_id != new_trip_id:
                    if not release_trip_seats(old_trip_id, old_seats):
                        print("No se pudo liberar cupos de la reservacion anterior.")
                        return
                    if not reserve_trip_seats(new_trip_id, new_seats):
                        release_trip_seats(old_trip_id, old_seats)
                        print("El nuevo viaje no tiene cupos suficientes.")
                        return
                else:
                    diff = new_seats - old_seats
                    if diff > 0:
                        if not reserve_trip_seats(new_trip_id, diff):
                            print("El viaje no tiene cupos suficientes.")
                            return
                    elif diff < 0:
                        if not release_trip_seats(new_trip_id, -diff):
                            print("No se pudo devolver cupos al viaje.")
                            return

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

    if table_name == "reservaciones" and target_row:
        seats = int(float(target_row.get("asientos", "0") or 0))
        if not release_trip_seats(target_row.get("id_viaje", ""), seats):
            print("No se pudieron liberar los cupos del viaje.")
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

    lugares = load_rows("lugares")

    if len(lugares) < 2:
        print("Cargue al menos dos lugares para generar viajes de ejemplo.")
        return

    origen_id = lugares[0]["id_lugar"]
    destino_id = lugares[1]["id_lugar"]

    seed_rows = [
        {
            "id_viaje": generate_id("id_viaje"),
            "id_lugar_origen": origen_id,
            "id_lugar_destino": destino_id,
            "fecha": "2026-05-01",
            "km_recorrer": "220",
            "tiempo_estimado_llegada": "3h 20m",
            "cupos_totales": "40",
            "cupos_disponibles": "40",
            "horario": "08:00",
        },
        {
            "id_viaje": generate_id("id_viaje"),
            "id_lugar_origen": destino_id,
            "id_lugar_destino": origen_id,
            "fecha": "2026-05-02",
            "km_recorrer": "220",
            "tiempo_estimado_llegada": "3h 35m",
            "cupos_totales": "40",
            "cupos_disponibles": "40",
            "horario": "15:30",
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
        print("5. Cargar seeders de viajes")
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
            seed_viajes()
        elif option == "0":
            print("Saliendo...")
            break
        else:
            print("Opcion invalida.")


if __name__ == "__main__":
    main()
