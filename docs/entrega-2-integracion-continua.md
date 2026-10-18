# Entrega 2 – Integración continua (CI)

> Universidad de los Andes. Transcripción a Markdown del enunciado oficial ("Entrega 2 - Integración Continua.pdf"), sin cambios de contenido.

## Objetivos

- Configurar un Pipeline de integración continua.
- Ejecutar Pipelines de CI exitosos y fallidos.

## Tiempo de dedicación

Esta entrega del proyecto está planeada para dos semanas (3 y 4), en las que cada estudiante deberá invertir las horas definidas en la planeación semanal. Recuerde que para el éxito de la actividad es necesario la planeación del trabajo con su equipo, según las pautas definidas en el curso.

## Lecturas previas

- Tutoriales públicos de Flask o aquellos visto en cursos anteriores
- Tutorial de AWS Beanstalk del curso y documentación pública de AWS Beanstalk
- Tutorial de AWS CodeBuild del curso y documentación pública de AWS CodeBuild
- Tutorial de AWS CodePipeline del curso y documentación pública de AWS CodePipeline

## Esquema de evaluación

La distribución de la calificación de la entrega está distribuida de la siguiente manera:

- Escenarios de pruebas de la API: **30%**
- Configuración del Pipeline de integración continua: **50%**
- Documento del pipeline de CI (más adelante se detalla lo que debe contener este documento): **20%**

## Lugar y formato de entrega

La entrega está conformada por:

- Aplicación en ejecución sobre AWS Beanstalk accesible vía Postman
- Repositorio con el código fuente en GitHub
- Configuración de Pipeline de integración continua AWS Code Build
- Documento de las construcciones ejecutadas

## Infraestructura requerida para el despliegue

En este proyecto se planea utilizar la siguiente infraestructura y servicios:

- AWS Academy o cuenta de AWS propia
- Servicios de AWS

## Recomendaciones del documento de la entrega

Se deberá entregar un documento. El nombre de este documento debe ser: **"Proyecto 1 entrega 2 – Documento.pdf"**

## Recomendaciones y consideraciones

En este proyecto se deberá continuar el desarrollo del microservicio con las funcionalidades y herramientas mencionadas en la Entrega 1. Adicionalmente tener en cuenta:

- En esta entrega pueden o no usar contenedores.
- Las pruebas unitarias dentro el proceso/herramienta de CI las pueden ejecutar:
  - Utilizando mocks (sin depender de un motor de base de datos)
  - Dependiendo de un motor de base de datos dentro del proceso de CI, en cuyo caso van a tener que configurar el despliegue del motor de base dentro de la herramienta de CI.
- Después de finalizar la ejecución de las pruebas unitarias, el proceso debe terminar con la generación del artefacto que luego va a ser desplegado. Este artefacto puede ser:
  - Un repositorio (en AWS S3 por ejemplo)
  - Una imagen de contenedor
- Esta entrega está enfocada en la integración continua (CI) y **No** deben implementar despliegue automatizados (CD).

## Alcance de la entrega

La compañía necesita mejorar la verificación de la confiabilidad de los desarrollos y por ende ha decidido agregar un Pipeline de integración continua a sus procesos de desarrollo.

### Configuración del Pipeline de integración continua (CI)

Para realizar la configuración del Pipeline de integración continua, es necesario desarrollar las siguientes actividades:

1. **(30%)** Configurar y desarrollar al menos un escenario de prueba unitaria para cada endpoint de la API, con el fin de validar que ante futuras modificaciones los desarrolladores puedan rápidamente validar si los endpoints siguen funcionando de forma adecuada.
2. **(10%)** Configurar el proceso de Construcción/Build sobre AWS CodeBuild.
3. **(25%)** Agregar los archivos de configuración sobre el repositorio del microservicio para que la Construcción de artefactos funcione sobre AWS CodeBuild, incluyendo la ejecución de las pruebas unitarias y la generación del artefacto que va a ser desplegado (sólo la generación, No el despliegue del artefacto).
4. **(15%)** Configurar el Pipeline para que cada vez que se haga un commit en master se ejecute automáticamente el proceso de Build.

## Documento de la entrega

Elabore un documento que incluya:

1. **(10%)** Ejecute 1 pipeline de Integración Continua exitoso. Documente los hallazgos encontrados y agregue capturas de pantalla de los servicios de AWS que soporten los hallazgos.
2. **(10%)** Ejecute 1 pipeline de Integración Continua fallido. Documente los hallazgos encontrados y agregue capturas de pantalla de los servicios de AWS que soporten los hallazgos.

## Sustentación de la entrega

- Se debe realizar un video con la sustentación de la entrega. Este video debe durar máximo 10 minutos (los tutores cortaran el video pasado este tiempo). Lo que se encuentre después del minuto 10 no será teniendo en cuenta y se considera que no fue presentado). El video debe ser explicativo por los integrantes del grupo (uno o varios) y debe contener la explicación y evidencias (consola de AWS, repositorios del código, etc.) funcionales del trabajo realizado para cumplir con todos los requisitos descritos en el entregable, sin dejar lugar a dudas de si algo descrito en el entregable fue o no incluido.
- El video debe evidenciar la configuración y el desarrollo de los escenarios de pruebas para los endpoints de la API, los repositorios de código y el ambiente en GitHub y AWS para realizar el proceso de integración continua.
- No se contemplará como sustentación, explicar/mostrar en el video, únicamente el contenido del pdf de la entrega ya que este al final será revisado por el tutor.
- La no entrega del video implica que no hay sustentación de la entrega y por ende la nota de la entrega será calificada con cero (0.0).
- Además del video de sustentación, el tutor podrá citar a su grupo a una sustentación síncrona.
