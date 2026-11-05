# Proyecto 1 · Entrega 3: Entrega continua del microservicio con AWS Fargate, CodeDeploy y CodePipeline

| | |
|---|---|
| Curso | MISW 4304 · DevOps · Universidad de los Andes (periodo 202615) |
| Entrega | Entrega 3: despliegue continuo (CD) sobre AWS Fargate |
| Grupo | Blacklist DevOps |
| Integrantes | Marcelo César Torres · Héctor José Melgarejo · Juan Sebastián Páez · Jean Pierre Betancourt |
| Fecha | 15 de noviembre de 2026 |

## Contenido

1. Microservicio heredado y pruebas
2. Arquitectura del CI/CD
3. Configuración del despliegue en Fargate (20 % de la configuración)
4. Archivos de configuración y pipeline (60 % de la configuración)
5. Pipeline de CI fallido (punto 1 del documento, 4 %)
6. Pipeline de CI y CD exitosos (punto 2 del documento, 8 %)
7. CI exitoso y CD fallido, con reversión (punto 3 del documento, 8 %)
8. Enlaces, decisiones y conclusiones

## 1. Microservicio heredado y pruebas

El microservicio administra la lista negra global de emails de la organización. Los sistemas internos
lo usan para agregar un email a la lista y para consultar si un email está en ella. Es un único
servicio REST en Python con Flask, protegido con un token Bearer, que persiste la información en
PostgreSQL sobre Amazon RDS y, desde esta entrega, se ejecuta en AWS ECS con Fargate en lugar de
Elastic Beanstalk.

Es el mismo microservicio de las entregas 1 y 2: su contrato no cambia. Lo que cambia es cómo se
empaqueta y cómo se despliega: el artefacto deja de ser el `.zip` de la aplicación y pasa a ser una
imagen de contenedor publicada en Amazon ECR, y el despliegue deja de ser manual y pasa a ser
automático con AWS CodeDeploy. Se conservan la base de datos RDS `blacklist-db`, el repositorio en
GitHub, la suite de pruebas, la colección de Postman y la aplicación de Beanstalk con su plantilla
`blacklist-base` (se mantiene hasta el cierre del curso para una posible sustentación síncrona de
las entregas 1 y 2).

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| POST | `/blacklists` | Agrega un email a la lista negra. Cuerpo: `email`, `app_uuid` (UUID obligatorio) y `blocked_reason` (opcional, máximo 255 caracteres). Guarda además la IP de origen y la fecha y hora de la solicitud | 201 con `msg` e `id`; 400 con `msg` y `errors`; 401 sin token o con token inválido; 409 si el email ya está |
| GET | `/blacklists/<string:email>` | Indica si el email está en la lista y el motivo | 200 con `is_blacklisted` y `blocked_reason`; 401 sin token o con token inválido |
| GET | `/ping` | Health check del balanceador. No requiere token ni consulta la base | 200 con `{"version": ...}` |

Stack: Python 3.13.16 (imagen `python:3.13.16-slim`), Flask 3.1.3, Flask-SQLAlchemy 3.1.1
(SQLAlchemy 2.1.4), Flask-RESTful 0.3.10, Flask-Marshmallow 1.5.0 (marshmallow 4.3.1),
Flask-JWT-Extended 4.7.4, Werkzeug 3.1.9, PostgreSQL 16 con el driver psycopg 3 (3.3.6, variante
binary) y Gunicorn 26.2.0 como servidor WSGI. Las pruebas usan pytest 9.1.1 y pytest-cov 7.1.0.

El código está organizado por capas: `domain` (entidad, validación del email, errores y reloj),
`application` (casos de uso *agregar* y *consultar*, y el puerto del repositorio) e `infrastructure`
(recursos HTTP, esquema de validación, autenticación y repositorio SQLAlchemy). El email se normaliza a
minúsculas y sin espacios al guardar y al consultar. La imagen copia primero `requirements.txt` y
después el código (`application.py` y `app/`), arranca con `gunicorn --bind :8000 --workers 2` como un
usuario sin privilegios (`appuser`, UID 10001) y recibe la etiqueta de la versión por el argumento
`VERSION`, que escribe el archivo que lee `/ping`.

| Tema | Entrega 2 | Entrega 3 |
|---|---|---|
| Empaquetado | Paquete `.zip` de la aplicación | Imagen de contenedor `python:3.13.16-slim` |
| Registro | Amazon S3 (artefacto del pipeline) | Amazon ECR privado `blacklist-devops` (etiquetas `<commit>` y `latest`) |
| Cómputo | AWS Elastic Beanstalk | AWS ECS con Fargate |
| Despliegue | Manual: una persona sube la versión al entorno | Automático con CodeDeploy, azul/verde con reversión |
| Artefacto del pipeline | `dist/app-<commit>.zip` | `imageDetail.json` con la dirección de la imagen |
| Se conserva | RDS `blacklist-db`, repositorio, pruebas, Postman, entorno de Beanstalk | igual |

