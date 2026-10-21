# Rúbrica y control de la Entrega 3 – Entrega continua (CD)

Resumen de seguimiento del equipo, derivado de `docs/entrega-3-entrega-continua.md` (el enunciado
oficial prevalece ante cualquier diferencia). Sirve para planear las tareas y comprobar el cierre de
cada punto. La entrega abarca las semanas 5 y 6 (2 al 15 de noviembre de 2026); la fecha oficial es el
domingo 15 de noviembre de 2026, 23:59 (hora de Colombia).

## Distribución de la calificación

| Bloque | Peso | Punto del enunciado | Peso del punto | Qué se debe poder mostrar |
|---|---|---|---|---|
| Configuración del despliegue en AWS Fargate | 20 % | Configuración manual del ambiente, despliegue manual y validación | 20 % | El microservicio en ejecución en AWS Fargate, creado a mano, con `POST /blacklists`, `GET /blacklists/<email>` y `GET /ping` respondiendo |
| Pipeline con entregas continuas a AWS Fargate | 60 % | Punto 1: archivos de configuración para el despliegue continuo con AWS CodeDeploy, con las pruebas unitarias en la construcción | 10 % | Archivos de configuración versionados en el repositorio (construcción, definición de despliegue y de la tarea) y pruebas ejecutándose en el build |
| | | Punto 2: build automático con cada commit en la rama principal, con creación de la imagen del contenedor | 10 % | Un commit inicia el build solo, ejecuta las pruebas y genera la imagen del contenedor |
| | | Punto 3: despliegue continuo automático sobre AWS Fargate tras un CI exitoso | 40 % | Tras un CI exitoso, el despliegue en Fargate ocurre sin intervención manual y la aplicación responde con la versión nueva |
| Documento del pipeline de despliegues | 20 % | Documento, punto 1: CI fallido | 4 % | Ejecución documentada con hallazgos y capturas de los servicios de AWS |
| | | Documento, punto 2: CI exitoso y CD exitoso | 8 % | Ejecución documentada con hallazgos y capturas de los servicios de AWS |
| | | Documento, punto 3: CI exitoso y CD fallido | 8 % | Ejecución documentada con hallazgos y capturas de los servicios de AWS |

Los pesos de cada bloque suman 100 %: 20 + (10 + 10 + 40) + (4 + 8 + 8).

## Qué se entrega

- Aplicación en ejecución sobre AWS Fargate accesible vía Postman.
- Repositorio con el código fuente (el enunciado dice AWS CodeCommit; ver "Puntos a aclarar").
- Pipeline de integración continua con AWS CodeBuild y AWS CodePipeline.
- Pipeline de entregas continuas con AWS CodeDeploy y AWS CodePipeline.
- Documento `Proyecto 1 entrega 3 – Documento.pdf` (nombre exacto) con los despliegues ejecutados.
- Video de sustentación de máximo 10 minutos. Sin video, la nota de la entrega es 0,0.

## Condiciones que dejan la entrega en cero o restan puntos

- **Sin video:** nota 0,0. Lo que pase del minuto 10 no cuenta.
- **El video no puede limitarse a leer el PDF:** debe mostrar en vivo la configuración y los escenarios de
  prueba de los endpoints, los repositorios y el ambiente en GitHub y AWS para el proceso de integración y
  despliegue continuo, sin dejar dudas de qué requisito se cumplió.
- **Se hereda lo anterior:** el microservicio, las pruebas automatizadas y el pipeline de CI de la
  Entrega 2 deben seguir funcionando.
- El tutor puede citar a una sustentación síncrona.

## Puntos a aclarar o decidir antes de empezar

- **Repositorio:** el enunciado exige el código en AWS CodeCommit y el equipo trabaja en GitHub. Confirmar
  con el tutor si GitHub es aceptable o si hay que replicar el repositorio en CodeCommit, y verificar que la
  cuenta de AWS pueda crear repositorios de CodeCommit.
- **Rama:** el enunciado habla de `master`; el repositorio usa `main` (misma equivalencia que en la Entrega 2).
- **CodePipeline en la Entrega 2:** esta entrega exige CodePipeline para CI y CD. Si en la Entrega 2 el
  disparo se hace con CodePipeline, se reutiliza; si se hizo con el webhook de CodeBuild, hay que migrarlo.
  Conviene decidirlo al diseñar la Entrega 2.
- **Cuenta de AWS:** el enunciado menciona AWS Academy; el equipo usa su cuenta de plan gratuito. Verificar que
  las restricciones del plan (sin características avanzadas) permitan Fargate, un registro de imágenes,
  CodeDeploy y CodePipeline; Fargate y el balanceador cuestan por hora y deben estar encendidos solo mientras
  se trabaja y se graba.
- **Imagen del contenedor:** definir dónde se guarda (registro de imágenes de AWS) y cómo se versiona.
- **CD fallido:** definir cómo se provoca un despliegue fallido sin dejar la aplicación caída (por ejemplo, una
  imagen que no pasa la verificación de salud) y cómo se vuelve atrás.
- **Secretos:** `DATABASE_URL` y `JWT_SECRET_KEY` van como secretos del servicio (no en el repositorio, en la
  imagen ni en la definición de la tarea en texto plano).
- **Base de datos:** la RDS de la Entrega 1 está detenida o eliminada; hay que restaurarla o crear una nueva y
  permitir el acceso desde la tarea de Fargate.

## Control de cierre

| Punto | Evidencia que debe quedar | Estado |
|---|---|---|
| Fargate: ambiente y despliegue manual (20 %) | Capturas de la consola y respuesta de la API en Fargate | Pendiente |
| Archivos de configuración y pruebas en el build (10 %) | Archivos en el repositorio y registro del build con las pruebas | Pendiente |
| Build automático con imagen del contenedor (10 %) | Commit, ejecución disparada por él e imagen en el registro | Pendiente |
| Despliegue continuo automático (40 %) | Ejecución completa del pipeline hasta Fargate sin intervención | Pendiente |
| Documento: CI fallido (4 %) | Sección con capturas y hallazgos | Pendiente |
| Documento: CI y CD exitosos (8 %) | Sección con capturas y hallazgos | Pendiente |
| Documento: CI exitoso y CD fallido (8 %) | Sección con capturas y hallazgos | Pendiente |
| Documento con nombre exacto | `Proyecto 1 entrega 3 – Documento.pdf` | Pendiente |
| Video de 10 minutos o menos | Enlace verificado | Pendiente |
| Aplicación en Fargate accesible vía Postman | Colección de Postman contra la URL del servicio | Pendiente |
