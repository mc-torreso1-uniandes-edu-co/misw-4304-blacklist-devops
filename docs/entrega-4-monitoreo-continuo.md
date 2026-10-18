# Entrega 4 – Monitoreo continuo (CM)

> Universidad de los Andes. Transcripción a Markdown del enunciado oficial ("Entrega 4 - Monitoreo Continuo.pdf"), sin cambios de contenido.

## Objetivos

- Configurar una herramienta de observabilidad en un microservicio
- Identificar y experimentar con las capacidades que ofrece una herramienta de observabilidad

## Tiempo de dedicación

Esta entrega del proyecto está planeada para dos semanas (7 y 8), en las que cada estudiante deberá invertir las horas definidas en la planeación semanal. Recuerde que para el éxito de la actividad es necesario la planeación del trabajo con su equipo, según las pautas definidas en el curso.

## Lecturas previas

- Tutoriales Flask
- Tutoriales de New Relic

## Esquema de evaluación

La distribución de la calificación de la entrega está distribuida de la siguiente manera:

- Configuración de New Relic: **50%**
- Documento del análisis de las capacidades de New Relic (más adelante se detalla lo que debe contener este documento): **50%**

## Lugar y formato de entrega

La entrega está conformada por:

- Aplicación en ejecución sobre AWS Fargate accesible vía Postman
- Repositorio con el código fuente en AWS CodeCommit
- Configuración de Pipeline de integración continua AWS CodeBuild y AWS CodePipeline
- Configuración de Pipeline de entregas continuas con AWS CodeDeploy y AWS CodePipeline
- Configuración de la herramienta de monitoreo New Relic
- Documento de análisis de la herramienta de monitoreo continuo

## Infraestructura requerida para el despliegue

En este proyecto se planea utilizar la siguiente infraestructura y servicios:

- AWS Academy
- Servicios de AWS

## Recomendaciones del documento de la entrega

Se deberá entregar un documento de la entrega. El nombre de este documento debe ser: **"Proyecto 1 entrega 4 – Documento.pdf"**

## Recomendaciones y consideraciones

En este proyecto se deberá continuar el desarrollo del microservicio con las funcionalidades y herramientas mencionadas en la Entrega 1, las pruebas automatizadas y el Pipeline de CI de la entrega 2, y el Pipeline de CD de la entrega 3.

## Alcance de la entrega

La compañía necesita poder monitorear el desempeño de la aplicación una vez entre en producción.

### Configuración de New Relic

El primer paso es configurar la herramienta de observabilidad, en este caso New Relic. Se recomienda seguir los siguientes pasos:

1. **(5%)** Crear la cuenta en New Relic.
2. **(30%)** Realizar la configuración de New Relic en el repositorio del proyecto y verificar que los eventos lleguen a New Relic desde el ambiente de desarrollo.
3. **(15%)** Realizar el despliegue utilizando el Pipeline de CI/CD sobre AWS Fargate y verificar que los eventos lleguen a New Relic desde el ambiente cloud.
4. Explorar las diferentes capacidades de la herramienta de monitoreo en lo relacionado a:
   - a. Tiempo de respuesta de los servicios
   - b. Tiempo de respuesta de la DB
   - c. Monitoreo del Apdex
   - d. Registro de errores en los servicios
   - e. Configuración de alertas/alarmas

## Documento de la entrega

Elabore un documento que incluya los siguientes análisis. Para realizar los análisis es necesario ejecutar pruebas de stress sobre el ambiente cloud (defina y ajuste el escenario de prueba de stress como sea necesario) y monitorear el comportamiento de los servicios con New Relic, para luego documentar los hallazgos en cada análisis.

1. **(20%)** Un análisis de **capacidades de monitoreo del desempeño a nivel de aplicación** que encuentra en la herramienta, teniendo en cuenta:
   - a. Tiempo de respuesta de los servicios
   - b. Tiempo de respuesta de la DB

   Documente las capacidades que ofrece la herramienta y agregue capturas de pantalla de New Relic que soporten el análisis.
2. **(10%)** Un análisis de **capacidades de monitoreo del Apdex** que encuentra en la herramienta. Documente las capacidades que ofrece la herramienta y agregue capturas de pantalla de New Relic que soporten el análisis.
3. **(10%)** Un análisis de **capacidades de registro y monitoreo de errores a nivel de aplicación** que encuentra en la herramienta. Documente las capacidades que ofrece la herramienta y agregue capturas de pantalla de New Relic que soporten el análisis.
4. **(10%)** Un análisis de **capacidades de configuración de alertas** que encuentra en la herramienta. Documente las capacidades que ofrece la herramienta y agregue capturas de pantalla de New Relic que soporten el análisis.

## Sustentación de la entrega

- Se debe realizar un video con la sustentación de la entrega. Este video debe durar máximo 10 minutos (los tutores cortaran el video pasado este tiempo). Lo que se encuentre después del minuto 10 no será teniendo en cuenta y se considera que no fue presentado). El video debe ser explicativo por los integrantes del grupo (uno o varios) y debe contener la explicación y evidencias (consola de AWS, repositorio del código, etc.) funcionales del trabajo realizado para cumplir con todos los requisitos descritos en el entregable, sin dejar lugar a dudas de si algo descrito en el entregable fue o no incluido.
- El video debe evidenciar la configuración y el desarrollo de los escenarios de pruebas para los endpoints de la API, los repositorios de código y el ambiente en GitHub, AWS y New Relic para realizar el proceso de integración, despliegue y monitoreo continuo.
- No se contemplará como sustentación, explicar/mostrar en el video, únicamente el contenido del pdf de la entrega ya que este al final será revisado por el tutor.
- La no entrega del video implica que no hay sustentación de la entrega y por ende la nota de la entrega será calificada con cero (0.0).
- Además del video de sustentación, el tutor podrá citar a su grupo a una sustentación síncrona.
