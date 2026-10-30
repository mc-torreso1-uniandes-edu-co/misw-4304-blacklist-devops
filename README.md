# Microservicio de Lista Negra Global de Emails
Proyecto de DevOps - MISW - 202615. Grupo Blacklist DevOps

Microservicio REST en Python y Flask para que los sistemas internos de una empresa agreguen emails a una lista negra global y consulten si un email está en ella. Corre en AWS Elastic Beanstalk con PostgreSQL en Amazon RDS (región `us-east-2`). Cada commit en `main` y cada pull request hacia `dev` o `main` pasan por un pipeline de integración continua (AWS CodePipeline y CodeBuild) que ejecuta las pruebas y genera el paquete de la aplicación; el despliegue en Beanstalk sigue siendo manual.

## Enlaces
| Recurso | Enlace |
|---|---|
| Documentación del API (Postman) | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| Entorno en AWS | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com (se enciende solo mientras se trabaja; `/ping` indica si responde) |
| Pipeline de integración continua | Consola de AWS, región `us-east-2`: CodePipeline `blacklist-devops-ci-pipeline` y CodeBuild `blacklist-devops-ci-build` |

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
scripts/              # generar_token.py, empaquetar.py, monitor_disponibilidad.py y ambiente_aws.py
tests/                # pytest
postman/              # colección y environments (JSON v2.1)
docs/                 # enunciados, rúbricas y aclaraciones del curso, documentos de cada entrega y:
  ci/                 #   diseño, configuración y ejecuciones del pipeline de integración continua
  pruebas/            #   escenarios por endpoint y resultados de las pruebas
  despliegues/        #   infraestructura reproducible y mediciones de las estrategias de despliegue
  capturas/           #   capturas de las entregas (desde la Entrega 2, en capturas/entrega-<N>/)
