# Microservicio de Lista Negra Global de Emails
Proyecto de DevOps - MISW - 202615. Grupo Blacklist DevOps

Microservicio REST en Python y Flask para que los sistemas internos de una empresa agreguen emails a una lista negra global y consulten si un email está en ella. Corre como contenedor en AWS Fargate (Amazon ECS), detrás de un balanceador de carga, con PostgreSQL en Amazon RDS (región `us-east-2`). Cada commit en `main` pasa por un pipeline de integración y despliegue continuos: AWS CodeBuild ejecuta las pruebas y construye la imagen, la publica en Amazon ECR y AWS CodeDeploy la despliega en Fargate con un despliegue azul/verde, sin intervención manual. Si la versión nueva no queda sana, CodeDeploy vuelve a la anterior.

En las entregas 1 y 2 el microservicio corría en AWS Elastic Beanstalk, con despliegue manual; las secciones de Beanstalk se conservan al final como referencia.

## Enlaces
| Recurso | Enlace |
|---|---|
| Documentación del API (Postman) | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| API en AWS Fargate | http://blacklist-devops-alb-663902063.us-east-2.elb.amazonaws.com (se enciende solo mientras se trabaja; `/ping` indica si responde y qué versión atiende) |
| Pipeline de CI/CD | Consola de AWS, región `us-east-2`: CodePipeline `blacklist-devops-ci-pipeline`, CodeBuild `blacklist-devops-ci-build` y CodeDeploy `blacklist-devops-app` |
| Entorno de Beanstalk (entregas 1 y 2) | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com (terminado; se vuelve a levantar con `scripts/ambiente_aws.py`) |

## Stack
| Componente | Versión |
|---|---|
| Python | 3.13.16 |
| Flask / Werkzeug | 3.1.3 / 3.1.9 |
| Flask-SQLAlchemy / SQLAlchemy | 3.1.1 / 2.1.4 |
| Flask-RESTful | 0.3.10 |
| Flask-Marshmallow / marshmallow | 1.5.0 / 4.3.1 |
| Flask-JWT-Extended | 4.7.4 |
| PostgreSQL (driver `psycopg`) | 16 (3.3.6) |
| Gunicorn | 26.2.0 |

## Estructura del repositorio
```
application.py        # expone `application` (WSGI), el nombre que espera Beanstalk
app/                  # el microservicio, por capas
  domain/             #   entidad, validación del email, errores y reloj
  application/        #   casos de uso (agregar y consultar) y puerto del repositorio
  infrastructure/     #   http (rutas, recursos, esquema y autenticación) y persistence (SQLAlchemy)
scripts/              # generar_token.py, empaquetar.py, monitor_disponibilidad.py, ambiente_aws.py y generar_pdf.py
tests/                # pytest
postman/              # colección y environments (JSON v2.1)
docs/                 # enunciados, rúbricas y aclaraciones del curso, documentos de cada entrega y:
  ci/                 #   diseño, configuración y ejecuciones del pipeline (la Entrega 3 en ci/entrega-3/)
  pruebas/            #   escenarios por endpoint y resultados de las pruebas
  despliegues/        #   infraestructura reproducible y mediciones de las estrategias de despliegue
  capturas/           #   capturas de las entregas (desde la Entrega 2, en capturas/entrega-<N>/)
  pdf/                #   PDF del documento de cada entrega (lo genera el flujo documento-pdf)
.ebextensions/        # configuración de Beanstalk (health check en /ping)
.github/workflows/    # chequeos de las ramas y generación del PDF del documento
Dockerfile            # imagen del microservicio (Python 3.13.16, Gunicorn en el puerto 8000)
.dockerignore         # lo que no entra en la imagen (pruebas, docs, scripts, .env...)
buildspec.yml         # archivo de construcción de CodeBuild: pruebas, imagen, envío a ECR y artefactos
taskdef.json          # plantilla de la definición de la tarea de Fargate (imagen como marcador)
appspec.yaml          # especificación de CodeDeploy: servicio, contenedor y puerto que recibe el tráfico
requirements.txt      # dependencias de la aplicación
requirements-dev.txt  # las de la aplicación más pytest y pytest-cov
.python-version       # 3.13.16
.env.example          # variables de entorno locales, sin valores reales
Procfile              # web: gunicorn --bind :8000 --workers 2 application:application (Beanstalk)
VERSION               # etiqueta de versión que devuelve /ping (la escriben la imagen y el empaquetado)
```