### 1.1 Pruebas por endpoint

Cubre la base de los tres puntos del documento: las mismas pruebas que validan el contrato son las
que ejecuta CodeBuild antes de construir la imagen. La suite tiene 156 pruebas. Por archivo
(`pytest --collect-only -q` en `dev`): `test_ambiente_aws` 34, `test_app_creation` 1,
`test_authentication` 10, `test_blacklist_api` 23, `test_configuration` 16, `test_domain` 1,
`test_empaquetar` 15, `test_generar_pdf` 25, `test_monitor_disponibilidad` 25 y `test_ping` 6. Las
de la API son 39 (23 en `tests/test_blacklist_api.py`, 10 casos de credencial inválida en
`tests/test_authentication.py` y 6 en `tests/test_ping.py`); las otras 117 cubren la configuración,
el dominio y los scripts del equipo.

| Endpoint | Respuesta | Escenario | Prueba representativa |
|---|---|---|---|
| `POST /blacklists` | 201 | Alta correcta, con mensaje e id; la IP y la fecha se prueban aparte | `test_post_adds_email_and_returns_id` |
| | 400 | Email inválido, UUID inválido, motivo demasiado largo o campos faltantes | `test_post_rejects_invalid_email` |
| | 401 | Cinco variantes de credencial inválida | `test_post_rejects_invalid_credentials_with_unauthorized` |
| | 409 | Email duplicado, también con otras mayúsculas o espacios, y carrera concurrente | `test_post_duplicated_email_returns_conflict` |
| `GET /blacklists/<email>` | 200 | Email en la lista, con su motivo; insensible a mayúsculas y espacios | `test_get_returns_true_and_reason_for_blacklisted_email` |
| | 200 | Email que no está en la lista | `test_get_returns_false_for_unknown_email` |
| | 401 | Cinco variantes de credencial inválida | `test_get_rejects_invalid_credentials_with_unauthorized` |
| `GET /ping` | 200 | Sin token, solo con la versión y sin consultar la base | `test_ping_does_not_query_the_database` |