.ebextensions/        # configuración de Beanstalk (health check en /ping)
.github/              # chequeos de las ramas
buildspec.yml         # archivo de construcción de CodeBuild: pruebas y paquete
requirements.txt      # dependencias de la aplicación
requirements-dev.txt  # las de la aplicación más pytest y pytest-cov
.python-version       # 3.13.16
.env.example          # variables de entorno locales, sin valores reales
Procfile              # web: gunicorn --bind :8000 --workers 2 application:application
VERSION               # etiqueta de versión que devuelve /ping (el empaquetado la escribe)
```

## Requisitos
- Python 3.13.16 (la versión de `.python-version`). Se instala desde python.org o con `uv python install 3.13.16`
- PostgreSQL (o SQLite para pruebas locales)

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

El segundo comando es el mismo que ejecuta el pipeline. El resultado esperado es `127 passed` y una cobertura del 100 % sobre `app/`. Para correr la misma suite contra PostgreSQL, define `DATABASE_URL` antes de ejecutarla.

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `tests/test_blacklist_api.py` | 23 | `POST /blacklists` y `GET /blacklists/<email>` |
| `tests/test_authentication.py` | 10 | 401 en los dos endpoints protegidos, cinco variantes de credencial en cada uno |
| `tests/test_ping.py` | 6 | `GET /ping` y lectura del archivo `VERSION` |
| `tests/test_configuration.py` | 16 | Configuración por ambiente |
| `tests/test_empaquetar.py` | 15 | Script de empaquetado |
| `tests/test_monitor_disponibilidad.py` | 25 | Script de monitoreo del despliegue |
| `tests/test_ambiente_aws.py` | 30 | Script para apagar y volver a levantar el ambiente |
| `tests/test_app_creation.py` | 1 | Creación de la aplicación |
| `tests/test_domain.py` | 1 | Entidad de dominio |

Escenarios por endpoint (cada respuesta del contrato tiene al menos una prueba):

| Endpoint | Escenarios |
|---|---|
| `POST /blacklists` | **201**: alta correcta con `msg` e `id`, sin `blocked_reason` o con él nulo, email guardado normalizado, IP del cliente desde `X-Forwarded-For`, fecha de creación, motivo de 255 caracteres. **400**: email o `app_uuid` inválidos, motivo de 256 caracteres, campos obligatorios faltantes, cuerpo que no es JSON o JSON mal formado. **409**: email duplicado, también con otras mayúsculas, con espacios alrededor o por una solicitud concurrente. **401**: sin token, token malformado, esquema no soportado, `Bearer` sin token y token firmado con otra clave |
| `GET /blacklists/<email>` | **200**: email en la lista con su motivo, email que no está (`is_blacklisted` falso y motivo nulo), mayúsculas y espacios normalizados. **401**: las mismas cinco variantes de credencial |
| `GET /ping` | **200** sin token y con el cuerpo exacto `{"version": ...}`, sin consultar la base; la versión sale de `VERSION`, con un valor por defecto si falta o está vacío |

El detalle prueba por prueba está en `docs/pruebas/2.1-escenarios-por-endpoint.md`.

## Integración continua
Un pipeline de AWS CodePipeline (V2) con dos etapas: **Source** obtiene el código de GitHub mediante la conexión `blacklist-devops-github`, autorizada solo para este repositorio, y **Build** lo construye en el proyecto de CodeBuild `blacklist-devops-ci-build`. No tiene etapa de despliegue.

**Cuándo se ejecuta:**
- Con cada *push* a `main`, es decir, cada commit que llega a la rama principal, sin excluir ningún archivo.
- Con cada pull request abierto o actualizado hacia `dev` o `main`. En los pull requests se omiten los cambios que solo tocan `docs/**`, `postman/**` o archivos `.md`.
- Las ejecuciones se encolan (modo `QUEUED`): una no reemplaza a otra en curso.

**Qué hace el build** (`buildspec.yml`, imagen `amazonlinux-x86_64-standard:6.0` con Python 3.13):
1. `install`: `pyenv install --skip-existing` con la versión de `.python-version` (3.13.16; la imagen trae otro parche de 3.13 y lo compila si falta), luego `pip install -r requirements-dev.txt`.
2. `build`: `python -m pytest -q --cov=app`. Si una prueba falla, el build termina en *Failed* y no se genera el paquete.
3. Si las pruebas pasan, `scripts/empaquetar.py` genera `dist/app-<commit>.zip`, con los siete primeros caracteres del commit (variable `COMMIT_ID`, que le pasa el pipeline) como etiqueta de versión.
4. `artifacts`: CodePipeline guarda el paquete en el bucket `blacklist-devops-ci-artifacts-253041091381`, dentro de un objeto con nombre generado (`blacklist-devops-ci-/BuildArtif/<id>`).

**Dónde ver los resultados** (consola de AWS, región `us-east-2`):
| Qué | Dónde |
|---|---|
| Historial de ejecuciones, con el commit y el disparador de cada una | CodePipeline → `blacklist-devops-ci-pipeline` → *Executions* |
| Fases del build, su duración y el registro con el resultado de `pytest` | CodeBuild → `blacklist-devops-ci-build` → *Build history* (el registro también queda en CloudWatch Logs) |
| Paquete generado | S3 → `blacklist-devops-ci-artifacts-253041091381` → `blacklist-devops-ci-/BuildArtif/` |

El build no despliega. Para desplegar un paquete del pipeline, se descarga el objeto de `BuildArtif/`, se extrae `app-<commit>.zip` y se carga en Beanstalk como se explica en "Empaquetar y desplegar en AWS"; `/ping` responde entonces el commit. Diseño, configuración y ejecuciones documentadas: `docs/ci/` (procedimiento completo en `docs/ci/1.7-codebuild.md`, ejecución exitosa en `docs/ci/2.2-pipeline-exitoso.md`, fallida en `docs/ci/2.3-pipeline-fallido.md` y despliegue manual del artefacto en `docs/ci/2.11-despliegue-manual.md`).

## Postman
La colección y los environments (`blacklist-local` y `blacklist-aws`) están en `postman/`. Importa los tres archivos, completa `token` en el environment y ejecuta los escenarios en orden. `base_url` ya apunta a `http://localhost:5000` (local) y a `http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com` (AWS). El token se carga solo como valor actual, nunca como valor inicial: el workspace es público. Los resultados contra AWS están en `docs/pruebas/2.3b-pruebas-aws.md`.

## Empaquetar y desplegar en AWS
El despliegue es manual. El pipeline genera el paquete de cada commit (ver "Integración continua"); para generar uno en local:
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

## Estrategias de despliegue
Las cuatro estrategias se ejecutaron sobre el mismo entorno, con Auto Scaling de 3 a 6 instancias `t3.micro`. Cada paquete tiene el mismo código y solo cambia `VERSION`.

| Estrategia | Versión | Tiempo | Instancias (antes / máx. / después) | Caída observada | Detalle |
|---|---|---|---|---|---|
| All at once | `v2-allatonce` | 0 min 21 s | 3 / 3 / 3 | 5 s con respuestas `502` | `docs/despliegues/2.4a-all-at-once.md` |
| Rolling | `v3-rolling` | 8 min 10 s | 3 / 3 / 3 | Ninguna | `docs/despliegues/2.4b-rolling.md` |
| Rolling with additional batch | `v4-rollingbatch` | 9 min 19 s | 3 / 4 / 3 | Ninguna | `docs/despliegues/2.4c-rolling-with-additional-batch.md` |
| Immutable | `v5-immutable` | 16 min 53 s | 3 / 6 / 3 | Ninguna | `docs/despliegues/2.4d-immutable.md` |

## Monitor de disponibilidad
Durante las estrategias de despliegue, consulta `/ping` cada segundo y guarda cada respuesta en un CSV (hora UTC, código HTTP, versión, latencia y error). No necesita token ni dependencias adicionales:
```bash
python scripts/monitor_disponibilidad.py http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com docs/despliegues/<estrategia>.csv
```
Se inicia antes de desplegar y se detiene con Ctrl+C cuando el entorno vuelve a *Ok*. Al detenerse imprime el resumen: solicitudes, respuestas no-200 y disponibilidad, la mayor caída (desde la primera respuesta no-200 hasta la siguiente respuesta 200; un corte de conexión cuenta como no-200), las versiones observadas con su primera y última respuesta, y la ventana en la que respondieron dos versiones. Las horas están en UTC; la consola de AWS muestra UTC-5. Opciones: `--intervalo` (segundos entre solicitudes), `--tiempo-espera` y `--solicitudes` (se detiene solo después de N solicitudes).

## Apagar y volver a levantar el ambiente
El entorno y la RDS solo se encienden para trabajar, grabar o sustentar. `scripts/ambiente_aws.py` los apaga y los vuelve a levantar con la CLI de AWS (perfil `blacklist`, región `us-east-2`). Sin `--aplicar` solo muestra el estado y los pasos:
```bash
python scripts/ambiente_aws.py estado
python scripts/ambiente_aws.py apagar [--aplicar]         # plantilla blacklist-entrega-2, snapshot de respaldo, termina el entorno y detiene la RDS
python scripts/ambiente_aws.py eliminar-rds [--aplicar]   # elimina la RDS con snapshot final
python scripts/ambiente_aws.py levantar [--aplicar]       # inicia o restaura la RDS y crea el entorno con la misma URL
```
Procedimiento y consideraciones en `docs/despliegues/1.7-infraestructura-reproducible.md` (sección 7.5).

## Flujo de trabajo en Git
Hay dos ramas protegidas: `main` (estable) y `dev` (integración). Nadie hace commit directo a ninguna.
- Los cambios salen de una rama de trabajo creada desde `dev` (con prefijo como `feature/`, `fix/` o `docs/`) y entran por un PR hacia `dev`, con una aprobación y fusión con *squash*. Un chequeo (`no-desde-main`) impide PR desde `main`.
- `dev` se promueve a `main` con un PR y *merge commit*. Un chequeo (`solo-desde-dev`) impide que `main` reciba PR de otras ramas.
- Cada commit en `main` y los PR hacia `dev` o `main` (salvo los que solo cambian documentación) inician el pipeline de integración continua.
- Los paquetes que se despliegan salen de `main`.

## Problemas conocidos en Windows
Si el control de aplicaciones bloquea una extensión compilada (error `DLL load failed`), por ejemplo la de SQLAlchemy, instálala sin compilar:
```powershell
$env:DISABLE_SQLALCHEMY_CEXT = "1"
pip install --force-reinstall --no-deps --no-binary sqlalchemy SQLAlchemy==2.1.4
```
La DLL de `psycopg-binary` también puede bloquearse; en ese caso, las pruebas contra PostgreSQL se hacen en Docker o WSL.

## Equipo
Marcelo César Torres, Héctor José Melgarejo, Juan Sebastián Páez y Jean Pierre Betancourt.
