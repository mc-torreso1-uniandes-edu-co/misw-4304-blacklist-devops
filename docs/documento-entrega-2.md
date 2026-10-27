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
SQLite en memoria, así que no dependen de un servidor de base de datos ni de la red. Antes de configurar
el pipeline, la suite se ejecutó en un entorno limpio con Python 3.13.16, sin red ni base de datos, como
el de CodeBuild: pasaron las 97 pruebas en tres ejecuciones seguidas, archivo por archivo y en orden
inverso.

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
los cambios antes de fusionarlos. El *push* a `main` no excluye ningún archivo, de modo que todo commit en
la rama principal inicia el build; en los pull requests se omiten los cambios que solo tocan documentación
(`docs/**`, `postman/**` o archivos `.md`).

Los dos disparadores están comprobados, sin intervención manual: el *merge* de la promoción `b0e9d03` en
`main` inició la ejecución exitosa 5 segundos después (sección 6), y el pull request #160 de
`test/build-fallido` hacia `dev` inició la ejecución fallida con el evento `PULL_REQUEST_CREATED`
(sección 7). Al abrir el pull request de promoción #156 hacia `main` no se inició ninguna ejecución, sin
causa identificada; el siguiente pull request hacia `main`, el #164, sí inició la ejecución `901438a7`, y el
*push* de su fusión (`625e8c4`) inició otra, la `8d6a7974`. Las dos terminaron con éxito.

El pipeline se creó con la exclusión de rutas también en el *push* a `main`. El 27 de octubre de 2026 se
quitó (versión 2 del pipeline), porque con ella un commit de solo documentación en la rama principal no
iniciaba el build, y el enunciado pide que lo haga cada commit.

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
  nombre al bucket; no se implementó, y para desplegar se extrae el paquete del objeto del build
  (sección 6).

## 3. Enlaces de la entrega

