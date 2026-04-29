# Proyecto Agencia Viajes - DB TXT + PySide6 GUI

Sistema completo de gestión para una agencia de viajes con base de datos en archivos TXT y interfaz gráfica moderna usando PySide6.

## Descripción

Este proyecto implementa una base de datos simple conectada a archivos .txt (similar a DB_Py) con:
- Interface gráfica moderna basada en PySide6 (Qt)
- Sistema de autenticación con contraseñas encriptadas (SHA-256 + salt)
- Gestión de reservaciones con sistema de cupos
- Temas personalizados con QSS (Qt Style Sheets)

## Archivos Principales

### Capa de Datos
- **insert.py**: CRUD operations, validaciones, seeders y gestión de cupos
- **open.py**: Visualizador CLI de todas las tablas en formato columna
- **data_db/**: Carpeta con 6 archivos .txt (base de datos)

### Interface Gráfica (PySide6)
- **gui_app.py**: Ventana principal (QMainWindow), login y orquestación de paneles
- **ui_components.py**: Componentes reutilizables (SearchSelectDialog, RecordDialog, TablePanel)
- **ui_config.py**: Configuración de formularios, validadores y helpers
- **styles.qss**: Estilos personalizados (tema profesional con colores coordinados)

### Documentación
- **ER_DIAGRAM.md**: Documentación detallada del modelo Entity-Relationship
- **ER_DIAGRAM.mmd**: Diagrama Mermaid del modelo relacional

## Modelos de Datos

### Tablas Principales

```
CLIENTES
  - id_cliente (PK)
  - nombre, apellido
  - correo, telefono

USUARIOS
  - id_usuario (PK)
  - username (UNIQUE), password_hash
  - id_terminal (FK)
  - fecha_contratacion
  - nombre, apellido, direccion, correo, numero, rfc, sueldo

TERMINALES
  - id_terminal (PK)
  - nombre_terminal
  - direccion, codigo_postal

LUGARES
  - id_lugar (PK)
  - nombre_lugar
  - codigo_postal

VIAJES
  - id_viaje (PK)
  - id_lugar_origen (FK), id_lugar_destino (FK)
  - fecha, horario
  - km_recorrer, tiempo_estimado_llegada
  - cupos_totales, cupos_disponibles

RESERVACIONES
  - id_reservacion (PK)
  - id_cliente (FK), id_viaje (FK)
  - id_usuario (FK), id_terminal (FK)
  - fecha_reservacion, asientos
  - estado (pendiente|confirmada|cancelada)
```

### Relaciones

- **1:N CLIENTES → RESERVACIONES** (un cliente puede tener múltiples reservaciones)
- **1:N USUARIOS → RESERVACIONES** (un usuario registra múltiples reservaciones)
- **1:N TERMINALES → USUARIOS** (una terminal tiene múltiples usuarios)
- **1:N TERMINALES → RESERVACIONES** (una terminal registra múltiples reservaciones)
- **1:N VIAJES → RESERVACIONES** (un viaje tiene múltiples reservaciones)
- **1:N LUGARES → VIAJES** (un lugar es origen/destino de múltiples viajes)

## Instalación y Ejecución

### Requisitos
- Python 3.10+
- PySide6

### Setup

```bash
# Crear ambiente virtual (si no existe)
python -m venv .venv
source .venv/Scripts/activate  # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install PySide6
```

### Ejecución

```bash
# Interfaz gráfica PySide6 (RECOMENDADO)
python gui_app.py

# CLI para CRUD
python insert.py

# Visualizador de datos
python open.py
```

## Características

### GUI PySide6
- ✅ Inicio de sesión con validación de credenciales
- ✅ 6 pestañas para CRUD de cada tabla
- ✅ Búsqueda y selección de registros relacionados
- ✅ Diálogos para crear/editar registros
- ✅ Validación de datos en tiempo real
- ✅ Gestión automática de cupos en viajes
- ✅ Temas personalizados (colores corporativos, espaciado, fuentes)
- ✅ Generación automática de usernames
- ✅ Encriptación de contraseñas

### Sistema de Cupos
- Cada viaje tiene `cupos_totales` y `cupos_disponibles`
- Al crear una reservación, se descuentan automáticamente los cupos
- Al eliminar una reservación, se devuelven los cupos
- No permite reservar si hay cupos insuficientes
- No permite eliminar un viaje si tiene reservaciones activas

### Autenticación
- Username y contraseña encriptados con SHA-256
- Salt único generado con UUID
- Usuario admin creado automáticamente (admin/admin123)
- Sesión mantiene información del usuario actual

### Auto-Generación
- **Usernames**: Generados automáticamente a partir de nombre + apellido
- **IDs**: Formato `id_tabla_<uuid>` único para cada registro
- **Fechas**: Fechas del sistema asignadas automáticamente
- **Terminal del Usuario**: Asignada automáticamente a nuevas reservaciones

## Notas de Implementación

### Persistencia de Datos
- Los datos se guardan en archivos .txt en formato `key1=value1,key2=value2,...`
- Carga/Guarda completa en memoria (toda la tabla se carga y guarda como unidad)
- IDs únicos usando UUID v4 con prefijo de tabla

### Validaciones
- Foreign keys verificadas antes de guardar
- Números validados como números
- Fechas validadas en formato YYYY-MM-DD
- Cupos validados antes de crear reservaciones
- Username único en tabla usuarios

### Estilos QSS
El archivo `styles.qss` define:
- Colores corporativos (#1976d2 primario, #4caf50 éxito, etc.)
- Bordes y esquinas redondeadas
- Espaciado consistente
- Hovers y estados activos

## Estructura del Proyecto

```
Proyecto_Agencia_Viajes/
├── gui_app.py              # Aplicación principal PySide6
├── ui_components.py        # Componentes (diálogos, tablas, búsqueda)
├── ui_config.py            # Configuración de formularios
├── insert.py               # Capa de datos TXT
├── open.py                 # Visualizador CLI
├── styles.qss              # Tema personalizado Qt
├── ER_DIAGRAM.md           # Documentación ER detallada
├── ER_DIAGRAM.mmd          # Diagrama Mermaid
├── README.md               # Este archivo
└── data_db/
    ├── clientes.txt
    ├── usuarios.txt
    ├── terminales.txt
    ├── lugares.txt
    ├── viajes.txt
    └── reservaciones.txt
```

## Ejemplos de Uso

### Crear una Reservación
1. Ir a pestaña "Reservaciones"
2. Click "Nuevo"
3. Buscar cliente (búsqueda con filtro)
4. Buscar viaje (con validación de cupos)
5. Sistema asigna automáticamente: usuario actual, terminal, fecha
6. Guardar (se descuentan cupos del viaje)

### Crear un Usuario
1. Ir a pestaña "Usuarios"
2. Click "Nuevo"
3. Ingresar nombre y apellido
4. Sistema genera automáticamente el username
5. Ingresar contraseña (se guarda hasheada)
6. Guardar

### Cargar Datos Demo
1. Click botón "Cargar Demos" en header
2. Se crean: terminales, viajes, reservaciones de ejemplo

## Próximas Mejoras Posibles

- Reportes PDF/Excel de reservaciones
- Gráficos de ocupación de viajes
- Export/Import de datos
- Caché de búsquedas frecuentes
- Histórico de cambios
- Respaldo automático de datos
- API REST para integración externa

