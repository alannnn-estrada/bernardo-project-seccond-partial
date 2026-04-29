# Diagrama Entity-Relationship - Agencia de Viajes

## Estructura de Entidades y Relaciones

```
CLIENTES                    USUARIOS                   TERMINALES
┌─────────────────┐        ┌──────────────────┐       ┌──────────────────┐
│ CLIENTES        │        │ USUARIOS         │       │ TERMINALES       │
├─────────────────┤        ├──────────────────┤       ├──────────────────┤
│ id_cliente (PK) │◄──┐    │ id_usuario (PK)  │◄──┐   │ id_terminal (PK) │
│ nombre          │   │    │ username         │   │   │ nombre_terminal  │
│ apellido        │   │    │ password_hash    │   │   │ direccion        │
│ correo          │   │    │ id_terminal(FK) ─┼─┐ │   │ codigo_postal    │
│ telefono        │   │    │ fecha_contratacion
                       │   │ nombre          │   │ │
│                 │    │   │ apellido        │   │ │
│                 │    │   │ direccion       │   │ │
│                 │    │   │ correo          │   │ │
│                 │    │   │ numero          │   │ │
│                 │    │   │ rfc             │   │ │
│                 │    │   │ sueldo          │   │ │
└─────────────────┘    │   └──────────────────┘   │ └──────────────────┘
         ▲             │                          │
         │             │◄──────────────┐          │
         │             │               │          │
    (1)  │ (N)         │           (1) │ (N)      │
         │             │               │          │
         │             │               │          │
┌──────────────────────────────────────────────────────────┐
│ RESERVACIONES                                            │
├──────────────────────────────────────────────────────────┤
│ id_reservacion (PK)                                      │
│ id_cliente (FK) ─────────────────────────► CLIENTES     │
│ id_viaje (FK) ──────────────────────────► VIAJES       │
│ id_usuario (FK) ────────────────────────► USUARIOS     │
│ id_terminal (FK) ───────────────────────► TERMINALES   │
│ fecha_reservacion                                        │
│ asientos                                                 │
│ estado (pendiente|confirmada|cancelada)                 │
└──────────────────────────────────────────────────────────┘


LUGARES                     VIAJES
┌──────────────────┐       ┌──────────────────────┐
│ LUGARES          │       │ VIAJES               │
├──────────────────┤       ├──────────────────────┤
│ id_lugar (PK)    │◄──┐   │ id_viaje (PK)        │
│ nombre_lugar     │   │   │ id_lugar_origen(FK)─┐
│ codigo_postal    │   │   │ id_lugar_destino(FK)├─► LUGARES
└──────────────────┘   │   │ fecha                │
                       │   │ km_recorrer          │
                       │   │ tiempo_estimado_llegada
                       │   │ cupos_totales        │
                       │   │ cupos_disponibles    │
                       │   │ horario              │
                       └───┴─────────────────────┘
                           ▲
                       (1) │ (N)
                           │
                    RESERVACIONES (id_viaje)
```

## Relaciones Detalladas (Pata de Cuervo)

### 1. **CLIENTES ←→ RESERVACIONES**
   - **Cardinalidad**: 1 CLIENTE : N RESERVACIONES
   - **Descripción**: Un cliente puede hacer múltiples reservaciones
   - **Clave Foránea**: `reservaciones.id_cliente` → `clientes.id_cliente`
   - **Restricción**: No se puede eliminar un cliente con reservaciones

### 2. **USUARIOS ←→ RESERVACIONES**
   - **Cardinalidad**: 1 USUARIO : N RESERVACIONES
   - **Descripción**: Un usuario puede registrar múltiples reservaciones
   - **Clave Foránea**: `reservaciones.id_usuario` → `usuarios.id_usuario`
   - **Auto-asignación**: Se asigna automáticamente el usuario que inicia sesión

### 3. **TERMINALES ←→ USUARIOS**
   - **Cardinalidad**: 1 TERMINAL : N USUARIOS
   - **Descripción**: Una terminal tiene múltiples usuarios asignados
   - **Clave Foránea**: `usuarios.id_terminal` → `terminales.id_terminal`
   - **Restricción**: No se puede eliminar una terminal con usuarios

### 4. **TERMINALES ←→ RESERVACIONES**
   - **Cardinalidad**: 1 TERMINAL : N RESERVACIONES
   - **Descripción**: Una terminal registra múltiples reservaciones
   - **Clave Foránea**: `reservaciones.id_terminal` → `terminales.id_terminal`
   - **Auto-asignación**: Se asigna automáticamente del terminal del usuario

### 5. **VIAJES ←→ RESERVACIONES**
   - **Cardinalidad**: 1 VIAJE : N RESERVACIONES
   - **Descripción**: Un viaje puede tener múltiples reservaciones
   - **Clave Foránea**: `reservaciones.id_viaje` → `viajes.id_viaje`
   - **Restricción**: No se puede eliminar un viaje con reservaciones activas
   - **Lógica de Cupos**: Al crear reservación se descuentan cupos; al eliminar se devuelven

### 6. **LUGARES ←→ VIAJES (Origen)**
   - **Cardinalidad**: 1 LUGAR : N VIAJES
   - **Descripción**: Un lugar puede ser el origen de múltiples viajes
   - **Clave Foránea**: `viajes.id_lugar_origen` → `lugares.id_lugar`
   - **Restricción**: No se puede eliminar un lugar que es origen de viajes

### 7. **LUGARES ←→ VIAJES (Destino)**
   - **Cardinalidad**: 1 LUGAR : N VIAJES
   - **Descripción**: Un lugar puede ser el destino de múltiples viajes
   - **Clave Foránea**: `viajes.id_lugar_destino` → `lugares.id_lugar`
   - **Restricción**: No se puede eliminar un lugar que es destino de viajes

