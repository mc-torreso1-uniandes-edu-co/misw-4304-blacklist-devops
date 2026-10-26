# Guion del video de sustentación · Entrega 2

Tarea 4.1 (#126) · Épica E2 · Cierre

| Dato | Valor |
|---|---|
| Duración | **9:00** (límite del curso: 10:00) |
| Estructura | 4 partes seguidas, una por integrante, de 2:15 cada una |
| Grabación | Martes 27 de octubre de 2026. Cada integrante graba su parte; Jean Pierre integra y publica (tarea 4.5) |

Regla del enunciado (`docs/entrega-2-integracion-continua.md`): el video muestra en vivo la consola de AWS,
el repositorio, los escenarios de prueba de los endpoints y la configuración del proceso de integración
continua en GitHub y AWS, sin dejar dudas de qué requisito se cumplió. Mostrar o leer solo el PDF no cuenta
como sustentación, y lo que pase del minuto 10 no se califica.

| Parte | Integrante | Tiempo | Tema |
|---|---|---|---|
| 1 | Marcelo Torres | 0:00–2:15 | Presentación y escenarios de prueba de la API |
| 2 | Héctor Melgarejo | 2:15–4:30 | Archivo de construcción, proyecto de CodeBuild y pipeline |
| 3 | Juan Sebastián Páez | 4:30–6:45 | Pipeline exitoso, artefacto y despliegue manual |
| 4 | Jean Pierre Betancourt | 6:45–9:00 | Pipeline fallido y cierre |

El reparto de las partes 2 a 4 sigue a quien construyó cada pieza. Las grabaciones del tablero (4.2 a 4.4) se
ajustan a este guion.

## 1. Marcelo Torres · 0:00–2:15 · Presentación y pruebas

Rúbrica: punto 1 de la configuración, pruebas por endpoint (30 %); aplicación en Beanstalk vía Postman.

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 0:00–0:25 | GitHub | Repositorio en `main`, README | Hola, somos el grupo Blacklist DevOps: Marcelo Torres, Héctor Melgarejo, Juan Sebastián Páez y Jean Pierre Betancourt. En esta entrega agregamos integración continua al microservicio de lista negra de emails: cada cambio en la rama principal ejecuta las pruebas en AWS CodeBuild y genera el paquete desplegable, sin despliegue automático. Yo soy Marcelo y voy a mostrar las pruebas de la API. |
| 1.1 | 0:25–1:00 | GitHub, `tests/` | `test_blacklist_api.py` (POST 201, 400, 409; GET con email que está, que no está, mayúsculas y espacios), `test_authentication.py` (401 parametrizados), `test_ping.py` (sin token, solo la versión, sin consultar la base) y `docs/pruebas/2.1-escenarios-por-endpoint.md` | Cada endpoint tiene escenarios para todas las respuestas del contrato. En POST probamos el alta con IP y fecha guardadas, el motivo opcional, los duplicados, los formatos inválidos y la falta de token. En GET, un email que está, uno que no está y la normalización. En /ping, que responde sin token, solo con la versión y sin tocar la base. La matriz relaciona cada respuesta con su prueba. |
| 1.2 | 1:00–1:25 | Terminal | `pytest -q --cov=app` → 97 passed, cobertura 100 % | Son 97 pruebas y todas pasan, con cobertura del cien por ciento. Usan SQLite en memoria, así que no necesitan servidor de base de datos ni red. Verificamos que corren igual en un entorno limpio con Python 3.13, que es lo que hace CodeBuild. |
| 1.3 | 1:25–2:00 | Postman, runner con `blacklist-aws` | Colección de 11 escenarios; *Run collection*, 1 iteración → 22 de 22, 0 errores. No abrir el token | La aplicación está en ejecución en Elastic Beanstalk y se prueba con Postman. La colección completa corre contra la URL del entorno: altas, duplicados, validaciones, consultas y falta de token. Pasan las 22 pruebas. |
| 1.4 | 2:00–2:15 | Navegador | `…elasticbeanstalk.com/ping` → `{"version": "b0e9d03"}` | La versión que responde es b0e9d03: el commit de la rama principal que construyó el pipeline. Héctor explica cómo está configurado. |

## 2. Héctor Melgarejo · 2:15–4:30 · Configuración del CI

Rúbrica: punto 2, CodeBuild (10 %); punto 3, archivo de construcción (25 %); punto 4, disparo por commit (15 %).

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 2:15–2:25 | GitHub | `buildspec.yml` en `main` | Soy Héctor Melgarejo y voy a mostrar la configuración de la integración continua: el archivo de construcción, el proyecto de CodeBuild y el pipeline que lo dispara. |
| 2.1 | 2:25–3:00 | GitHub, `buildspec.yml` | `install`: Python 3.13 y `pip install -r requirements-dev.txt`; `build`: `pytest` con cobertura, verificación de `COMMIT_ID`, `scripts/empaquetar.py` y listado del zip; `artifacts`: `dist/app-*.zip` | El archivo de construcción está versionado en la raíz del repositorio. Instala las dependencias, ejecuta las pruebas con cobertura y, solo si pasan, empaqueta la aplicación en un zip con los siete primeros caracteres del commit. Si una prueba falla, el build se detiene antes de empaquetar. Termina en la generación del artefacto: no despliega nada. |
| 2.2 | 3:00–3:30 | Consola de AWS, CodeBuild | `blacklist-devops-ci-build`: origen y artefactos desde CodePipeline; imagen `amazonlinux-x86_64-standard:6.0`, cómputo pequeño, sin variables de entorno; rol `blacklist-devops-codebuild-role`; registros en CloudWatch | El proyecto de CodeBuild recibe el código desde el pipeline y usa una imagen administrada de Amazon Linux 2023 con Python 3.13. No tiene variables con secretos ni cadena de conexión a la base. Su rol tiene permisos mínimos: escribir sus registros y leer y escribir solo en el bucket de artefactos. |
| 2.3 | 3:30–4:05 | Consola de AWS, CodePipeline | `blacklist-devops-ci-pipeline`: V2, `QUEUED`, rol `blacklist-devops-codepipeline-role`; etapa *Source* con la conexión `blacklist-devops-github`; etapa *Build* con `COMMIT_ID = #{SourceVariables.CommitId}`; almacén en el bucket del proyecto | El pipeline tiene dos etapas. Origen obtiene el código de GitHub mediante una conexión autorizada solo para este repositorio, sin tokens personales. Construcción lanza CodeBuild y le pasa el identificador del commit. Las ejecuciones se encolan, así que una no reemplaza a otra. No hay etapa de despliegue. |
| 2.4 | 4:05–4:30 | CodePipeline, edición de desencadenadores | *Push* hacia `main`; *pull request* creado y revisado hacia `dev` y `main`. Salir con *Cancel* | El pipeline se dispara solo con cada commit en la rama principal, main, y también con los pull requests, para validar los cambios antes de fusionarlos. Juan Sebastián muestra una ejecución exitosa provocada por un commit en main. |

## 3. Juan Sebastián Páez · 4:30–6:45 · Pipeline exitoso

Rúbrica: punto 1 del documento, pipeline exitoso (10 %); punto 4, disparo por commit (15 %).

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 4:30–4:40 | GitHub | PR #156, promoción de `dev` a `main`, fusionado | Soy Juan Sebastián Páez y voy a mostrar una ejecución exitosa del pipeline, de punta a punta: el commit, las pruebas en CodeBuild, el artefacto en S3 y su despliegue manual. |
| 3.1 | 4:40–5:10 | GitHub y CodePipeline | Reglas de las ramas `dev` y `main` (solo entran cambios por PR revisado); commit `b0e9d03` en `main`; ejecución `ff3146a4` disparada por ese commit, *Succeeded* en 38 s | Los cambios entran a dev por pull request revisado y se promueven a main con otro pull request. Al fusionar la promoción quedó el commit b0e9d03. Cinco segundos después el pipeline inició solo la ejecución, sin intervención manual, y terminó bien en 38 segundos. |
| 3.2 | 5:10–5:45 | Consola de AWS, CodeBuild | Build 2 iniciado por el pipeline, *Succeeded*; fases (instalación 19 s, construcción 3 s); registro con Python 3.13.16, 97 passed, cobertura 100 % y `Generado dist/app-b0e9d03.zip con 31 archivos` | El build usó Python 3.13.16, instaló las dependencias en 19 segundos y corrió las 97 pruebas con cobertura del cien por ciento. Como todas pasaron, generó el paquete app-b0e9d03.zip con 31 archivos. |
| 3.3 | 5:45–6:10 | Consola de AWS, S3 | Bucket `blacklist-devops-ci-artifacts-253041091381` → `blacklist-devops-ci-/BuildArtif/`: un objeto de 8 KB del 24 de octubre | El artefacto queda en un bucket privado y cifrado. Este objeto contiene el paquete del build exitoso. Aquí termina el pipeline: la entrega no incluye despliegue automático. |
| 3.4 | 6:10–6:45 | Consola de AWS, Elastic Beanstalk | Versión `b0e9d03`; entorno `Blacklist-devops-env` con salud *Ok* y versión en ejecución `b0e9d03`; eventos de la actualización de 54 s | Ese paquete lo subimos a mano como versión de la aplicación y lo desplegamos en Beanstalk: tardó 54 segundos y las tres instancias quedaron sanas. Es el mismo zip que generó CodeBuild, así que lo que corre se puede rastrear hasta su commit. Jean Pierre muestra qué pasa cuando una prueba falla. |

## 4. Jean Pierre Betancourt · 6:45–9:00 · Pipeline fallido y cierre

Rúbrica: punto 2 del documento, pipeline fallido (10 %).

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 6:45–6:55 | GitHub | PR #160, cerrado sin fusionar | Soy Jean Pierre Betancourt y voy a mostrar una ejecución fallida del pipeline: cómo la provocamos, dónde falla y qué no se genera. |
| 4.1 | 6:55–7:20 | GitHub, PR #160 | *NO FUSIONAR*: `test/build-fallido` → `dev`, commit `c423bff`; *Files changed* con `test_intentional_failure_for_the_pipeline`, que espera 500 en `/ping` | Creamos una rama temporal con una prueba que espera un error 500 en /ping, cuando el servicio responde 200, así que siempre falla. Abrimos un pull request hacia dev solo para disparar el pipeline y lo cerramos sin fusionar: la prueba rota nunca llegó a dev ni a main. |
| 4.2 | 7:20–7:50 | Consola de AWS, CodePipeline | Ejecución `69f3a6bb` disparada por el PR #160, *Failed* en 38 s; *Source* correcta, *Build* fallida | El pull request disparó el pipeline cinco segundos después de abrirlo. La etapa de origen obtuvo el código y la de construcción falló. En el historial se ven juntas la ejecución fallida y la exitosa. |
| 4.3 | 7:50–8:20 | Consola de AWS, CodeBuild | Build 3: fases `BUILD` y `UPLOAD_ARTIFACTS` en *Failed*; registro con `FAILED tests/test_ping.py::test_intentional_failure_for_the_pipeline`, `1 failed, 97 passed`, `COMMAND_EXECUTION_ERROR` y `no matching artifact paths found` | El registro identifica la prueba, el archivo y la línea: una falla y 97 pasan. Pytest termina con error, así que CodeBuild detiene la fase de construcción y nunca ejecuta el empaquetado. Por eso la subida del artefacto no encuentra nada que subir. |
| 4.4 | 8:20–8:40 | Consola de AWS, S3 | `blacklist-devops-ci-/BuildArtif/` con un solo objeto, el del build exitoso | En el bucket sigue habiendo un solo artefacto, el del build exitoso. Un cambio con pruebas rotas no produce un paquete desplegable, que es lo que buscamos con la integración continua. |
| 4.5 | 8:40–9:00 | GitHub | Repositorio en `main` con `buildspec.yml` y `tests/` | En resumen: cada endpoint tiene sus pruebas, el archivo de construcción las ejecuta y genera el artefacto, CodeBuild y CodePipeline lo hacen automáticamente con cada commit en main, y mostramos una ejecución exitosa y una fallida. El despliegue en Beanstalk sigue siendo manual. Gracias. |

## Cobertura de la rúbrica

| Requisito del enunciado | Peso | Pasos |
|---|---|---|
| Al menos una prueba unitaria por endpoint, que corre en el pipeline | 30 % | 1.1, 1.2, 3.2 |
| Proceso de build en AWS CodeBuild | 10 % | 2.2, 3.2 |
| Archivo de construcción: pruebas y generación del artefacto, sin despliegue | 25 % | 2.1, 3.2, 3.3, 4.3 |
| Cada commit en la rama principal dispara el build | 15 % | 2.3, 2.4, 3.1 |
| Documento 1: pipeline exitoso con hallazgos y capturas | 10 % | 3.1 a 3.4 |
| Documento 2: pipeline fallido con hallazgos y capturas | 10 % | 4.1 a 4.4 |
| Aplicación en ejecución en Beanstalk, accesible vía Postman | Entregable | 1.3, 1.4, 3.4 |
| Repositorio y flujo de ramas | Entregable | Intro, 2.1, 3.1, 4.5 |
| Evidencia en vivo, máximo 10 minutos | Condición | Todo el video, 9:00 |

## Preparación

Antes de grabar:

- Entorno encendido con `b0e9d03`, salud *Ok* y RDS disponible.
- Si se hace una segunda promoción de `dev` a `main` antes de grabar, actualizar en los pasos 1.4, 3.1 a 3.4 la
  versión y la ejecución que se muestran.
- Token cargado solo como valor actual en `blacklist-aws`, con tipo *secret*.
- Pestañas abiertas en el orden del guion, consola de AWS en `us-east-2`.
- Ensayo con cronómetro: cada parte dentro de sus 2:15; total por debajo de 9:30.
- Cada integrante graba su parte en pantalla completa, con audio claro, y la entrega a Jean Pierre.
- Jean Pierre une las cuatro partes en este orden, revisa el video completo y lo publica como en la Entrega 1
  (carpeta del equipo de Teams de la Universidad y copia en YouTube); verifica el enlace con otra cuenta (4.5).
- Después de aprobar el video: apagar el ambiente (4.7).

No mostrar en pantalla:

- Valores de `DATABASE_URL` y `JWT_SECRET_KEY` (en Beanstalk, solo los nombres de las propiedades).
- El token en Postman o en los encabezados.
- El archivo `.env` local.
- La barra de favoritos del navegador, paneles laterales de chat de las aplicaciones y datos personales de las
  cuentas.
- No guardar cambios al abrir la edición del pipeline o de los desencadenadores: salir con *Cancel*.
