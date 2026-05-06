# Proyecto Autobuses - DB TXT + PySide6 GUI

Sistema básico de reservación de autobuses con base de datos en archivos TXT e interfaz gráfica en PySide6.

### Descripción

Este proyecto implementa una base de datos simple conectada a archivos .txt (similar a DB_Py) con:
- Interface gráfica básica basada en PySide6 (Qt)
- Login para separar vista de usuario y vista de administrador
- Gestión de clientes, autobuses, rutas, viajes, boletos, empleados, accesos y reportes
- Generación de boleto y reporte básico

## Archivos Principales

### Capa de Datos
- **insert.py**: CRUD operations, validaciones, seeders y lógica del esquema básico
- **open.py**: Visualizador CLI de todas las tablas en formato columna
- **data_db/**: Carpeta con archivos .txt de la base de datos

### Interface Gráfica (PySide6)
- **gui_app.py**: Ventana principal (QMainWindow), login y orquestación de paneles
- **ui_components.py**: Componentes reutilizables (SearchSelectDialog, RecordDialog, TablePanel)
- **ui_config.py**: Configuración de formularios, validadores y helpers
- **styles.qss**: Estilos personalizados (tema profesional con colores coordinados)

### Documentación
- **ER_DIAGRAM.md**: Documentación detallada del modelo Entity-Relationship
- **ER_DIAGRAM.mmd**: Diagrama Mermaid del modelo relacional

### Modelos de Datos

### Tablas Principales

```
CLIENTES
  - id_cliente (PK)
  - nombre_completo
  - telefono, email

AUTOBUSES
  - id_autobus (PK)
  - numero_unidad, modelo
  - capacidad_total, placa

RUTAS
  - id_ruta (PK)
  - origen, destino
  - distancia_estimada

VIAJES
  - id_viaje (PK)
  - id_ruta (FK), id_autobus (FK)
  - fecha_salida, hora_salida
  - costo_base

BOLETOS
  - id_boleto (PK)
  - id_viaje (FK), id_cliente (FK)
  - numero_asiento, costo_final

EMPLEADOS
  - id_empleado (PK)
  - nombre, rol, usuario
  - contrasena_encriptada

ACCESOS
  - id_acceso (PK)
  - id_empleado (FK)
  - permiso_altas, permiso_bajas, permiso_modificaciones
  - interfaz_accedida (Usuario|Admin)

REPORTES
  - id_reporte (PK)
  - id_viaje (FK)
  - descripcion_incidencia, fecha_reporte
```

### Relaciones

- **1:N CLIENTES → BOLETOS** (un cliente puede tener múltiples boletos)
- **1:N AUTOBUSES → VIAJES** (un autobús puede participar en múltiples viajes)
- **1:N RUTAS → VIAJES** (una ruta puede tener múltiples viajes)
- **1:N VIAJES → BOLETOS** (un viaje puede tener múltiples boletos)
- **1:N EMPLEADOS → ACCESOS** (un empleado tiene su acceso de sesión)
- **1:N VIAJES → REPORTES** (un viaje puede tener múltiples reportes)

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
- ✅ Vista de administrador y vista básica de usuario
- ✅ Búsqueda y selección de registros relacionados
- ✅ Diálogos para crear/editar clientes, autobuses, rutas, viajes, boletos, empleados, accesos y reportes
- ✅ Validación de datos en tiempo real
- ✅ Validación de campos numéricos para evitar letras en entradas de número
- ✅ Generación de boleto y reporte básico
- ✅ Temas personalizados (colores corporativos, espaciado, fuentes)
- ✅ Encriptación de contraseñas

### Sistema de Cupos
- Cada viaje usa la capacidad total del autobús asignado
- Cada boleto ocupa un asiento único dentro del viaje
- No permite vender el mismo asiento dos veces en el mismo viaje
- No permite eliminar un viaje con boletos o reportes relacionados

### Autenticación
- Usuario y contraseña encriptados con SHA-256
- Salt único generado con UUID
- Accesos separados por interfaz Usuario/Admin
- Usuario admin creado automáticamente (admin/admin123)

### Auto-Generación
- **Usuarios**: Generados automáticamente a partir de nombre + rol
- **IDs**: Formato `id_tabla_<uuid>` único para cada registro
- **Fechas**: Fechas del sistema asignadas automáticamente

## Notas de Implementación

### Persistencia de Datos
- Los datos se guardan en archivos .txt en formato `key1=value1,key2=value2,...`
- Carga/Guarda completa en memoria (toda la tabla se carga y guarda como unidad)
- IDs únicos usando UUID v4 con prefijo de tabla

### Validaciones
- Foreign keys verificadas antes de guardar
- Números validados como números
- Fechas validadas en formato YYYY-MM-DD
- No se permiten letras en entradas numéricas
- Usuario único en tabla empleados

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
    ├── reservaciones.txt
    └── roles.txt
```

## Ejemplos de Uso

### Crear una Reservación
1. Ir a pestaña "Boletos"
2. Click "Nuevo"
3. Buscar cliente y viaje
4. Elegir número de asiento
5. Guardar para generar el boleto

### Cargar Datos Demo
1. Click botón "Cargar Demos" en el encabezado del administrador
2. Se crean clientes, autobuses, rutas, viajes, boletos y reportes de ejemplo

## Próximas Mejoras Posibles

- Reportes PDF/Excel de reservaciones
- Gráficos de ocupación de viajes
- Export/Import de datos
- Caché de búsquedas frecuentes
- Histórico de cambios
- Respaldo automático de datos
- API REST para integración externa