| Recurso | Enlace |
|---|---|
| Repositorio de GitHub | https://github.com/mc-torreso1-uniandes-edu-co/misw-4304-blacklist-devops |
| URL del entorno | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| Documentación publicada del API | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Video de sustentación | [PENDIENTE: tarea 4.5 (#130).] |

Notas aclaratorias:

- **Mismos recursos de la Entrega 1.** El repositorio, el entorno, el workspace de Postman y la
  documentación publicada son los de la Entrega 1; solo el video es nuevo.
- **Repositorio.** Es privado. Si el tutor necesita acceso, debe suministrar su usuario de GitHub para
  agregarlo como colaborador.
- **Entorno.** Según la aclaración del tutor sobre los recursos de AWS, el entorno solo está encendido
  mientras se trabaja y se graba el video: para esta entrega se volvió a provisionar el 23 de octubre de
  2026, con la misma URL, y se apaga después de grabar, así que puede no responder durante la
  calificación. El pipeline de integración continua no depende del entorno.
- **Postman.** El workspace y la documentación publicada son públicos y se abren sin cuenta. Para
  ejecutar las solicitudes hace falta el token, que no se publica en ningún lugar.

## 4. Configuración en AWS

[PENDIENTE: tarea 3.2 (#118).]

## 5. Archivo de construcción y disparo automático

[PENDIENTE: tarea 3.3 (#119).]

## 6. Pipeline exitoso

Cubre el punto 1 del documento (10 %) y respalda el punto 4 de la configuración (15 %): un commit en la
rama principal inició el pipeline sin intervención manual, CodeBuild ejecutó las pruebas y generó el
artefacto. Todas las horas están en UTC-05:00 (Colombia).

### 6.1 Qué se ejecutó

El 24 de octubre de 2026 se fusionó en `main` la promoción de `dev` (pull request #156), que llevó por
primera vez el `buildspec.yml` a la rama principal. El *merge* creó el commit `b0e9d03`, y ese *push* a
`main` disparó la ejecución.

| Dato | Valor |
|---|---|
| Commit en `main` | `b0e9d0397c05ba9b66fdd69161efd3619265f97d` (`b0e9d03`), 11:19:44 |
| Ejecución del pipeline | `ff3146a4-74b7-458f-927e-980fee5eb56d`, **Succeeded** |
| Disparo | *Push* a `main`, 5 segundos después del *merge*, sin intervención manual |
| Duración del pipeline | 38 segundos (11:19:49 a 11:20:27) |
| Build de CodeBuild | Build número 2, `blacklist-devops-ci-build:de0d4f11-4626-44a5-b969-3987f6ac0c91`, **SUCCEEDED**, iniciado por `codepipeline/blacklist-devops-ci-pipeline` |
| Duración del build | 30 segundos (11:19:56 a 11:20:26) |
| Entorno del build | Imagen `aws/codebuild/amazonlinux-x86_64-standard:6.0`, Python **3.13.16** |
| Variable `COMMIT_ID` | El hash completo del commit, entregado por el pipeline |
| Pruebas | **97 aprobadas**, 0 fallidas; cobertura de `app/` del **100 %** |
| Paquete | `app-b0e9d03.zip`, 31 archivos, `VERSION = b0e9d03` |

![Figura 6.1. Commit de la promoción en main (PR #156 fusionado)](capturas/entrega-2/2.6-github-commit-main.png)

![Figura 6.2. Historial del pipeline: la ejecución disparada por el commit b0e9d039 en main, Succeeded en 38 s](capturas/entrega-2/2.6-pipeline-historial.png)

![Figura 6.3. Ejecución del pipeline: etapas Source y Build correctas con el commit b0e9d039](capturas/entrega-2/2.6-pipeline-ejecucion.png)

### 6.2 Fases y pruebas

| Fase del build | Estado | Duración |
|---|---|---|
| `PROVISIONING` | Succeeded | 3 s |
| `DOWNLOAD_SOURCE` | Succeeded | 2 s |
| `INSTALL` | Succeeded | 19 s |
| `BUILD` | Succeeded | 3 s |
| `UPLOAD_ARTIFACTS` | Succeeded | < 1 s |

Las fases `SUBMITTED`, `QUEUED`, `PRE_BUILD`, `POST_BUILD` y `FINALIZING` también terminaron en
*Succeeded*, cada una en menos de un segundo.

Extracto del registro en CloudWatch (`/aws/codebuild/blacklist-devops-ci-build`):

```text
Selecting 'python' runtime version '3.13' based on manual selections...
Running command pip install -r requirements-dev.txt
Phase complete: INSTALL State: SUCCEEDED
Running command python -m pytest -q --cov=app
coverage: platform linux, python 3.13.16-final-0
TOTAL                                                                 290      0   100%
97 passed in 0.77s
Running command python scripts/empaquetar.py "$ETIQUETA" --omitir-pruebas
Generado dist/app-b0e9d03.zip con 31 archivos.
Phase complete: BUILD State: SUCCEEDED
Phase complete: UPLOAD_ARTIFACTS State: SUCCEEDED
```

En esta ejecución el `buildspec.yml` todavía verificaba `COMMIT_ID` antes de las pruebas; el ajuste del
pull request #154 movió esa verificación a después de `pytest`, sin cambiar el resultado.

![Figura 6.4. Fases del build con su duración](capturas/entrega-2/2.6-codebuild-fases.png)

![Figura 6.5. Registro del build: instalación, pruebas y cobertura con Python 3.13.16](capturas/entrega-2/2.7-codebuild-registro-pruebas.png)

![Figura 6.6. Registro del build: contenido del paquete y subida del artefacto](capturas/entrega-2/2.7-codebuild-registro-paquete.png)

### 6.3 Artefacto

CodePipeline guardó la salida del build en el bucket del proyecto como
`blacklist-devops-ci-/BuildArtif/QZJkTHW` (8 191 bytes). Ese objeto contiene el paquete
`app-b0e9d03.zip`; se descargó con la CLI y se revisó:

| Verificación | Resultado |
|---|---|
| Paquete | `app-b0e9d03.zip`, 11 040 bytes, 31 archivos |
| `VERSION` | `b0e9d03`, igual a la etiqueta del commit |
| Contenido en la raíz | `.ebextensions/`, `Procfile`, `VERSION`, `app/`, `application.py` y `requirements.txt` |
| Archivos que no deben ir | Ninguno: sin `tests/`, `docs/`, `scripts/`, `postman/`, `.env` ni bases de datos locales |

![Figura 6.7. Artefacto del build exitoso en el bucket de S3](capturas/entrega-2/2.7-s3-artefacto.png)

Fuera del pipeline, el paquete se extrajo de ese objeto, se subió como versión `b0e9d03` de la
aplicación y se desplegó en `Blacklist-devops-env`: el despliegue tardó 54 segundos, las tres instancias
quedaron con salud *Ok* y `/ping` responde `{"version": "b0e9d03"}`. Contra ese entorno, la colección de
Postman pasó 22 de 22 pruebas.

![Figura 6.8. /ping responde la versión del artefacto desplegado](capturas/entrega-2/2.11-ping-version.png)

### 6.4 Hallazgos

1. **El disparo por *push* funciona.** El pipeline inició 5 segundos después del *merge* en `main`, sin
   intervención manual.
2. **El build es corto y casi todo su tiempo es la instalación.** De 30 segundos, 19 son la fase
   `INSTALL` (`pip install` sin caché); las pruebas y el empaquetado tardan menos de un segundo cada uno.
   Para el tamaño de este proyecto no hace falta caché.
3. **Python 3.13 está disponible en la imagen administrada.** `runtime-versions` resolvió Python
   3.13.16, la misma versión que usa el equipo en local y la plataforma de Beanstalk.
4. **Las pruebas corren sin servicios externos.** El proyecto de CodeBuild no define la cadena de
   conexión a la base ni secretos: la suite usó SQLite en memoria.
5. **El paquete queda dentro del objeto del pipeline.** CodePipeline guarda la salida con un nombre
   generado (`BuildArtif/QZJkTHW`) y la cifra con la clave administrada de S3 (`aws:kms`), aunque el
   cifrado por defecto del bucket es SSE-S3. Para desplegarlo hay que extraer `app-b0e9d03.zip` primero.
6. **La versión en ejecución se puede rastrear hasta el commit.** `/ping` devuelve `b0e9d03`: del
   entorno se llega al build, a la ejecución del pipeline y al pull request que la originó.
7. **Hubo una ejecución fallida previa, esperada.** La ejecución de arranque del pipeline (24 de octubre,
   9:06) falló al descargar el origen porque `main` todavía no tenía `buildspec.yml`. No es la ejecución
   fallida de la sección 7.

## 7. Pipeline fallido

Cubre el punto 2 del documento (10 %): una ejecución del pipeline que falla en la fase de pruebas y no
genera artefacto. Todas las horas están en UTC-05:00 (Colombia).

### 7.1 Qué se provocó

Se creó la rama temporal `test/build-fallido` desde `dev` con una prueba que falla a propósito:
`test_intentional_failure_for_the_pipeline`, en `tests/test_ping.py`, espera un error 500 de `GET /ping`,
que responde 200. El 25 de octubre de 2026 a las 11:47:18 se abrió el pull request #160 hacia `dev`,
titulado *NO FUSIONAR*, solo para disparar el pipeline. A las 12:08:15 se cerró sin fusionar y se
eliminó la rama: la prueba rota nunca llegó a `dev` ni a `main`.

Se usó un pull request y no un build lanzado a mano por dos razones. El proyecto de CodeBuild recibe el
código solo desde el pipeline y su rol no tiene acceso a la conexión de GitHub, así que no puede
construir una rama por sí solo. Además, el punto 2 del documento pide una ejecución fallida del
pipeline, no un build suelto.

| Dato | Valor |
|---|---|
| Commit construido | `c423bff171a52fb5017bbf7fb532c631b954c242` (`c423bff`), en `test/build-fallido` |
| Ejecución del pipeline | `69f3a6bb-3509-4e5d-8a91-38a667a90e64`, **Failed** |
| Disparo | Pull request #160 hacia `dev`, evento `PULL_REQUEST_CREATED`, 5 segundos después de abrirlo |
| Duración del pipeline | 38 segundos (11:47:22 a 11:48:01) |
| Etapas | Source **Succeeded** en 6 segundos; Build **Failed** |
| Build de CodeBuild | Build número 3, `blacklist-devops-ci-build:fc926738-0b5c-4713-ad5b-5dc17ffdf417`, **FAILED**, iniciado por el pipeline |
| Duración del build | 25 segundos (11:47:29 a 11:47:55) |
| Pruebas | 98 recopiladas: **1 fallida y 97 aprobadas**; cobertura de `app/` del 100 % |
| Artefacto | **Ninguno** |

![Figura 7.1. Pull request #160, marcado como no fusionar, con el commit c423bff](capturas/entrega-2/2.9-github-pr.png)

![Figura 7.2. Detalle del disparo: pull request 160, rama de origen, rama de destino y commit](capturas/entrega-2/2.9-pipeline-disparo-pr.png)

![Figura 7.3. Ejecución del pipeline: Source correcta y Build fallida](capturas/entrega-2/2.9-pipeline-ejecucion.png)

### 7.2 Dónde falló y por qué

| Fase del build | Estado | Duración |
|---|---|---|
| `PROVISIONING` | Succeeded | 3 s |
| `DOWNLOAD_SOURCE` | Succeeded | 2 s |
| `INSTALL` | Succeeded | 16 s |
| `BUILD` | **Failed** | 2 s |
| `POST_BUILD` | Succeeded | < 1 s |
| `UPLOAD_ARTIFACTS` | **Failed** | < 1 s |

La etapa Build del pipeline informa el motivo:

```text
Build terminated with state: FAILED. Phase: BUILD, Code: COMMAND_EXECUTION_ERROR,
Message: Error while executing command: python -m pytest -q --cov=app. Reason: exit status 1
```

Extracto del registro en CloudWatch:

```text
Running command python -m pytest -q --cov=app
    def test_intentional_failure_for_the_pipeline(client):
        response = client.get(constants.PING_PATH)
>       assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
E       assert 200 == <HTTPStatus.INTERNAL_SERVER_ERROR: 500>
tests/test_ping.py:62: AssertionError
FAILED tests/test_ping.py::test_intentional_failure_for_the_pipeline - assert...
1 failed, 97 passed in 0.77s
Phase complete: BUILD State: FAILED
Expanding dist/app-*.zip
Phase complete: UPLOAD_ARTIFACTS State: FAILED
Phase context status code: CLIENT_ERROR Message: no matching artifact paths found
```

Como `pytest` termina con código de salida 1, CodeBuild cancela los comandos restantes de la fase
`build`: el script de empaquetado nunca se ejecuta y `dist/app-*.zip` no existe. Por eso la fase
`UPLOAD_ARTIFACTS` falla: no encuentra el paquete declarado en el `buildspec.yml`.

![Figura 7.4. Fases del build: BUILD y UPLOAD_ARTIFACTS en Failed](capturas/entrega-2/2.9-codebuild-fases.png)

![Figura 7.5. Registro del build: 1 failed, 97 passed y no matching artifact paths found](capturas/entrega-2/2.9-registro-fallo.png)

### 7.3 Sin artefacto y sin cambios en las ramas

Después de la ejecución, `blacklist-devops-ci-/BuildArtif/` seguía teniendo un solo objeto: el del build
exitoso del 24 de octubre (`QZJkTHW`). La ubicación de salida que informa el build
(`BuildArtif/krWSeNK`) es solo el destino que reservó el pipeline: el objeto no existe. El único objeto
nuevo en el bucket es el código de origen que la etapa Source deja como entrada del build
(`SourceArti/JdFZGO1`), que no es un paquete de la aplicación.

`dev` y `main` quedaron intactos (`241a309` y `b0e9d03`), porque el pull request se cerró sin fusionar.

![Figura 7.6. Bucket: BuildArtif con un solo objeto, el del build exitoso](capturas/entrega-2/2.9-s3-sin-artefacto.png)

### 7.4 Comparación con la ejecución exitosa

| | Exitosa (sección 6) | Fallida |
|---|---|---|
| Disparo | *Push* a `main` (`b0e9d03`) | Pull request #160 hacia `dev` (`c423bff`) |
| Pipeline | *Succeeded*, 38 s | *Failed*, 38 s |
| Build | Número 2, 30 s | Número 3, 25 s |
| Pruebas | 97 aprobadas | 1 fallida y 97 aprobadas |
| Fase `BUILD` | *Succeeded* | *Failed* |
| Artefacto | `app-b0e9d03.zip` en el bucket | Ninguno |

![Figura 7.7. Historial del pipeline: la ejecución fallida junto a la exitosa](capturas/entrega-2/2.9-pipeline-historial.png)

### 7.5 Hallazgos

1. **El fallo ocurrió en la fase correcta.** El `buildspec.yml` verifica `COMMIT_ID` después de
   `pytest`, así que la causa del fallo es la prueba y no una variable ausente.
2. **El registro identifica la prueba, el archivo y la línea.** El nombre de la prueba deja claro que el
   fallo es deliberado y no una prueba real del contrato rota.
3. **Un cambio con pruebas rotas no produce un paquete desplegable.** El empaquetado nunca se ejecutó y
   no quedó ningún artefacto nuevo, que es el objetivo de la integración continua.
4. **El mismo pipeline da los dos resultados.** Sin cambiar configuración ni lanzar nada a mano, el
   disparador de *push* produjo el build exitoso y el de pull request, el fallido.
5. **El disparador de pull request se comportó distinto en dos intentos.** Con el #160 hacia `dev` se
   inició la ejecución; con el #156 hacia `main`, abierto cuando el pipeline ya existía, no se inició.
   El siguiente pull request hacia `main`, el #164, sí la inició (`901438a7`). La causa del caso del #156
   no está identificada.
6. **La ubicación de salida del build no es un artefacto.** El build informa `BuildArtif/krWSeNK`, pero
   ese objeto no existe porque la subida falló; conviene no confundirlo con un paquete generado.

## 8. Limitaciones y decisiones

[PENDIENTE: tarea 3.6 (#122).]

## 9. Conclusiones

[PENDIENTE: tarea 3.6 (#122).]
