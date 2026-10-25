# Proyecto 1 · Entrega 2: Integración continua del microservicio con AWS CodeBuild y CodePipeline

| | |
|---|---|
| Curso | MISW 4304 · DevOps · Universidad de los Andes (periodo 202615) |
| Entrega | Entrega 2: integración continua (CI) del microservicio |
| Grupo | Blacklist DevOps |
| Integrantes | Marcelo César Torres · Héctor José Melgarejo · Juan Sebastián Páez · Jean Pierre Betancourt |
| Fecha | 1 de noviembre de 2026 |

## Contenido

1. Descripción del microservicio
2. Arquitectura de la integración continua
3. Enlaces de la entrega
4. Configuración en AWS (punto 2 de la configuración, 10 %)
5. Archivo de construcción y disparo automático (puntos 3 y 4 de la configuración, 25 % y 15 %)
6. Pipeline exitoso (punto 1 del documento, 10 %)
7. Pipeline fallido (punto 2 del documento, 10 %)
8. Limitaciones y decisiones
9. Conclusiones

## 1. Descripción del microservicio

El microservicio administra la lista negra global de emails de la organización. Los sistemas internos
lo usan para agregar un email a la lista y para consultar si un email está en ella. Es un único
servicio REST en Python con Flask, protegido con un token Bearer, que persiste la información en
PostgreSQL sobre Amazon RDS y se ejecuta en AWS Elastic Beanstalk.

Es el mismo microservicio de la Entrega 1: su contrato no cambia. Esta entrega agrega las pruebas
unitarias por endpoint y el pipeline que las ejecuta y genera el artefacto desplegable en cada cambio.

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| POST | `/blacklists` | Agrega un email a la lista negra. Cuerpo: `email`, `app_uuid` (UUID obligatorio) y `blocked_reason` (opcional, máximo 255 caracteres). Guarda además la IP de origen y la fecha y hora de la solicitud | 201 con `msg` e `id`; 400 con `msg` y `errors`; 401 sin token o con token inválido; 409 si el email ya está |
| GET | `/blacklists/<string:email>` | Indica si el email está en la lista y el motivo | 200 con `is_blacklisted` y `blocked_reason`; 401 sin token o con token inválido |
| GET | `/ping` | Health check del balanceador. No requiere token ni consulta la base | 200 con `{"version": ...}` |

Stack: Python 3.13, Flask 3.1.3, Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.4), Flask-RESTful 0.3.10,
Flask-Marshmallow 1.5.0 (marshmallow 4.3.1), Flask-JWT-Extended 4.7.4, Werkzeug 3.1.9, PostgreSQL 16
con el driver psycopg 3 y Gunicorn 26.2.0 como servidor WSGI. Las pruebas usan pytest 9.1.1 y
pytest-cov 7.1.0.

El código está organizado por capas: `domain` (entidad, validación del email, errores y reloj),
`application` (casos de uso *agregar* y *consultar*, y el puerto del repositorio) e `infrastructure`
(recursos HTTP, esquema de validación, autenticación y repositorio SQLAlchemy). El email se normaliza a
minúsculas y sin espacios al guardar y al consultar.

**Pruebas unitarias.** La suite tiene 97 pruebas, con 100 % de cobertura del paquete `app`. Cada
endpoint tiene sus escenarios: respuestas correctas, validaciones, duplicados, normalización del email,
las cinco variantes de credencial inválida (401) y que `/ping` no consulta la base. Las pruebas usan
SQLite en memoria, así que no dependen de un servidor de base de datos ni de la red. La matriz de
escenarios por endpoint, con la prueba que cubre cada uno, está en
`docs/pruebas/2.1-escenarios-por-endpoint.md`, y la verificación de que la suite corre sin cambios en un
entorno limpio como el de CodeBuild, en `docs/pruebas/2.4-pruebas-ci.md`.

## 2. Arquitectura de la integración continua

El pipeline valida cada cambio y genera el artefacto desplegable. Ejecuta las pruebas unitarias en AWS
CodeBuild y, si todas pasan, deja el paquete de la aplicación en Amazon S3. **No despliega**: la carga
del artefacto en Elastic Beanstalk es un paso manual, porque la entrega excluye el despliegue
automatizado (CD).

```
Desarrollador
     │  push a main · pull request hacia dev o main
     ▼
GitHub · repositorio misw-4304-blacklist-devops
     │  conexión blacklist-devops-github (AWS CodeConnections, sin tokens)
     ▼
AWS CodePipeline V2 · blacklist-devops-ci-pipeline
     │  Etapa Origen: código del commit (ZIP) y su identificador (CommitId)
     ▼
     │  Etapa Construcción
     ▼
AWS CodeBuild · blacklist-devops-ci-build (buildspec.yml)
     │  1. Instala las dependencias (requirements-dev.txt)
     │  2. Ejecuta las pruebas con pytest ──── una falla ──▶ build Failed, sin artefacto
     │  3. Empaqueta la aplicación: app-<commit>.zip
     │  Registros de cada fase en Amazon CloudWatch Logs
     ▼
Amazon S3 · blacklist-devops-ci-artifacts-253041091381
     │  almacén del pipeline: objeto BuildArtif/<id> que contiene app-<commit>.zip
     ┊
     ┊  despliegue manual, fuera del pipeline: se extrae el paquete y se sube a Beanstalk
     ▼
AWS Elastic Beanstalk · Blacklist-devops-env
```

