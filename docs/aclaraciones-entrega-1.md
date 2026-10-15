# Aclaraciones del curso sobre la Entrega 1

Respuestas de los tutores a preguntas del equipo. Complementan el enunciado
(`docs/entrega-1-despliegue-manual-microservicio.md`), que no se modifica. Registradas el 14 de octubre
de 2026.

## 1. Disponibilidad de los recursos de AWS durante la calificación

**Pregunta del equipo:** ¿Los recursos en AWS deben estar disponibles para la calificación o solo para
la grabación del video? Esto pensando en ahorrar costos de la cuenta gratuita (entre 100 y 200 USD de
crédito). En caso de que sea necesario que estén arriba para la calificación, ¿desde cuándo y hasta
cuándo deberían estar encendidos?

**Respuesta del tutor:** Por lo general solo deben estar disponibles mientras los grupos realizan el
trabajo y elaboran la sustentación en el video; luego de ello pueden borrar los recursos. Ahora bien,
si se encuentra alguna inconsistencia, alguna duda o algo no cuadra técnicamente dentro de la entrega,
el tutor podrá solicitar una sustentación al equipo, y para ello deben volver a proveer el ambiente y
los recursos mientras realizan una entrega sincrónica.

### Cómo lo aplica el equipo

- El entorno se enciende solo en ventanas de trabajo: primer despliegue, pruebas contra AWS,
  estrategias de despliegue y grabación del video. Al cerrar cada ventana se termina el entorno y se
  detiene la RDS.
- No hay periodo de revisión con el entorno encendido. Como el tutor no prueba la aplicación en vivo,
  el video debe mostrar contra la URL de Beanstalk el POST, el GET, `/ping` y la ejecución de la
  colección de Postman.
- Después de la fecha de entrega se eliminan los recursos con costo y se conserva lo necesario para
  reconstruir el ambiente si el tutor cita a una sustentación síncrona:

| Recurso | Después de la entrega | Motivo |
|---|---|---|
| Entorno de Beanstalk (instancias y balanceador) | Terminado | Es el costo principal por hora |
| RDS `blacklist-db` | Snapshot final y eliminación | Detenida, AWS la vuelve a encender a los 7 días y cobra por hora |
| Snapshot final de la RDS | Se conserva | Permite restaurar la base con sus datos |
| Configuración guardada `blacklist-base` | Se conserva | Recrea el entorno con la misma configuración y URL |
| Versiones de la aplicación en S3 | Se conservan | Se despliegan sin regenerar el paquete |
| Grupos de seguridad y roles de IAM | Se conservan | Sin costo; la RDS restaurada y el entorno los necesitan |

El procedimiento para volver a proveer el ambiente está en
`docs/despliegues/1.7-infraestructura-reproducible.md`, sección 7.4.