## Requisitos
- Python 3.13.16 (la versión de `.python-version`). Se instala desde python.org o con `uv python install 3.13.16`
- PostgreSQL (o SQLite para pruebas locales)
- Docker, para construir y ejecutar la imagen en local (opcional)

## Crear el entorno

Windows (PowerShell):
```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Linux / macOS:
```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Configuración
Copia `.env.example` a `.env` (obligatorio, sin él la aplicación no arranca) y completa los valores:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión, por ejemplo `postgresql://usuario:clave@host:5432/base` o `sqlite:///local.db`. Siempre `postgresql://`, sin sufijo de driver |
| `JWT_SECRET_KEY` | Clave con la que se firma y valida el token |
| `APP_ENV` | Opcional. `development` (por defecto, también si queda vacío), `production` o `testing`. Otro valor detiene el arranque con un mensaje que lista los válidos |
| `PROXY_FIX_X_FOR` | Opcional. Cantidad de proxies que agregan una entrada a `X-Forwarded-For` antes de la aplicación, para guardar la IP del cliente. `1` por defecto |

Las tablas se crean automáticamente al iniciar la aplicación.

## Token de autorización
El API usa un único token estático, generado con la misma `JWT_SECRET_KEY` del entorno:
```bash
python scripts/generar_token.py
```
Los clientes lo envían en el encabezado `Authorization: Bearer <token>`. Si cambia `JWT_SECRET_KEY`, hay que generar uno nuevo.

## Ejecutar el API

Windows (PowerShell), con `python -m` funciona aunque la política del equipo bloquee `flask.exe`:
```powershell
$env:FLASK_APP = "application"
python -m flask run
```

En CMD usa `set FLASK_APP=application` en lugar de `$env:FLASK_APP = "application"`.

Linux / macOS:
```bash
FLASK_APP=application python -m flask run
```

El API queda en `http://127.0.0.1:5000`. Gunicorn no funciona en Windows; en Linux, el comando del `Procfile` también sirve en local.

## Ejecutar el contenedor en local
La imagen es la misma que el pipeline publica en ECR: Python 3.13.16 (`python:3.13.16-slim`), solo las dependencias de `requirements.txt`, la aplicación y Gunicorn en el puerto 8000, con un usuario sin privilegios. No incluye `.env`, pruebas, `docs/` ni `scripts/` (ver `.dockerignore`).

```bash
docker build --platform linux/amd64 --build-arg VERSION=local -t blacklist-devops:local .
docker run --rm --env-file .env -p 8000:8000 blacklist-devops:local
```

- `--build-arg VERSION` es la etiqueta que devuelve `/ping`; el pipeline usa los siete primeros caracteres del commit.
- `--env-file .env` entrega `DATABASE_URL`, `JWT_SECRET_KEY` y `APP_ENV` al contenedor sin guardarlos en la imagen. Con `DATABASE_URL=sqlite:///local.db` la base queda dentro del contenedor y se pierde al detenerlo. La RDS del proyecto es privada y no se alcanza desde un equipo local.
- El API queda en `http://localhost:8000`: `curl http://localhost:8000/ping` responde `{"version": "local"}`. El environment `blacklist-local` de Postman apunta al puerto 5000; para el contenedor se cambia `base_url` a `http://localhost:8000`.

## Endpoints
Los de `/blacklists` requieren el encabezado `Authorization: Bearer <token>`. `/ping` es público.

| Método | Ruta | Respuestas |
|---|---|---|
| GET | `/ping` | 200 con `{"version": ...}`, leída del archivo `VERSION` |
| POST | `/blacklists` | 201 con `msg` e `id`, 400 con `msg` y `errors`, 401 con `msg`, 409 con `msg` si el email ya está |
| GET | `/blacklists/<email>` | 200 con `is_blacklisted` y `blocked_reason`, 401 con `msg` |

El email se normaliza a minúsculas y sin espacios al guardar y al consultar. El POST guarda además la IP de origen y la fecha y hora de la solicitud.

Cuerpo del POST:
```json
{
  "email": "cliente@example.com",
  "app_uuid": "0b8f6a52-6f0c-4c1e-9a8e-5f1d2c3b4a5e",
  "blocked_reason": "Motivo opcional de máximo 255 caracteres"
}
```

## Pruebas
No necesitan `.env`, base de datos ni red: usan SQLite en memoria. Basta con crear el entorno (sección "Crear el entorno") y, con el entorno activado, ejecutar desde la raíz del repositorio:
```bash
python -m pytest -q
python -m pytest -q --cov=app
```

