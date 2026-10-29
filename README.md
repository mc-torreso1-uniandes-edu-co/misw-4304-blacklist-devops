# Microservicio de Lista Negra Global de Emails
Proyecto de DevOps - MISW - 202615. Grupo Blacklist DevOps

Microservicio REST en Python y Flask para que los sistemas internos de una empresa agreguen emails a una lista negra global y consulten si un email está en ella. Corre en AWS Elastic Beanstalk con PostgreSQL en Amazon RDS (región `us-east-2`). Cada commit en `main` inicia un pipeline de integración continua (AWS CodePipeline y AWS CodeBuild) que ejecuta las pruebas y genera el paquete de la aplicación; el despliegue sigue siendo manual, sin CD.

## Enlaces
| Recurso | Enlace |
|---|---|
| Documentación del API (Postman) | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| Entorno en AWS | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com (se enciende solo mientras se trabaja; `/ping` indica si responde) |

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
scripts/              # generar_token.py, empaquetar.py y monitor_disponibilidad.py
tests/                # pytest, con SQLite en memoria
postman/              # colección y environments (JSON v2.1)
docs/                 # enunciados y rúbricas del curso, documentos de las entregas y guion del video
  ci/                 #   diseño, decisiones y configuración del pipeline, y ejecuciones exitosa y fallida
  pruebas/            #   escenarios por endpoint y resultados de las pruebas
  despliegues/        #   infraestructura reproducible y mediciones de las estrategias de despliegue
  capturas/           #   capturas de la consola de AWS (las de la entrega 2 en entrega-2/)
.ebextensions/        # configuración de Beanstalk (health check en /ping)
.github/              # chequeos de las ramas
buildspec.yml         # build de CodeBuild: instala, ejecuta las pruebas y genera el paquete
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
No necesitan `.env` ni base de datos: usan SQLite en memoria. Con el entorno creado (ver "Crear el entorno"):
```bash
python -m pytest -q
python -m pytest --cov=app
```

Resultado esperado: `97 passed` y cobertura de 100 % sobre `app/`. Para correr la misma suite contra PostgreSQL, define `DATABASE_URL` antes de ejecutarla.

Cada endpoint tiene sus propias pruebas; la matriz completa de escenarios está en `docs/pruebas/2.1-escenarios-por-endpoint.md`.

| Endpoint | Archivo | Escenarios |
|---|---|---|
| `POST /blacklists` | `tests/test_blacklist_api.py`, `tests/test_authentication.py` | 201 con `msg` e `id` (con y sin `blocked_reason`, email normalizado, IP de `X-Forwarded-For` y fecha guardadas); 409 por email duplicado, también con otras mayúsculas, espacios o una solicitud concurrente; 400 por email o `app_uuid` inválido, motivo de más de 255 caracteres, campos faltantes, cuerpo que no es JSON o JSON mal formado; 401 con cinco variantes de credencial inválida |
| `GET /blacklists/<email>` | `tests/test_blacklist_api.py`, `tests/test_authentication.py` | 200 con `is_blacklisted` verdadero y el motivo, o falso y motivo nulo; consulta sin distinguir mayúsculas ni espacios alrededor; 401 con las mismas cinco variantes (nunca 422) |
| `GET /ping` | `tests/test_ping.py` | 200 sin token, cuerpo solo con `version`, versión leída de `VERSION` (con valor por defecto si falta) y sin consultar la base de datos |

El resto de la suite cubre la configuración por ambiente (`test_configuration.py`), la creación de la aplicación y la entidad de dominio, y los scripts de empaquetado y de monitoreo.

## Integración continua
El pipeline `blacklist-devops-ci-pipeline` (AWS CodePipeline V2, `us-east-2`) tiene dos etapas: el origen en este repositorio de GitHub, por una conexión sin tokens, y el build en el proyecto de CodeBuild `blacklist-devops-ci-build`. No tiene etapa de despliegue.

**Disparo.** Se inicia solo con:
- cada *push* a `main`, sea cual sea el archivo que cambie (cada promoción de `dev` a `main` es un *push*);
- cada PR hacia `dev` o `main` al abrirse o actualizarse, salvo que solo cambie `docs/**`, `postman/**` o archivos `*.md`.

**Fases del build** (`buildspec.yml`, imagen Amazon Linux 2023 con Python 3.13):

| Fase | Qué hace | Si falla |
|---|---|---|
| `INSTALL` | `pip install -r requirements-dev.txt` | El build termina en *Failed* |
| `BUILD` | `python -m pytest -q --cov=app`; si las pruebas pasan, `python scripts/empaquetar.py <commit> --omitir-pruebas` genera `dist/app-<commit>.zip` (la etiqueta son los 7 primeros caracteres del commit) | Una prueba fallida detiene el build y no se genera el paquete |
| `UPLOAD_ARTIFACTS` | Entrega el paquete al pipeline | — |

**Artefacto.** CodePipeline guarda el paquete en el bucket `blacklist-devops-ci-artifacts-253041091381`, dentro de la carpeta del pipeline y como un objeto propio que contiene `app-<commit>.zip`. Ese `.zip` es el que se carga en Beanstalk; el procedimiento está en `docs/ci/2.11-despliegue-manual.md`.

**Dónde ver los resultados.** En la consola de AWS (`us-east-2`): CodePipeline › `blacklist-devops-ci-pipeline` › Historial de ejecuciones, para ver qué commit inició cada ejecución; y CodeBuild › `blacklist-devops-ci-build` › Historial de compilaciones, para ver las fases, y el registro con la línea `97 passed`. Los registros también quedan en CloudWatch Logs, grupo `/aws/codebuild/blacklist-devops-ci-build`.

Antes de abrir un PR conviene ejecutar `python -m pytest -q` en local: es la misma suite que corre el build.

La configuración del pipeline está en `docs/ci/` (de `1.1-diseno-pipeline.md` a `1.11-pipeline.md`). Las ejecuciones exitosa y fallida están documentadas en `docs/ci/2.2-pipeline-exitoso.md` y `docs/ci/2.3-pipeline-fallido.md`.

## Postman
La colección y los environments (`blacklist-local` y `blacklist-aws`) están en `postman/`. Importa los tres archivos, completa `token` en el environment y ejecuta los escenarios en orden. `base_url` ya apunta a `http://localhost:5000` (local) y a `http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com` (AWS). El token se carga solo como valor actual, nunca como valor inicial: el workspace es público. Los resultados contra AWS están en `docs/pruebas/2.3b-pruebas-aws.md` (entrega 1) y `docs/pruebas/2.12-postman-aws.md` (entrega 2, versión desplegada desde el artefacto del pipeline).

## Empaquetar y desplegar en AWS
El despliegue es manual. El paquete se toma del artefacto del pipeline (ver "Integración continua") o se genera en local:
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

## Flujo de trabajo en Git
Hay dos ramas protegidas: `main` (estable) y `dev` (integración). Nadie hace commit directo a ninguna.
- Los cambios salen de una rama de trabajo creada desde `dev` (con prefijo como `feature/`, `fix/` o `docs/`) y entran por un PR hacia `dev`, con una aprobación y fusión con *squash*. Un chequeo (`no-desde-main`) impide PR desde `main`.
- `dev` se promueve a `main` con un PR y *merge commit*. Un chequeo (`solo-desde-dev`) impide que `main` reciba PR de otras ramas.
- Los PR y los *push* a `main` inician el pipeline de integración continua (ver "Integración continua").
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
