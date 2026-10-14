# Microservicio de Lista Negra Global de Emails
Proyecto de DevOps - MISW - 202615. Grupo 20: Blacklist DevOps

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

El email se normaliza a minúsculas y sin espacios al guardar y al consultar.

Cuerpo del POST:
```json
{
  "email": "cliente@example.com",
  "app_uuid": "0b8f6a52-6f0c-4c1e-9a8e-5f1d2c3b4a5e",
  "blocked_reason": "Motivo opcional de máximo 255 caracteres"
}
```

## Pruebas
No necesitan `.env` ni base de datos: usan SQLite en memoria.
```bash
python -m pytest -q
python -m pytest --cov=app
```

Para correr la misma suite contra PostgreSQL, define `DATABASE_URL` antes de ejecutarla.

## Postman
La colección y los environments (`blacklist-local` y `blacklist-aws`) están en `postman/`. Importa los tres archivos, completa `token` y `base_url` en el environment y ejecuta los escenarios en orden.

## Problemas conocidos en Windows
Si el control de aplicaciones bloquea una extensión compilada (error `DLL load failed`), por ejemplo la de SQLAlchemy, instálala sin compilar:
```powershell
$env:DISABLE_SQLALCHEMY_CEXT = "1"
pip install --force-reinstall --no-deps --no-binary sqlalchemy SQLAlchemy==2.1.4
```
La DLL de `psycopg-binary` también puede bloquearse; en ese caso, las pruebas contra PostgreSQL se hacen en Docker o WSL.
