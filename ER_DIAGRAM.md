# Diagrama Entity-Relationship - Agencia de Viajes

## Modelo simplificado

El diagrama se ajusto para dejar al administrador separado del empleado y para eliminar la tabla de cliente como entidad independiente. Los datos del cliente se integran directamente en viaje para simplificar la estructura.

## Entidades

- **Empleado**: guarda los datos basicos del personal del sistema.
- **Administrador**: representa al empleado con funciones administrativas.
- **Acceso**: concentra los permisos de altas, bajas y modificaciones.
- **Autobus**: almacena la informacion de cada unidad.
- **Ruta**: define origen, destino y distancia estimada.
- **Viaje**: relaciona ruta, autobus, datos del cliente y datos operativos del viaje.
- **Boleto**: registra el asiento y el costo final por asiento reservado.
- **Reporte**: guarda incidencias asociadas a un viaje.

## Relaciones principales

- Un empleado puede ser un administrador o no.
- Un administrador define un acceso.
- Un autobus puede participar en muchos viajes.
- Una ruta puede organizar muchos viajes.
- Un viaje puede generar muchos boletos.
- Un viaje puede tener muchos reportes.

## Campos destacados

### Empleado
- id_empleado
- nombre
- usuario
- contrasena_encriptada

### Administrador
- id_admin
- id_empleado

### Acceso
- id_acceso
- id_admin
- permiso_altas
- permiso_bajas
- permiso_modificaciones
- interfaz_accedida

### Autobus
- id_autobus
- numero_unidad
- modelo
- capacidad_total
- placa

### Ruta
- id_ruta
- origen
- destino
- distancia_estimada

### Viaje
- id_viaje
- id_ruta
- id_autobus
- fecha_salida
- hora_salida
- costo_base
- nombre_cliente
- telefono_cliente
- correo_cliente

### Boleto
- id_boleto
- id_viaje
- numero_asiento
- costo_final

### Reporte
- id_reporte
- id_viaje
- descripcion_incidencia
- fecha_reporte

## Diagrama Mermaid

El archivo [ER_DIAGRAM.mmd](ER_DIAGRAM.mmd) contiene la version actualizada en Mermaid para renderizar el diagrama directamente en el editor o en una vista previa compatible.
