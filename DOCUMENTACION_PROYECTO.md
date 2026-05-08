# Proyecto: Agencia de Viajes con Interfaz Grafica y Archivos de Texto

## Portada

**Institucion:** TESI
**Asignatura:** Programacion
**Proyecto:** Mini proyecto de agencia de viajes con entorno grafico
**Grupo:** 201-2
**Fecha:** Mayo de 2026

---

## Introduccion

El presente proyecto consiste en el desarrollo de un sistema grafico para una agencia de viajes. Su objetivo principal es administrar registros relacionados con clientes, usuarios, roles, terminales, lugares, viajes y reservaciones, utilizando archivos de texto como medio de almacenamiento.

La aplicacion simula el funcionamiento basico de una base de datos mediante tablas representadas por archivos `.txt`. Cada archivo almacena registros con campos definidos, identificadores unicos y relaciones entre entidades. Ademas, se incluye una interfaz grafica desarrollada con PySide6 para facilitar las operaciones de alta, consulta, modificacion y baja de informacion.

El sistema tambien contempla privilegios de usuario, control de cupos disponibles en los viajes, calculo del costo total de una reservacion y validacion de relaciones entre tablas. Con esto se busca representar de forma practica la logica de una base de datos relacional, aunque la persistencia se realice mediante archivos de texto.

---

## Desarrollo

### Descripcion general del sistema

La aplicacion permite gestionar la informacion principal de una agencia de viajes. Al iniciar, el usuario debe autenticarse con nombre de usuario y contrasena. Una vez dentro, el sistema muestra un panel grafico con las tablas permitidas segun el rol del usuario.

El menu principal cumple con las operaciones solicitadas para el proyecto:

- **Altas:** permite registrar nuevos clientes, viajes, usuarios, lugares, terminales, roles y reservaciones.
- **Consultas:** muestra los registros almacenados en tablas visuales.
- **Modificaciones:** permite editar registros existentes respetando sus identificadores.
- **Bajas:** permite eliminar registros, aplicando validaciones para no dejar datos inconsistentes.
- **Salida:** permite cerrar sesion o terminar el programa.

### Almacenamiento en archivos de texto

Los datos se guardan en la carpeta `data_db`. Cada tabla del sistema corresponde a un archivo `.txt`:

| Tabla             | Archivo               | Función                                                       |
| ----------------- | --------------------- | ------------------------------------------------------------- |
| `empleados`     | `empleados.txt`     | Guarda los empleados del sistema con credenciales.            |
| `administrador` | `administrador.txt` | Guarda los administradores vinculados a empleados.            |
| `accesos`       | `accesos.txt`       | Guarda los permisos asignados a cada administrador.           |
| `autobuses`     | `autobuses.txt`     | Guarda la información de los autobuses disponibles.           |
| `rutas`         | `rutas.txt`         | Guarda los lugares de origen y destino de las rutas.          |
| `viajes`        | `viajes.txt`        | Guarda fechas, horarios, cupos y datos de clientes del viaje. |
| `boletos`       | `boletos.txt`       | Guarda los boletos emitidos para cada viaje.                  |
| `reportes`      | `reportes.txt`      | Guarda los reportes generados del sistema.                    |

Cada registro se almacena en una linea con formato de pares `campo=valor`. Para evitar errores con valores que contienen comas, como los permisos de los roles, el sistema utiliza lectura y escritura basada en CSV. Esto permite conservar correctamente valores como:

```txt
permisos=roles,clientes,terminales,lugares,viajes,usuarios,reservaciones
```

### Estructura de las tablas

#### Roles

La tabla `roles` define los tipos de usuario y las secciones a las que puede acceder cada uno.

Campos:

- `id_rol`: identificador unico del rol.
- `nombre_rol`: nombre del rol, por ejemplo Administrador o Recepcionista.
- `permisos`: lista de tablas permitidas para ese rol.

#### Clientes

La tabla `clientes` guarda la informacion basica de las personas que realizan reservaciones.

Campos:

- `id_cliente`
- `nombre`
- `apellido`
- `correo`
- `telefono`

#### Terminales

La tabla `terminales` representa las sucursales o puntos desde donde opera la agencia.

Campos:

- `id_terminal`
- `nombre_terminal`
- `direccion`
- `codigo_postal`

#### Lugares

La tabla `lugares` registra los posibles origenes y destinos de los viajes.

Campos:

- `id_lugar`
- `nombre_lugar`
- `codigo_postal`

#### Viajes

La tabla `viajes` almacena la informacion de cada ruta programada. Cada viaje tiene un lugar de origen, un lugar de destino, una fecha, horario, cupos y costo por asiento.

Campos:

- `id_viaje`
- `id_lugar_origen`
- `id_lugar_destino`
- `fecha`
- `km_recorrer`
- `tiempo_estimado_llegada`
- `cupos_totales`
- `cupos_disponibles`
- `horario`
- `costo_asiento`

#### Usuarios

La tabla `usuarios` almacena a los trabajadores o usuarios que pueden iniciar sesion en el sistema. Cada usuario pertenece a un rol y a una terminal.

Campos:

- `id_usuario`
- `username`
- `password_hash`
- `id_rol`
- `id_terminal`
- `fecha_contratacion`
- `nombre`
- `apellido`
- `direccion`
- `correo`
- `numero`
- `curp`
- `rfc`
- `sueldo`

#### Reservaciones

La tabla `reservaciones` representa la compra o apartado de asientos para un viaje. Relaciona a un cliente, un viaje, el usuario que registra la operacion y la terminal desde donde se realiza.

