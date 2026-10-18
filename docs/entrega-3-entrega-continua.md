# Entrega 3 – Entrega continua (CD)

> Universidad de los Andes. Transcripción a Markdown del enunciado oficial ("Entrega 3 - Entrega Continua.pdf"), sin cambios de contenido.

## Objetivos

- Realizar el despliegue de microservicios sobre una plataforma de contenedores gestionada por el proveedor Cloud
- Configurar un Pipeline que involucre integración continua, y entregas continuas.
- Ejecutar Pipelines de integración continua, y procesos de entregas continuas exitosos y fallidos

## Tiempo de dedicación

Esta entrega del proyecto está planeada para dos semanas (5 y 6), en las que cada estudiante deberá invertir las horas definidas en la planeación semanal. Recuerde que para el éxito de la actividad es necesario la planeación del trabajo con su equipo, según las pautas definidas en el curso.

## Lecturas previas

- Tutoriales Flask
- Tutoriales de AWS Fargate
- Tutoriales AWS Code Build
- Tutoriales AWS Code Pipeline
- Tutoriales AWS Code Deploy

## Esquema de evaluación

La distribución de la calificación de la entrega está distribuida de la siguiente manera:

- Configuración del despliegue del microservicio en AWS Fargate: **20%**
- Configuración del Pipeline con entregas continuas a AWS Fargate: **60%**
- Documento del pipeline de despliegues (más adelante se detalla lo que debe contener este documento): **20%**

## Lugar y formato de entrega

La entrega está conformada por:

- Aplicación en ejecución sobre AWS Fargate accesible vía Postman
- Repositorio con el código fuente en AWS CodeCommit
- Configuración de Pipeline de integración continua AWS CodeBuild y AWS CodePipeline
- Configuración de Pipeline de entregas continuas con AWS CodeDeploy y AWS CodePipeline
- Documento de los despliegues ejecutados

## Infraestructura requerida para el despliegue

En este proyecto se planea utilizar la siguiente infraestructura y servicios:

- AWS Academy
- Servicios de AWS

## Recomendaciones del documento de la entrega

Se deberá entregar un documento de la entrega. El nombre de este documento debe ser: **"Proyecto 1 entrega 3 – Documento.pdf"**

## Recomendaciones y consideraciones

En este proyecto se deberá continuar el desarrollo del microservicio con las funcionalidades y herramientas mencionadas en la Entrega 1, y las pruebas automatizadas y el Pipeline de CI de la entrega 2.

## Alcance de la entrega

La compañía necesita optimizar y agilizar los procesos de entregas continuas de los desarrollos por ende ha decidido agregar un Pipeline automatizando los despliegues.

### Configuración de la plataforma de contenedores

**(20%)** El primer paso es configurar el despliegue del microservicio sobre AWS Fargate. Se recomienda seguir los siguientes pasos:

1. Realizar la configuración manual del ambiente en AWS Fargate
2. Realizar el despliegue manual sobre AWS Fargate
3. Validar que el microservicio quede funcionando de forma exitosa en AWS Fargate

### Configuración del Pipeline de integración continua (CI) y de entrega continua (CD)

Para realizar la configuración del Pipeline de entrega continua, es necesario desarrollar las siguientes actividades:

1. **(10%)** Agregar los archivos de configuración sobre el repositorio del microservicio para que el despliegue continuo funcione sobre AWS CodeDeploy, incluyendo la ejecución de las pruebas unitarias durante el proceso de construcción.
2. **(10%)** Configurar el Pipeline para que cada vez que se haga un commit en master se ejecute automáticamente el proceso de Build incluyendo la creación de la imagen del contenedor que debe ser desplegada
3. **(40%)** Configurar el Pipeline para luego de ejecutarse el proceso de Integración Continua de forma exitosa, se realice el despliegue continuo de forma automática sobre AWS Fargate.

## Documento de la entrega

Elabore un documento que incluya:

1. **(4%)** Ejecute 1 pipeline de Integración Continua fallido. Documente los hallazgos encontrados y agregue capturas de pantalla de los servicios de AWS que soporten los hallazgos.
2. **(8%)** Ejecute 1 pipeline de Integración Continua exitoso y de entrega continua exitoso. Documente los hallazgos encontrados y agregue capturas de pantalla de los servicios de AWS que soporten los hallazgos.
3. **(8%)** Ejecute 1 pipeline de Integración Continua exitoso y de entrega continua fallido. Documente los hallazgos encontrados y agregue capturas de pantalla de los servicios de AWS que soporten los hallazgos.

## Sustentación de la entrega

- Se debe realizar un video con la sustentación de la entrega. Este video debe durar máximo 10 minutos (los tutores cortaran el video pasado este tiempo). Lo que se encuentre después del minuto 10 no será teniendo en cuenta y se considera que no fue presentado). El video debe ser explicativo por los integrantes del grupo (uno o varios) y debe contener la explicación y evidencias (consola de AWS, repositorio del código, etc.) funcionales del trabajo realizado para cumplir con todos los requisitos descritos en el entregable, sin dejar lugar a dudas de si algo descrito en el entregable fue o no incluido.
- El video debe evidenciar la configuración y el desarrollo de los escenarios de pruebas para los endpoints de la API, los repositorios de código y el ambiente en GitHub y AWS para realizar el proceso de integración y despliegue continuo.
- No se contemplará como sustentación, explicar/mostrar en el video, únicamente el contenido del pdf de la entrega ya que este al final será revisado por el tutor.
- La no entrega del video implica que no hay sustentación de la entrega y por ende la nota de la entrega será calificada con cero (0.0).
- Además del video de sustentación, el tutor podrá citar a su grupo a una sustentación síncrona.