Las pruebas usan SQLite en memoria, así que no dependen de un servidor de base de datos ni de la red.
La prueba local del contenedor de la 1.5 se hizo con SQLite por ese mismo motivo y porque la RDS es
privada; la validación contra PostgreSQL corresponde a la 1.11 (#199).

## 2. Arquitectura del CI/CD

El pipeline valida cada cambio, construye la imagen y la despliega sin intervención manual. Ejecuta
las pruebas unitarias en AWS CodeBuild y, si todas pasan, publica la imagen en Amazon ECR y despliega
la versión nueva en AWS ECS con Fargate mediante AWS CodeDeploy. Si la versión nueva no supera la
verificación de salud, CodeDeploy revierte solo a la versión anterior. A diferencia de la Entrega 2,
nada es manual: el *merge* a `main` termina con la versión nueva atendiendo el tráfico.

```
Desarrollador
     │  push a main (en la práctica, el merge del PR dev → main, porque main está protegida)
     ▼
GitHub · repositorio misw-4304-blacklist-devops
     │  conexión blacklist-devops-github (AWS CodeConnections, sin tokens)
     ▼
AWS CodePipeline V2 · blacklist-devops-ci-pipeline
     │  Etapa Origen: código del commit y su identificador (CommitId)
     ▼
     │  Etapa Construcción
     ▼
AWS CodeBuild · blacklist-devops-ci-build (buildspec.yml, modo privilegiado)
     │  1. Instala las dependencias (requirements-dev.txt)
     │  2. Ejecuta las pruebas con pytest ──── una falla ──▶ build Failed: sin imagen y sin despliegue
     │  3. Construye la imagen con la etiqueta del commit (<commit> y latest)
     │  4. La envía a ECR y escribe imageDetail.json
     │  Registros de cada fase en Amazon CloudWatch Logs
     ▼
Amazon ECR · blacklist-devops (etiquetas <commit> y latest)
     │  imageDetail.json como artefacto del pipeline
     ▼
     │  Etapa Despliegue
     ▼
AWS CodeDeploy · blacklist-devops-app / blacklist-devops-dg
     │  Azul/verde sobre el servicio de ECS (controlador CODE_DEPLOY)
     │  Registra blacklist-devops-task con la imagen nueva
     │  Traslada el tráfico del grupo de destino azul al verde
     │  ── salud fallida ──▶ reversión automática a la versión anterior
     ▼
Amazon ECS · Fargate · blacklist-devops-cluster / blacklist-devops-service
     │  1 tarea de 0,25 vCPU y 0,5 GB · contenedor blacklist-devops en el puerto 8000
     │  DATABASE_URL y JWT_SECRET_KEY leídos de Parameter Store (referencias, sin valores)
     │  Registros en CloudWatch Logs (/ecs/blacklist-devops)
     ▼
ALB blacklist-devops-alb (puerto 80) ──▶ tareas ──▶ RDS PostgreSQL blacklist-db
```

| Pieza | Recurso | Qué hace |
|---|---|---|
| Repositorio | GitHub, `misw-4304-blacklist-devops` | Guarda el código, las pruebas y los archivos de configuración (`Dockerfile`, `buildspec.yml`, `appspec.yaml`, `taskdef.json`). `main` es la rama estable y `dev` la de integración; las dos están protegidas: solo cambian por pull request aprobado. El repositorio es el privado de GitHub, conectado a CodePipeline y CodeBuild como en la Entrega 2 (decisión 1 de la 1.1, 3 de 4 votos; confirmada por el curso el 3 de noviembre de 2026: «lo deben entregar en GitHub»). La tarea 1.4 (#192) se cerró como no planeada |
| Conexión | `blacklist-devops-github` (AWS CodeConnections) | Autoriza a AWS a leer el repositorio mediante una aplicación de GitHub limitada a este repositorio, sin tokens personales ni llaves guardadas |
| Pipeline | AWS CodePipeline V2, `blacklist-devops-ci-pipeline` (existe, cambia en la 1.16) | Orquesta las tres etapas: Origen, Construcción y Despliegue. Con cada commit en `main` corren las pruebas, la imagen, el envío a ECR y el despliegue. Abrir o actualizar un pull request ya no ejecuta nada en AWS (decisión 4 de la 1.1) |
| Construcción | AWS CodeBuild, `blacklist-devops-ci-build` (existe, cambia en la 1.14) | Ejecuta el `buildspec.yml` con modo privilegiado: instala las dependencias, corre las pruebas y, si pasan, construye la imagen y la envía a ECR. Si una prueba falla, el build termina en *Failed* y no hay imagen ni despliegue |
| Imagen | Amazon ECR privado, `blacklist-devops` (propuesta, 1.7) | Guarda cada imagen con dos etiquetas: los siete primeros caracteres del commit y `latest`. Una política de ciclo de vida conserva las últimas 10 imágenes |
| Despliegue | AWS CodeDeploy, `blacklist-devops-app` / `blacklist-devops-dg` (propuesta, 1.15) | Despliegue azul/verde sobre el servicio de ECS, con los grupos de destino azul y verde y el *listener* de producción del balanceador. Configuración `CodeDeployDefault.ECSAllAtOnce`; reversión automática si el despliegue falla, sin alarmas de CloudWatch |
| Cómputo | Amazon ECS con Fargate, `blacklist-devops-cluster` / `blacklist-devops-service` (propuesta, 1.10 y 1.11) | Servicio con controlador de despliegue `CODE_DEPLOY`, una tarea con IP pública asignada. Definición `blacklist-devops-task` (0,25 vCPU y 0,5 GB) y contenedor `blacklist-devops` en el puerto 8000 |
| Red | VPC por defecto con subredes públicas; ALB `blacklist-devops-alb` con dos grupos de destino tipo IP (propuesta, 1.9) | El balanceador atiende el puerto 80 y comprueba la salud en `/ping` con código 200. El grupo de las tareas solo acepta el 8000 desde el grupo del balanceador; el de la base solo acepta el 5432 desde el grupo de las tareas. Sin NAT gateway ni *endpoints* de VPC |
| Secretos | Parameter Store, `/blacklist-devops/DATABASE_URL` y `/blacklist-devops/JWT_SECRET_KEY` (propuesta, 1.8) | Parámetros `SecureString` de nivel estándar. La definición de la tarea los referencia en `secrets`; el archivo no contiene ningún valor |
| Permisos | Cuatro roles de IAM (1.6) | Ejecución de ECS (descargar la imagen, escribir registros y leer los dos parámetros), servicio de CodeDeploy para ECS, CodeBuild ampliado con envío a ECR y CodePipeline ampliado con CodeDeploy, ECS y `iam:PassRole` |
| Registros | Amazon CloudWatch Logs | Guarda la salida de cada build y los registros del contenedor (`/ecs/blacklist-devops`, retención de 7 días) |
| Base de datos | RDS PostgreSQL `blacklist-db` (se conserva de la Entrega 1) | Sigue sin acceso público; recibe conexiones solo desde las tareas de Fargate. Si cambia `JWT_SECRET_KEY`, hay que generar un token nuevo para Postman, como hasta ahora |

Los nombres de ECR, ECS, CodeDeploy, el balanceador y los parámetros son propuesta del diseño
(1.3, sección 6): al escribir esta sección aún no existe ninguno en `us-east-2` (verificado el 5
de noviembre: 0 repositorios, 0 clústeres, 0 balanceadores y 0 parámetros). La sección 3 los confirma
al crearse.

**Cuándo se ejecuta.** Con cada *push* a `main`, sin filtro de rutas: todo commit en la rama
principal inicia el pipeline y, si el CI pasa, despliega. Es la decisión 4 de la 1.1: el pipeline
pierde el disparador de pull requests de la Entrega 2, así que abrir o actualizar un PR ya no ejecuta
nada en AWS. Por eso el CI fallido no sale de un PR sin fusionar, sino de una promoción `dev` →
`main` que lleva una prueba que falla (decisión 4 de la 1.2).

**Flujo de una ejecución:**

1. Un desarrollador fusiona un cambio en `main` (el *merge* del PR `dev` → `main`).
2. CodePipeline recibe el evento por la conexión de GitHub y la etapa Origen obtiene el código de ese
   commit.
3. La etapa Construcción lanza CodeBuild, que instala las dependencias y ejecuta las 156 pruebas.
4. Si todas pasan, CodeBuild construye la imagen con la etiqueta del commit, la envía a ECR con las
   etiquetas `<commit>` y `latest`, y escribe `imageDetail.json`. Si una falla, el build y la ejecución
   terminan en *Failed*: no hay imagen nueva y CodeDeploy no se ejecuta.
5. La etapa Despliegue entrega `imageDetail.json`, `appspec.yaml` y `taskdef.json` a CodeDeploy.
6. CodeDeploy registra una revisión de `blacklist-devops-task` con la imagen nueva, levanta la
   versión verde y traslada el tráfico del grupo azul al verde cuando la verificación de salud en
   `/ping` responde 200. Si la versión nueva no pasa la salud, revierte solo a la azul.
7. `/ping` responde la etiqueta del commit desplegado, así que la versión que atiende se comprueba
   con una solicitud sin token.

**Decisiones de la arquitectura:**

- **Fargate en lugar de Beanstalk,** porque la entrega lo pide y no hay servidores que administrar.
- **Controlador de despliegue `CODE_DEPLOY`** en el servicio de ECS, que es lo que habilita el
  azul/verde con los dos grupos de destino.
- **Secretos en Parameter Store (`SecureString`)** y no en la definición de la tarea ni en la imagen.
- **Subredes públicas con IP pública,** sin NAT gateway ni *endpoints* de VPC, que cobran por hora en
  el plan gratuito.
- **Reversión automática sin alarmas de CloudWatch,** porque el criterio es la verificación de salud
  en `/ping`.
- **La etiqueta de la imagen es el commit** (igual que el `.zip` de la Entrega 2), así `/ping`
  demuestra qué versión atiende.
- **Un solo *listener* de producción en el puerto 80,** sin *listener* de prueba: HTTP como en
  Beanstalk, sin dominio ni certificado.

**Costo y encendido.** Unos 0,06 USD/h con todo encendido (Fargate 0,25 vCPU + 0,5 GB, balanceador y
direcciones IPv4; cerca de 1,5 USD por día sin la RDS, precios de `us-east-2` consultados el 4 de
noviembre). El balanceador cobra aunque el servicio esté en cero tareas, así que los recursos solo se
encienden mientras se trabaja y se graba, como en las entregas anteriores.

[PENDIENTE: confirmar esta sección con la configuración real de la 1.6 a la 1.16 (#194–#204), en
particular los nombres de ECR, ECS, CodeDeploy, el balanceador y los parámetros, y el tiempo que
CodeDeploy tarda en declarar fallido el despliegue.]

## 3. Configuración del despliegue en Fargate

[PENDIENTE: tarea 3.2 (#212).]

## 4. Archivos de configuración y pipeline

[PENDIENTE: tarea 3.3 (#213).]

## 5. Pipeline de CI fallido

[PENDIENTE: tarea 3.4 (#214).]

## 6. Pipeline de CI y CD exitosos

[PENDIENTE: tarea 3.5 (#215).]

## 7. CI exitoso y CD fallido, con reversión

[PENDIENTE: tarea 3.6 (#216).]

## 8. Enlaces, decisiones y conclusiones

[PENDIENTE: tarea 3.7 (#217).]
