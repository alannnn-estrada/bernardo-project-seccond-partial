import os

from insert import TABLES, ensure_data_files, load_rows

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_db")


def parse_line(line):
    row = {}
    parts = [part.strip() for part in line.strip().split(",") if part.strip()]
    for part in parts:
        if "=" in part:
            key, value = part.split("=", 1)
            row[key.strip()] = value.strip()
    return row


def load_rows(path):
    rows = []
    columns = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            row = parse_line(line)
            if not row:
                continue
            for key in row.keys():
                if key not in columns:
                    columns.append(key)
            rows.append(row)

    return rows, columns


def print_table(table_name, rows, columns):
    print(f"\nTabla: {table_name}")

    if not rows:
        print("No hay registros.")
        return

    widths = {column: max(len(column), *(len(row.get(column, "")) for row in rows)) for column in columns}
    header = " | ".join(column.ljust(widths[column]) for column in columns)
    separator = "-+-".join("-" * widths[column] for column in columns)

    print(header)
    print(separator)
    for row in rows:
        print(" | ".join(row.get(column, "").ljust(widths[column]) for column in columns))


def main():
    ensure_data_files()

    for table_name, table_data in TABLES.items():
        path = os.path.join(DATA_DIR, table_data["file"])
        if not os.path.exists(path):
            print(f"\nTabla: {table_name}")
            print(f"Archivo no encontrado: {path}")
            continue

        rows, columns = load_rows(path)
        print_table(table_name, rows, columns)


if __name__ == "__main__":
    main()