| Pieza | Recurso | Qué hace |
|---|---|---|
| Repositorio | GitHub, `misw-4304-blacklist-devops` | Guarda el código, las pruebas y el `buildspec.yml`. `main` es la rama estable y `dev` la de integración; las dos están protegidas: solo cambian por pull request aprobado |
| Conexión | `blacklist-devops-github` (AWS CodeConnections) | Autoriza a AWS a leer el repositorio mediante una aplicación de GitHub limitada a este repositorio, sin tokens personales ni llaves guardadas |
| Pipeline | AWS CodePipeline V2, `blacklist-devops-ci-pipeline` | Detecta los cambios y orquesta las dos etapas: Origen (obtiene el código) y Construcción (lanza CodeBuild). Modo de ejecución `QUEUED`: si llegan varios cambios, se ejecutan en orden y ninguno reemplaza a otro |
| Construcción | AWS CodeBuild, `blacklist-devops-ci-build` | Ejecuta las fases del `buildspec.yml`: instala las dependencias, corre las pruebas y genera el paquete. Si una prueba falla, el build termina en *Failed* y no se genera artefacto |
| Artefacto | Amazon S3, `blacklist-devops-ci-artifacts-253041091381` | Bucket privado, con el acceso público bloqueado y cifrado SSE-S3, que también es el almacén de artefactos del pipeline. CodePipeline guarda la salida del build como un objeto con nombre generado (`blacklist-devops-ci-/BuildArtif/<id>`) que contiene el paquete `app-<commit>.zip`, identificado con los siete primeros caracteres del commit |
| Permisos | Roles de IAM `blacklist-devops-codebuild-role` y `blacklist-devops-codepipeline-role` | Cada servicio actúa con su propio rol y permisos mínimos sobre los recursos del proyecto. Ninguno tiene permisos de administrador ni usa llaves de acceso |
| Registros | Amazon CloudWatch Logs | Guarda la salida de cada build, con el resultado de las pruebas |
| Despliegue | AWS Elastic Beanstalk, `Blacklist-devops-env` | Fuera del pipeline: una persona descarga el objeto del build, extrae `app-<commit>.zip`, lo sube como versión de la aplicación y la despliega en el entorno de la Entrega 1 |

**Cuándo se ejecuta.** El pipeline se dispara con cada *push* a `main` (el commit en la rama principal
que pide el enunciado) y con cada pull request abierto o actualizado hacia `dev` o `main`, para validar
los cambios antes de fusionarlos. Los cambios que solo tocan documentación (`docs/**`, `postman/**` o
archivos `.md`) no lo disparan.

El disparo por *push* a `main` está comprobado: el *merge* de la promoción `b0e9d03` inició la ejecución
5 segundos después, sin intervención manual (sección 6). El disparador de pull requests está configurado,
pero todavía no ha iniciado ninguna ejecución; su revisión está en la tarea 1.11 (#103), junto con la
propuesta de quitar la exclusión de rutas en el *push* a `main`. Si la configuración cambia, se actualiza
este párrafo.

**Flujo de una ejecución:**

1. Un desarrollador fusiona un cambio en `main` o abre un pull request.
2. CodePipeline recibe el evento por la conexión de GitHub y la etapa Origen obtiene el código de ese
   commit.
3. La etapa Construcción lanza CodeBuild, que instala las dependencias y ejecuta las pruebas.
4. Si todas las pruebas pasan, CodeBuild genera `app-<commit>.zip` y CodePipeline lo guarda en el bucket
   de S3, dentro del objeto de salida del build. Si una falla, el build y la ejecución del pipeline
   terminan en *Failed* y no se genera artefacto.
5. Fuera del pipeline, el equipo extrae el paquete del último build exitoso de `main` y lo despliega
   manualmente en Beanstalk.

**Decisiones de la arquitectura:**

- **CodePipeline con CodeBuild como etapa,** en lugar de un webhook directo de CodeBuild: centraliza en
  un solo lugar el origen de GitHub y la ejecución de CodeBuild, separa la obtención del código de la
  construcción y deja un historial de ejecuciones por etapa. El acceso a GitHub es por la conexión, sin
  tokens personales ni llaves guardadas.
- **Pruebas sin servidor de base de datos.** El enunciado permite usar mocks o levantar un motor de base
  de datos dentro del CI; el equipo eligió SQLite en memoria, que no requiere configurar servicios
  adicionales en CodeBuild. El proyecto de CodeBuild no define la cadena de conexión a la base ni
  secretos.
- **Artefacto en S3,** como paquete `.zip` listo para crear una versión de la aplicación en Beanstalk
  (el enunciado permite un repositorio o una imagen de contenedor; no se usan contenedores). El
  `buildspec.yml` lo declara en su sección `artifacts` y CodePipeline lo publica en su almacén, sin
  llamadas a la CLI de AWS desde el build. El diseño inicial proponía copiar además el paquete con su
  nombre al bucket; esa opción sigue en revisión en la tarea 1.11 (#103).

El diseño completo, con los permisos de cada recurso, está en `docs/ci/1.1-diseno-pipeline.md`; la
configuración real de cada recurso, en `docs/ci/1.7-proyecto-codebuild.md` y `docs/ci/1.11-pipeline.md`.

## 3. Enlaces de la entrega

[PENDIENTE: tarea 3.6 (#122).]

## 4. Configuración en AWS

[PENDIENTE: tarea 3.2 (#118).]

## 5. Archivo de construcción y disparo automático

[PENDIENTE: tarea 3.3 (#119).]

## 6. Pipeline exitoso

[PENDIENTE: tarea 3.4 (#120).]

## 7. Pipeline fallido

[PENDIENTE: tarea 3.5 (#121).]

## 8. Limitaciones y decisiones

[PENDIENTE: tarea 3.6 (#122).]

## 9. Conclusiones

[PENDIENTE: tarea 3.6 (#122).]