El segundo comando es el mismo que ejecuta el pipeline. El resultado esperado es `171 passed` y una cobertura del 100 % sobre `app/`. Para correr la misma suite contra PostgreSQL, define `DATABASE_URL` antes de ejecutarla.

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `tests/test_blacklist_api.py` | 23 | `POST /blacklists` y `GET /blacklists/<email>` |
| `tests/test_authentication.py` | 10 | 401 en los dos endpoints protegidos, cinco variantes de credencial en cada uno |
| `tests/test_ping.py` | 6 | `GET /ping` y lectura del archivo `VERSION` |
| `tests/test_configuration.py` | 16 | Configuración por ambiente |
| `tests/test_empaquetar.py` | 15 | Script de empaquetado |
| `tests/test_monitor_disponibilidad.py` | 25 | Script de monitoreo del despliegue |
| `tests/test_ambiente_aws.py` | 34 | Script para apagar y volver a levantar el ambiente de Beanstalk |
| `tests/test_generar_pdf.py` | 40 | Generador del PDF del documento de cada entrega |
| `tests/test_app_creation.py` | 1 | Creación de la aplicación |
| `tests/test_domain.py` | 1 | Entidad de dominio |

Escenarios por endpoint (cada respuesta del contrato tiene al menos una prueba):

| Endpoint | Escenarios |
|---|---|
| `POST /blacklists` | **201**: alta correcta con `msg` e `id`, sin `blocked_reason` o con él nulo, email guardado normalizado, IP del cliente desde `X-Forwarded-For`, fecha de creación, motivo de 255 caracteres. **400**: email o `app_uuid` inválidos, motivo de 256 caracteres, campos obligatorios faltantes, cuerpo que no es JSON o JSON mal formado. **409**: email duplicado, también con otras mayúsculas, con espacios alrededor o por una solicitud concurrente. **401**: sin token, token malformado, esquema no soportado, `Bearer` sin token y token firmado con otra clave |
| `GET /blacklists/<email>` | **200**: email en la lista con su motivo, email que no está (`is_blacklisted` falso y motivo nulo), mayúsculas y espacios normalizados. **401**: las mismas cinco variantes de credencial |
| `GET /ping` | **200** sin token y con el cuerpo exacto `{"version": ...}`, sin consultar la base; la versión sale de `VERSION`, con un valor por defecto si falta o está vacío |

El detalle prueba por prueba está en `docs/pruebas/2.1-escenarios-por-endpoint.md`.

## Integración y despliegue continuos
Un pipeline de AWS CodePipeline (V2), `blacklist-devops-ci-pipeline`, con tres etapas:

```
push a main ──▶ Source (GitHub) ──▶ Build (CodeBuild) ──▶ Deploy (CodeDeploy) ──▶ Fargate
                                    pruebas, imagen       azul/verde con
                                    y envío a ECR         reversión automática
```

| Etapa | Servicio | Qué hace |
|---|---|---|
| Source | GitHub, por la conexión `blacklist-devops-github` (autorizada solo para este repositorio) | Obtiene el código del commit de `main` y su identificador |
| Build | CodeBuild `blacklist-devops-ci-build`, con `buildspec.yml` | Ejecuta las pruebas, construye la imagen, la envía a ECR y entrega `imageDetail.json`, `taskdef.json` y `appspec.yaml` |
| Deploy | CodeDeploy `blacklist-devops-app`, grupo `blacklist-devops-dg` (acción `CodeDeployToECS`) | Registra una revisión de la definición de la tarea con la imagen nueva y la despliega en el servicio de Fargate |

**Cuándo se ejecuta:**
- Con cada *push* a `main`, es decir, cada commit que llega a la rama principal (en la práctica, el *merge* de la promoción `dev` → `main`), sin excluir ningún archivo.
- Abrir o actualizar un pull request no ejecuta nada en AWS: el disparador de pull requests de la Entrega 2 se quitó.
- Las ejecuciones se encolan (modo `QUEUED`): una no reemplaza a otra en curso.