## Lógica de Negocio

### Sistema de Cupos en Viajes
- **Cupos Totales**: Número máximo de asientos disponibles en un viaje
- **Cupos Disponibles**: Se actualiza cuando se crea/elimina una reservación
- **Validación**: No se puede crear reservación si `cupos_disponibles < asientos_solicitados`
- **Transacción Atómica**: Reserve cupos ANTES de guardar la reservación

### Ciclo de Vida de una Reservación
1. Cliente selecciona un viaje
2. Sistema valida disponibilidad de cupos
3. Usuario registra la reservación (se auto-asigna usuario y terminal)
4. Sistema descuenta cupos del viaje
5. Reservación se marca como "pendiente"
6. Usuario puede cambiar estado a "confirmada" o "cancelada"
7. Al eliminar o cancelar, se devuelven los cupos

### Restricciones de Integridad
- No se puede eliminar un cliente con reservaciones
- No se puede eliminar un viaje con reservaciones (activas)
- No se puede eliminar una terminal con usuarios
- No se puede eliminar un lugar que sea origen/destino de viajes
- Username único en tabla usuarios
- Foreign keys deben existir en sus tablas referenciadas

## Diagrama en Notación Crow's Foot (ASCII)

```
                          ┌──────────────────────┐
                          │     TERMINALES       │
                          ├──────────────────────┤
                          │ id_terminal (PK)     │
                          │ nombre_terminal      │
                          │ direccion            │
                          │ codigo_postal        │
                          └──────────────────────┘
                                    ▲
                    (1)    ╱─────────┘
                          ╱
                   (N)   ╱
                       ╱
              ┌─────────────────┐              ┌──────────────────────┐
              │    USUARIOS     │              │    CLIENTES          │
              ├─────────────────┤              ├──────────────────────┤
              │ id_usuario (PK) │              │ id_cliente (PK)      │
              │ username        │              │ nombre               │
              │ password_hash   │              │ apellido             │
              │ id_terminal(FK) │              │ correo               │
              │ ...datos...     │              │ telefono             │
              └─────────────────┘              └──────────────────────┘
                    ▲                                  ▲
        (1)         │                      (1)        │
              ╱─────┘                             ╱──┐│
             ╱                                   ╱   ││
        (N)╱                               (N) ╱    ││
          ╱                                   ╱     │└──────────────┐
    ┌─────────────────────────────────────────────────────────────┐   │
    │          RESERVACIONES                                       │   │
    ├─────────────────────────────────────────────────────────────┤   │
    │ id_reservacion (PK)                                         │   │
    │ id_cliente (FK) ─────────────────────────────────────────┐  │   │
    │ id_viaje (FK) ──────────────────────────┐              │  │   │
    │ id_usuario (FK) ─────────────────────┐  │              │  │   │
    │ id_terminal (FK) ────────────────────┼──┼──────────────┼──┼─┐  │
    │ fecha_reservacion                    │  │              │  │ │  │
    │ asientos                             │  │              │  │ │  │
    │ estado                               │  │              │  │ │  │
    └─────────────────────────────────────────────────────────────┘   │
                                           │  │              │  │ │   │
                                       (N)│  │ (1)      (N)│  │(1)│
                                           │  │              │  └┴─┘
                                           │  ▼              │
                                      ┌──────────────┐       │
                                      │   VIAJES     │       │
                                      ├──────────────┤       │
                                      │id_viaje(PK)  │       │
                                      │id_lugar_... (FK)─┐  │
                                      │fecha             │  │
                                      │km_recorrer       │  │
                                      │tiempo_estimado   │  │
                                      │cupos_totales     │  │
                                      │cupos_disponibles │  │
                                      │horario           │  │
                                      └──────────────────┘  │
                                                    ▲        │
                                                    │        │
                                        (1)  ╱──────┘        │
                                             ╱               │
                                      (N) ╱             (1)  │
                                         ╱                   │
                                     ┌─────────────────┐     │
                                     │  LUGARES        │◄────┘
                                     ├─────────────────┤
                                     │ id_lugar (PK)   │
                                     │ nombre_lugar    │
                                     │ codigo_postal   │
                                     └─────────────────┘
```

## Ejemplo de Operaciones

### Crear una Reservación
1. Verificar que cliente existe
2. Verificar que viaje existe y tiene cupos disponibles
3. Auto-asignar id_usuario (del usuario logueado)
4. Auto-asignar id_terminal (del usuario logueado)
5. Auto-asignar fecha_reservacion (fecha actual)
6. Decrementar cupos: `viaje.cupos_disponibles -= reservacion.asientos`
7. Guardar reservación con estado "pendiente"

### Cancelar una Reservación
1. Buscar la reservación
2. Cambiar estado a "cancelada"
3. Liberar cupos: `viaje.cupos_disponibles += reservacion.asientos`
4. Guardar cambios

### Listar Viajes Disponibles
```
SELECT v.* 
FROM viajes v 
WHERE v.cupos_disponibles > 0 
AND v.fecha >= CURDATE()
ORDER BY v.fecha, v.horario
```

### Contar Reservaciones por Cliente
```
SELECT c.nombre, c.apellido, COUNT(r.id_reservacion) as total_reservas
FROM clientes c
LEFT JOIN reservaciones r ON c.id_cliente = r.id_cliente
GROUP BY c.id_cliente
ORDER BY total_reservas DESC
```

## Notas Técnicas
- Los IDs se generan con formato: `id_tabla_<uuid>`
- Las contraseñas se almacenan hasheadas (SHA-256 con salt)
- Los datos se persisten en archivos TXT con formato key=value
- La aplicación carga todos los datos en memoria al iniciar
- Las operaciones son atómicas: cargar → modificar → guardar
