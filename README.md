# misw-4304-blacklist-devops
Microservicio de lista negra global de emails – Proyecto 1, Entrega 1 (MISW 4304)

## Requisitos
- Python 3.11
- PostgreSQL (o SQLite para pruebas locales)

## Crear el entorno

Windows (PowerShell):
```powershell
py -3.11 -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
```

Linux / macOS:
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuración
Copia `.env.example` a `.env` (obligatorio, sin él la aplicación no arranca) y completa los valores:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión, por ejemplo `postgresql://usuario:clave@host:5432/base` o `sqlite:///local.db` |
| `STATIC_BEARER_TOKEN` | Token que deben enviar los clientes en el encabezado `Authorization: Bearer <token>` |

Las tablas se crean automáticamente al iniciar la aplicación.

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

El API queda en `http://127.0.0.1:5000`.

## Endpoints
Todos requieren el encabezado `Authorization: Bearer <token>`.

| Método | Ruta | Respuestas |
|---|---|---|
| POST | `/blacklists` | 201 creado, 400 solicitud inválida, 401 sin autorización, 409 email ya registrado |
| GET | `/blacklists/<email>` | 200 con `is_blacklisted` y `blocked_reason`, 401 sin autorización |

Cuerpo del POST:
```json
{
  "email": "cliente@example.com",
  "app_uuid": "0b8f6a52-6f0c-4c1e-9a8e-5f1d2c3b4a5e",
  "blocked_reason": "Motivo opcional de máximo 255 caracteres"
}
```

## Pruebas
```bash
pytest
```