**Qué hace el build** (`buildspec.yml`, imagen `amazonlinux-x86_64-standard:6.0` con Python 3.13 y modo privilegiado para Docker):
1. `install`: `pyenv install --skip-existing` con la versión de `.python-version` (3.13.16; la imagen trae otro parche de 3.13 y lo compila si falta), luego `pip install -r requirements-dev.txt`.
2. `build`: `python -m pytest -q --cov=app` es el primer comando. Si una prueba falla, el build termina en *Failed*: no se construye la imagen y la etapa Deploy no se ejecuta.
3. Si las pruebas pasan, inicia sesión en ECR y construye la imagen con dos etiquetas: los siete primeros caracteres del commit (variable `COMMIT_ID`, que le pasa el pipeline) y `latest`. La etiqueta del commit queda en `VERSION`, así que `/ping` la devuelve.
4. `post_build`: solo si el build sigue en verde (`CODEBUILD_BUILD_SUCCEEDING = 1`), envía las dos etiquetas al repositorio `blacklist-devops` de ECR y escribe `imageDetail.json` con la dirección de la imagen.
5. `artifacts`: `imageDetail.json`, `taskdef.json` y `appspec.yaml`, la entrada de la etapa Deploy. Salen del build y no del código fuente porque la acción de CodeDeploy acepta artefactos de hasta 3 MB.

**Cómo despliega** (`taskdef.json` y `appspec.yaml`):
- La etapa Deploy reemplaza `<IMAGE1_NAME>` de `taskdef.json` por la imagen de `imageDetail.json`, registra una revisión nueva de `blacklist-devops-task` y reemplaza `<TASK_DEFINITION>` de `appspec.yaml` por esa revisión.
- CodeDeploy levanta la versión nueva en el grupo de destino que no atiende el tráfico (`blacklist-devops-tg-azul` o `blacklist-devops-tg-verde`) y mueve el tráfico del *listener* HTTP:80 del balanceador con `CodeDeployDefault.ECSCanary10Percent5Minutes`: el 10 % durante 5 minutos y después el resto. La versión anterior se termina 2 minutos después.
- Si la versión nueva queda en mal estado, el despliegue falla y CodeDeploy revierte solo a la anterior. El contenedor tiene una verificación de salud contra `/ping` (`healthCheck` de `taskdef.json`), así que ECS solo da por estable una tarea que responde.

**Infraestructura en AWS** (cuenta del proyecto, región `us-east-2`):

| Recurso | Nombre |
|---|---|
| Repositorio de imágenes | Amazon ECR `blacklist-devops` (privado; conserva las últimas 10 imágenes) |
| Clúster y servicio | `blacklist-devops-cluster` y `blacklist-devops-service`: 1 tarea de Fargate de 0,25 vCPU y 0,5 GB, controlador de despliegue `CODE_DEPLOY` |
| Definición de la tarea | `blacklist-devops-task` (una revisión por despliegue) |
| Balanceador | `blacklist-devops-alb`, *listener* HTTP:80 y grupos de destino azul y verde con salud en `/ping` |
| Secretos | Parameter Store: `/blacklist-devops/DATABASE_URL` y `/blacklist-devops/JWT_SECRET_KEY` (`SecureString`). `taskdef.json` los referencia por ARN, sin valores |
| Base de datos | RDS PostgreSQL `blacklist-db`, privada; solo acepta conexiones desde las tareas de Fargate |
| Registros | CloudWatch Logs: `/ecs/blacklist-devops` (contenedor) y los de cada build |

**Dónde ver los resultados** (consola de AWS, región `us-east-2`):
| Qué | Dónde |
|---|---|
| Historial de ejecuciones, con el commit y el disparador de cada una | CodePipeline → `blacklist-devops-ci-pipeline` → *Executions* |
| Fases del build, su duración y el registro con el resultado de `pytest` | CodeBuild → `blacklist-devops-ci-build` → *Build history* (el registro también queda en CloudWatch Logs) |
| Imagen de cada commit | ECR → `blacklist-devops` |
| Despliegues, pasos del tráfico y reversiones | CodeDeploy → *Deployments* (aplicación `blacklist-devops-app`) |
| Tareas, revisión en uso y eventos del servicio | ECS → `blacklist-devops-cluster` → `blacklist-devops-service` |

Después de un despliegue, `GET /ping` contra el balanceador responde la etiqueta del commit desplegado. Diseño, configuración y ejecuciones documentadas en `docs/ci/entrega-3/`: diseño en `1.3-diseno-pipeline.md`, configuración completa en `1.17-pipeline-cd.md`, CI y CD exitosos en `2.3-pipeline-exitoso.md`, CI fallido en `2.4-ci-fallido.md`, CD fallido con reversión en `2.5-cd-fallido.md` y versión final en `2.6-version-final.md`. El pipeline de la Entrega 2, que solo generaba el paquete de Beanstalk, está documentado en `docs/ci/`.

