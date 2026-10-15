ENV_DATABASE_URL = "DATABASE_URL"
ENV_JWT_SECRET_KEY = "JWT_SECRET_KEY"
ENV_APP_ENV = "APP_ENV"

APP_ENV_DEVELOPMENT = "development"
APP_ENV_TESTING = "testing"
APP_ENV_PRODUCTION = "production"
DEFAULT_APP_ENV = APP_ENV_DEVELOPMENT

CONFIG_APP_VERSION = "APP_VERSION"
CONFIG_JWT_SECRET_KEY = "JWT_SECRET_KEY"
VERSION_FILE_NAME = "VERSION"
DEFAULT_APP_VERSION = "local"

TOKEN_IDENTITY = "lista-negra"
ENV_PROXY_FIX_X_FOR = "PROXY_FIX_X_FOR"
CONFIG_PROXY_FIX_X_FOR = "PROXY_FIX_X_FOR"
DEFAULT_PROXY_FORWARDED_FOR_HOPS = 1

PING_PATH = "/ping"
BLACKLISTS_PATH = "/blacklists"
EMAIL_URL_VARIABLE = "email"
BLACKLIST_EMAIL_PATH = f"{BLACKLISTS_PATH}/<string:{EMAIL_URL_VARIABLE}>"

FIELD_EMAIL = "email"
FIELD_APP_UUID = "app_uuid"
FIELD_BLOCKED_REASON = "blocked_reason"

BLACKLIST_TABLE_NAME = "blacklist"
EMAIL_MAX_LENGTH = 255
BLOCKED_REASON_MAX_LENGTH = 255
UUID_STRING_LENGTH = 36
IP_ADDRESS_MAX_LENGTH = 45

KEY_MSG = "msg"
KEY_ERRORS = "errors"
KEY_ID = "id"
KEY_IS_BLACKLISTED = "is_blacklisted"
KEY_VERSION = "version"

MESSAGE_EMAIL_ADDED = "Email agregado a la lista negra"
MESSAGE_EMAIL_ALREADY_BLACKLISTED = "El email ya está en la lista negra"
MESSAGE_INVALID_REQUEST = "Datos inválidos"
MESSAGE_MISSING_TOKEN = "Token de autorización ausente"
MESSAGE_INVALID_TOKEN = "Token de autorización inválido"

LOG_CREATE_TABLES_FAILED = "No se pudieron crear las tablas al iniciar la aplicación"
ERROR_INVALID_APP_ENV = "Valor de APP_ENV no válido: '{value}'. Valores válidos: {valid}"
ERROR_INVALID_PROXY_FIX_X_FOR = "Valor de PROXY_FIX_X_FOR no válido: '{value}'. Debe ser un entero mayor o igual a 1"

TEST_DATABASE_URI = "sqlite://"
TEST_JWT_SECRET_KEY = "clave-secreta-solo-para-pruebas-con-longitud-suficiente"
