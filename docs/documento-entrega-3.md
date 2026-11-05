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
