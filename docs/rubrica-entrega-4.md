# Rúbrica y control de la Entrega 4 – Monitoreo continuo (CM)

Resumen de seguimiento del equipo, derivado de `docs/entrega-4-monitoreo-continuo.md` (el enunciado
oficial prevalece ante cualquier diferencia). Sirve para planear las tareas y comprobar el cierre de
cada punto. La entrega abarca las semanas 7 y 8 (16 al 29 de noviembre de 2026); la fecha oficial es el
domingo 29 de noviembre de 2026, 23:59 (hora de Colombia).

## Distribución de la calificación

| Bloque | Peso | Punto del enunciado | Peso del punto | Qué se debe poder mostrar |
|---|---|---|---|---|
| Configuración de New Relic | 50 % | Punto 1: crear la cuenta en New Relic | 5 % | Cuenta creada y accesible para el equipo |
| | | Punto 2: configuración de New Relic en el repositorio y eventos desde el ambiente de desarrollo | 30 % | Configuración del agente en el código del repositorio (sin secretos) y eventos que llegan a New Relic desde la ejecución local |
| | | Punto 3: despliegue con el pipeline de CI/CD sobre AWS Fargate y eventos desde el ambiente cloud | 15 % | Un despliegue hecho por el pipeline de la Entrega 3 cuyos eventos llegan a New Relic desde Fargate |
| Documento del análisis de New Relic | 50 % | Análisis 1: monitoreo del desempeño a nivel de aplicación (tiempo de respuesta de los servicios y de la DB) | 20 % | Capacidades de la herramienta documentadas con capturas de New Relic |
| | | Análisis 2: monitoreo del Apdex | 10 % | Capacidades documentadas con capturas de New Relic |
| | | Análisis 3: registro y monitoreo de errores a nivel de aplicación | 10 % | Capacidades documentadas con capturas de New Relic |
| | | Análisis 4: configuración de alertas | 10 % | Capacidades documentadas con capturas de New Relic |

Los pesos de cada bloque suman 100 %: (5 + 30 + 15) + (20 + 10 + 10 + 10).

El punto 4 de la configuración (explorar tiempo de respuesta de los servicios y de la DB, Apdex, registro de
errores y alertas) no tiene porcentaje propio, pero alimenta el documento.

## Qué se entrega

- Aplicación en ejecución sobre AWS Fargate accesible vía Postman.
- Repositorio con el código fuente (el enunciado dice AWS CodeCommit; ver la rúbrica de la Entrega 3).
- Pipelines de integración continua (CodeBuild y CodePipeline) y de entrega continua (CodeDeploy y
  CodePipeline) de las entregas 2 y 3.
- Configuración de la herramienta de monitoreo New Relic.
- Documento `Proyecto 1 entrega 4 – Documento.pdf` (nombre exacto) con el análisis de la herramienta.
- Video de sustentación de máximo 10 minutos. Sin video, la nota de la entrega es 0,0.

## Condiciones que dejan la entrega en cero o restan puntos

- **Sin video:** nota 0,0. Lo que pase del minuto 10 no cuenta.
- **El video no puede limitarse a leer el PDF:** debe mostrar la configuración y los escenarios de prueba de
  los endpoints, los repositorios y el ambiente en GitHub, AWS y New Relic, para el proceso de integración,
  despliegue y monitoreo continuo.
- **Pruebas de estrés obligatorias para el documento:** los análisis se hacen ejecutando pruebas de estrés
  sobre el ambiente cloud y monitoreando los servicios con New Relic; el escenario de la prueba lo define el
  equipo y lo ajusta según haga falta.
- **Se hereda lo anterior:** el microservicio, las pruebas, el pipeline de CI (Entrega 2) y el de CD
  (Entrega 3) deben seguir funcionando.
- El tutor puede citar a una sustentación síncrona.

## Puntos a aclarar o decidir antes de empezar

- **Plan de New Relic:** verificar los límites del plan gratuito y que cubra las capacidades que exige el
  documento (desempeño de la aplicación y de la base de datos, Apdex, errores y alertas).
- **Secretos:** la llave de licencia de New Relic nunca va en el repositorio, en la imagen ni en Postman; va
  como secreto del servicio y como variable en `.env` local (que no se versiona).
- **Herramienta de pruebas de estrés:** elegir cuál se usa, cómo se parametriza (usuarios concurrentes,
  duración, endpoints) y desde dónde se ejecuta; guardar los resultados como evidencia.
- **Base de datos:** el análisis de tiempo de respuesta de la DB necesita que la aplicación consulte la RDS
  durante la prueba; `GET /ping` no la consulta.
- **Costo y encendido:** Fargate, el balanceador y la RDS cuestan por hora; deben estar encendidos solo
  durante las pruebas de estrés y la grabación del video.
- **Alertas:** definir al menos una condición de alerta de ejemplo y cómo se provoca para capturarla.

## Control de cierre

| Punto | Evidencia que debe quedar | Estado |
|---|---|---|
| Cuenta de New Relic (5 %) | Captura de la cuenta y de los accesos del equipo | Pendiente |
| Configuración en el repositorio y eventos desde desarrollo (30 %) | Archivos de configuración en el repositorio y captura de eventos en New Relic | Pendiente |
| Despliegue por pipeline y eventos desde la nube (15 %) | Ejecución del pipeline y eventos desde Fargate en New Relic | Pendiente |
| Análisis de desempeño: servicios y DB (20 %) | Sección del documento con capturas y pruebas de estrés | Pendiente |
| Análisis del Apdex (10 %) | Sección del documento con capturas | Pendiente |
| Análisis de errores (10 %) | Sección del documento con capturas | Pendiente |
| Análisis de alertas (10 %) | Sección del documento con capturas | Pendiente |
| Documento con nombre exacto | `Proyecto 1 entrega 4 – Documento.pdf` | Pendiente |
| Video de 10 minutos o menos | Enlace verificado | Pendiente |
| Aplicación en Fargate accesible vía Postman | Colección de Postman contra la URL del servicio | Pendiente |