Campos:

- `id_reservacion`
- `id_cliente`
- `id_viaje`
- `id_usuario`
- `id_terminal`
- `fecha_reservacion`
- `asientos`
- `estado`
- `costo_total`

### Relaciones entre tablas

El sistema funciona con una logica relacional. Aunque no usa un gestor de base de datos tradicional, valida que los identificadores relacionados existan antes de guardar registros.

Relaciones principales:

- Un **rol** puede estar asignado a muchos **usuarios**.
- Una **terminal** puede tener muchos **usuarios**.
- Una **terminal** puede registrar muchas **reservaciones**.
- Un **cliente** puede realizar muchas **reservaciones**.
- Un **usuario** puede registrar muchas **reservaciones**.
- Un **viaje** puede tener muchas **reservaciones**.
- Un **lugar** puede ser origen de muchos **viajes**.
- Un **lugar** puede ser destino de muchos **viajes**.

Estas relaciones estan representadas en el archivo `ER_DIAGRAM.mmd`, el cual contiene el diagrama entidad-relacion en formato Mermaid.

### Logica de reservaciones y cupos

Una de las partes mas importantes del proyecto es el control de cupos. Cada viaje tiene dos campos principales:

- `cupos_totales`: cantidad maxima de asientos del viaje.
- `cupos_disponibles`: cantidad de asientos que todavia pueden reservarse.

Cuando se crea una reservacion, el sistema verifica que el numero de asientos solicitados sea mayor que cero y que no supere los cupos disponibles. Si la reservacion es valida, se descuentan los asientos del viaje.

Ejemplo:

- Cupos totales: 40
- Cupos disponibles antes de reservar: 40
- Asientos reservados: 5
- Cupos disponibles despues de reservar: 35

Cuando se elimina una reservacion, los asientos se devuelven al viaje. Cuando se modifica una reservacion, el sistema calcula la diferencia entre los asientos anteriores y los nuevos para actualizar correctamente los cupos.

### Calculo de costos

Cada viaje tiene un campo `costo_asiento`. Al crear o modificar una reservacion, el sistema calcula automaticamente el costo total multiplicando:

```txt
costo_total = costo_asiento * asientos
```

Por ejemplo, si un asiento cuesta `$30.00` y se reservan 5 asientos:

```txt
30.00 * 5 = 150.00
```

### Validaciones aplicadas

El sistema incluye validaciones para reducir errores de captura y evitar inconsistencias:

- Los IDs se generan automaticamente con UUID.
- Los usuarios no pueden repetir `username`.
- Las contrasenas se guardan como hash con salt.
- Las fechas se manejan con formato `YYYY-MM-DD`.
- Los campos numericos se validan antes de guardarse.
- Las llaves foraneas se verifican antes de crear o modificar registros.
- No se permite reservar si no hay cupos suficientes.
- No se permite eliminar un viaje si tiene reservaciones asociadas.
- Al editar registros, se conserva la llave primaria de la tabla y se permite modificar las relaciones correspondientes.

### Interfaz grafica

La interfaz grafica esta desarrollada con PySide6. Sus archivos principales son:

| Archivo              | Descripcion                                                                     |
| -------------------- | ------------------------------------------------------------------------------- |
| `gui_app.py`       | Controla la ventana principal, login, sesion y navegacion.                      |
| `ui_components.py` | Contiene componentes como dialogos, tablas, busquedas y formularios.            |
| `ui_config.py`     | Define campos, encabezados, relaciones visibles y configuracion de formularios. |
| `styles.qss`       | Contiene los estilos visuales de la aplicacion.                                 |

La aplicacion cuenta con inicio de sesion, menu lateral, tablas visuales, formularios para altas y modificaciones, busqueda de registros relacionados y generacion de ticket de reservacion.

### Revision de consistencia

Despues de revisar las correcciones, las tablas principales coinciden con la logica del programa. Se verifico que:

- Las tablas tengan sus campos definidos.
- Los registros tengan identificadores.
- Las relaciones entre tablas apunten a registros existentes.
- La reservacion registrada coincida con la disponibilidad del viaje.
- Los permisos de roles con comas se puedan leer correctamente.
- El diagrama ER coincida con el modelo implementado.

---

## Conclusion

El proyecto cumple con el objetivo de construir un mini sistema de agencia de viajes con interfaz grafica y almacenamiento en archivos de texto. Aunque no utiliza una base de datos formal como MySQL o SQLite, su estructura imita el comportamiento de tablas relacionales mediante identificadores, relaciones y validaciones.

La separacion entre archivos de datos, logica de operaciones e interfaz grafica permite que el sistema sea mas organizado y facil de mantener. La parte mas relevante del proyecto es el manejo de reservaciones, ya que integra clientes, viajes, usuarios, terminales, cupos y costos dentro de un mismo flujo.

Con las correcciones aplicadas, el modelo de datos queda mas consistente: los roles conservan correctamente sus permisos, las relaciones usan los identificadores adecuados y el diagrama entidad-relacion representa las tablas reales del sistema. En conjunto, el proyecto demuestra el uso de estructuras de datos, archivos, validaciones, interfaz grafica y logica de negocio en una aplicacion funcional.

---

## Bibliografia / Webgrafia

No se consultaron fuentes externas para la elaboracion de esta documentacion. La informacion fue obtenida a partir del analisis del codigo fuente, los archivos de datos y el diagrama del propio proyecto.