**Apagar y encender.** Fargate y el balanceador cobran por hora mientras están encendidos, y el balanceador cobra aunque el servicio no tenga tareas. Para apagar, el servicio se baja a cero tareas, se elimina el balanceador y se detiene la RDS. El procedimiento completo, con los pasos para volver a encender, está en la sección 8 de `docs/ci/entrega-3/1.3-diseno-pipeline.md`. Bajar el servicio a cero tareas:
```bash
aws ecs update-service --cluster blacklist-devops-cluster --service blacklist-devops-service --desired-count 0 --region us-east-2
```

## Postman
La colección y los environments (`blacklist-local`, `blacklist-fargate` y `blacklist-aws`) están en `postman/`. Importa los archivos, completa `token` en el environment y ejecuta los escenarios en orden. `base_url` ya apunta a `http://localhost:5000` (local), a `http://blacklist-devops-alb-663902063.us-east-2.elb.amazonaws.com` (Fargate) y a `http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com` (Beanstalk, entregas 1 y 2). El token se carga solo como valor actual, nunca como valor inicial: el workspace es público. Los resultados contra AWS están en `docs/pruebas/2.3b-pruebas-aws.md`.

## Elastic Beanstalk (entregas 1 y 2)
Las secciones siguientes son de las entregas 1 y 2, cuando el microservicio corría en Elastic Beanstalk con despliegue manual. Se conservan como referencia: el entorno puede volver a levantarse si hace falta sustentar esas entregas.

### Empaquetar y desplegar en Beanstalk
Para generar en local el paquete `.zip` de Beanstalk:
```bash
python scripts/empaquetar.py <etiqueta>   # por ejemplo v1.1
```
Ejecuta las pruebas y genera `dist/app-<etiqueta>.zip` con `application.py`, `app/`, `requirements.txt`, `Procfile` y `.ebextensions/`. La etiqueta se escribe en el archivo `VERSION` dentro del paquete, y es la que devuelve `/ping`. Con `--omitir-pruebas` genera el paquete sin ejecutarlas.

El `.zip` se carga como versión de la aplicación en Elastic Beanstalk y se despliega desde la consola, o con la AWS CLI:
```bash
aws elasticbeanstalk update-environment --environment-name Blacklist-devops-env --version-label <etiqueta> --region us-east-2
```

Propiedades del entorno (nunca van en el repositorio): `DATABASE_URL`, `JWT_SECRET_KEY`, `APP_ENV=production` y `PROXY_FIX_X_FOR=2`. En Beanstalk la solicitud pasa por el balanceador y por el nginx de la instancia, por eso son dos saltos. El balanceador comprueba cada instancia con `GET /ping`.

El procedimiento para crear y recrear el entorno está en `docs/despliegues/1.7-infraestructura-reproducible.md`.

### Estrategias de despliegue
Las cuatro estrategias se ejecutaron sobre el mismo entorno, con Auto Scaling de 3 a 6 instancias `t3.micro`. Cada paquete tiene el mismo código y solo cambia `VERSION`.

| Estrategia | Versión | Tiempo | Instancias (antes / máx. / después) | Caída observada | Detalle |
|---|---|---|---|---|---|
| All at once | `v2-allatonce` | 0 min 21 s | 3 / 3 / 3 | 5 s con respuestas `502` | `docs/despliegues/2.4a-all-at-once.md` |
| Rolling | `v3-rolling` | 8 min 10 s | 3 / 3 / 3 | Ninguna | `docs/despliegues/2.4b-rolling.md` |
| Rolling with additional batch | `v4-rollingbatch` | 9 min 19 s | 3 / 4 / 3 | Ninguna | `docs/despliegues/2.4c-rolling-with-additional-batch.md` |
| Immutable | `v5-immutable` | 16 min 53 s | 3 / 6 / 3 | Ninguna | `docs/despliegues/2.4d-immutable.md` |

### Monitor de disponibilidad
Durante las estrategias de despliegue, consulta `/ping` cada segundo y guarda cada respuesta en un CSV (hora UTC, código HTTP, versión, latencia y error). No necesita token ni dependencias adicionales:
```bash
python scripts/monitor_disponibilidad.py http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com docs/despliegues/<estrategia>.csv
```
Se inicia antes de desplegar y se detiene con Ctrl+C cuando el entorno vuelve a *Ok*. Al detenerse imprime el resumen: solicitudes, respuestas no-200 y disponibilidad, la mayor caída (desde la primera respuesta no-200 hasta la siguiente respuesta 200; un corte de conexión cuenta como no-200), las versiones observadas con su primera y última respuesta, y la ventana en la que respondieron dos versiones. Las horas están en UTC; la consola de AWS muestra UTC-5. Opciones: `--intervalo` (segundos entre solicitudes), `--tiempo-espera` y `--solicitudes` (se detiene solo después de N solicitudes).

