# Rúbrica y control de la Entrega 2 – Integración continua

Resumen de seguimiento del equipo, derivado de `docs/entrega-2-integracion-continua.md` (el enunciado
oficial prevalece ante cualquier diferencia). Sirve para planear las tareas y comprobar el cierre de
cada punto.

## Distribución de la calificación

| Bloque | Peso | Punto del enunciado | Peso del punto | Qué se debe poder mostrar |
|---|---|---|---|---|
| Escenarios de pruebas de la API | 30 % | Configuración del pipeline, punto 1 | 30 % | Al menos una prueba unitaria por endpoint (`POST /blacklists`, `GET /blacklists/<email>`, `GET /ping`) que pasa y que corre en el pipeline |
| Configuración del pipeline de CI | 50 % | Punto 2: proceso de Build en AWS CodeBuild | 10 % | Proyecto de CodeBuild creado y configurado en la consola de AWS |
| | | Punto 3: archivos de configuración en el repositorio | 25 % | Archivo de construcción (por ejemplo `buildspec.yml`) versionado en el repositorio que ejecuta las pruebas unitarias y genera el artefacto (solo la generación, sin desplegarlo) |
| | | Punto 4: disparo automático | 15 % | Cada commit en la rama principal del repositorio inicia el Build de forma automática (se muestra un commit y la ejecución que provoca) |
| Documento del pipeline de CI | 20 % | Documento, punto 1: pipeline exitoso | 10 % | Ejecución exitosa documentada con hallazgos y capturas de los servicios de AWS |
| | | Documento, punto 2: pipeline fallido | 10 % | Ejecución fallida documentada con hallazgos y capturas de los servicios de AWS |

Los pesos de cada bloque suman 100 %: 30 + (10 + 25 + 15) + (10 + 10).

## Qué se entrega

- Aplicación en ejecución sobre AWS Beanstalk accesible vía Postman.
- Repositorio con el código fuente en GitHub.
- Configuración del pipeline de integración continua en AWS CodeBuild.
- Documento `Proyecto 1 entrega 2 – Documento.pdf` (nombre exacto) con las construcciones ejecutadas.
- Video de sustentación de máximo 10 minutos. Sin video, la nota de la entrega es 0,0.

## Condiciones que dejan la entrega en cero o restan puntos

- **Sin video:** nota 0,0. Lo que pase del minuto 10 no cuenta.
- **El video no puede limitarse a leer el PDF:** debe mostrar en vivo la consola de AWS, los repositorios
  y los escenarios de pruebas de los endpoints, y la configuración del proceso de integración continua en
  GitHub y AWS, sin dejar dudas de qué requisito se cumplió.
- **No se implementa despliegue automatizado (CD):** el pipeline termina al generar el artefacto.
- El tutor puede citar a una sustentación síncrona.

## Margen de decisión del equipo (el enunciado lo permite)

- **Pruebas en el pipeline:** con mocks (sin motor de base de datos) o con un motor de base de datos
  levantado dentro de la herramienta de CI.
- **Artefacto generado:** un repositorio (por ejemplo, en AWS S3) o una imagen de contenedor.
- **Contenedores:** se pueden usar o no.
- **Infraestructura:** cuenta de AWS propia o AWS Academy; en este proyecto, la cuenta del equipo.

## Puntos a aclarar o decidir antes de empezar

- El enunciado habla de commits en `master`; el repositorio tiene `main` como rama estable y por defecto.
  Se entiende que el disparo automático es sobre `main`. Confirmar con el tutor si hace falta.
- El enunciado menciona AWS CodePipeline en las lecturas previas pero los puntos hablan de CodeBuild y de
  "configurar el Pipeline" para el disparo por commit. Decidir si el disparo se hace con un webhook de
  CodeBuild o con CodePipeline.
- El entorno de Beanstalk de la Entrega 1 está terminado y la RDS está detenida (ver
  `docs/despliegues/1.7-infraestructura-reproducible.md`, sección 7): la entrega 2 exige la aplicación en
  ejecución accesible vía Postman, así que hay que volver a levantarlos para la sustentación y la
  grabación del video, y apagarlos después.
- Respetar las restricciones del plan gratuito de AWS (sin características avanzadas) al crear los
  recursos de CodeBuild, CodePipeline o S3.

## Control de cierre

| Punto | Evidencia que debe quedar | Estado |
|---|---|---|
| Pruebas por endpoint (30 %) | Salida de `pytest -q` y de la fase de pruebas del Build | Pendiente |
| Proyecto de CodeBuild (10 %) | Capturas de la consola de AWS | Pendiente |
| Archivos de configuración y artefacto (25 %) | Archivo de construcción en el repositorio y artefacto generado | Pendiente |
| Disparo automático por commit (15 %) | Commit y Build iniciado por él | Pendiente |
| Pipeline exitoso (10 %) | Sección del documento con capturas y hallazgos | Pendiente |
| Pipeline fallido (10 %) | Sección del documento con capturas y hallazgos | Pendiente |
| Documento con nombre exacto | `Proyecto 1 entrega 2 – Documento.pdf` | Pendiente |
| Video de 10 minutos o menos | Enlace verificado | Pendiente |
| Aplicación en Beanstalk accesible vía Postman | `/ping` y colección de Postman contra la URL del entorno | Pendiente |