### Apagar y volver a levantar el entorno de Beanstalk
El entorno y la RDS solo se encienden para trabajar, grabar o sustentar. `scripts/ambiente_aws.py` los apaga y los vuelve a levantar con la CLI de AWS (perfil `blacklist`, región `us-east-2`). Sin `--aplicar` solo muestra el estado y los pasos:
```bash
python scripts/ambiente_aws.py estado
python scripts/ambiente_aws.py apagar [--aplicar]         # plantilla blacklist-entrega-2, snapshot de respaldo, termina el entorno y detiene la RDS
python scripts/ambiente_aws.py eliminar-rds [--aplicar]   # elimina la RDS con snapshot final
python scripts/ambiente_aws.py levantar [--aplicar]       # inicia o restaura la RDS y crea o restaura el entorno con la misma URL
```
Procedimiento y consideraciones en `docs/despliegues/1.7-infraestructura-reproducible.md` (sección 7.5).

## Documento de la entrega en PDF
El documento de cada entrega se escribe en Markdown en `docs/` (`docs/documento-entrega.md` para la Entrega 1 y `docs/documento-entrega-<N>.md` desde la 2) y se convierte en `docs/pdf/Proyecto 1 entrega <N> – Documento.pdf` con `scripts/generar_pdf.py`. El flujo de GitHub Actions `documento-pdf` (`.github/workflows/documento-pdf.yml`) lo ejecuta de dos formas:

| Cómo se inicia | Qué hace |
|---|---|
| A demanda: *Actions* → `documento-pdf` → *Run workflow*, eligiendo la rama, la entrega y, si hace falta, `forzar` | Genera el PDF de la entrega elegida. Desde `dev` o `main` lo genera a partir de `dev`, lo sube a la rama `pdf/entrega-<N>` y abre un PR hacia `dev`; desde otra rama, hace el commit en esa misma rama. Sin `forzar`, no genera nada si el PDF ya está al día con sus fuentes |
| Con cada *push* a `dev` o `main` que cambie un `.md` de `docs/` o el generador | Genera solo el PDF de la entrega en curso (según la fecha) y lo deja como artefacto de la ejecución, sin commit ni PR |

El generador revisa el documento y avisa (código de salida 2, sin detener la generación) si quedan marcas `[PENDIENTE]`, si cita archivos `.md` o tareas del tablero que el lector del PDF no puede abrir, o si la numeración de las figuras tiene saltos. En local necesita la CLI de GitHub (`gh`) con sesión iniciada y Google Chrome, Chromium o Microsoft Edge:
```bash
python scripts/generar_pdf.py --entrega 3                     # deja el PDF en docs/pdf/
python scripts/generar_pdf.py --entrega 3 --salida <carpeta>  # en otra carpeta
python scripts/generar_pdf.py --en-curso                      # número de la entrega en curso
```

## Flujo de trabajo en Git
Hay dos ramas protegidas: `main` (estable) y `dev` (integración). Nadie hace commit directo a ninguna.
- Los cambios salen de una rama de trabajo creada desde `dev` (con prefijo como `feature/`, `fix/` o `docs/`) y entran por un PR hacia `dev`, con una aprobación y fusión con *squash*. Un chequeo (`no-desde-main`) impide PR desde `main`.
- `dev` se promueve a `main` con un PR y *merge commit*. Un chequeo (`solo-desde-dev`) impide que `main` reciba PR de otras ramas.
- Cada commit en `main` inicia el pipeline de CI/CD, que despliega en Fargate si las pruebas pasan. Los PR no inician el pipeline.
- Lo que corre en Fargate sale siempre de `main`.

## Problemas conocidos en Windows
Si el control de aplicaciones bloquea una extensión compilada (error `DLL load failed`), por ejemplo la de SQLAlchemy, instálala sin compilar:
```powershell
$env:DISABLE_SQLALCHEMY_CEXT = "1"
pip install --force-reinstall --no-deps --no-binary sqlalchemy SQLAlchemy==2.1.4
```
La DLL de `psycopg-binary` también puede bloquearse; en ese caso, las pruebas contra PostgreSQL se hacen en Docker o WSL.

## Equipo
Marcelo César Torres, Héctor José Melgarejo, Juan Sebastián Páez y Jean Pierre Betancourt.
