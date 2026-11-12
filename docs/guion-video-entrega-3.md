# Guion del video de sustentación · Entrega 3

Tarea 4.1 (#221) · Épica E3 · Cierre

| Dato | Valor |
|---|---|
| Duración | **9:15** (límite del curso: 10:00) |
| Estructura | 4 partes seguidas, una por integrante, en 3 grabaciones |
| Grabación | Parte 2 el miércoles 11 de noviembre de 2026 (4.3, #223); partes 1, 3 y 4 el jueves 12 (4.2, #222 y 4.4, #224). Marcelo integra y publica el viernes 13 (4.5, #225) |

Regla del enunciado (`docs/entrega-3-entrega-continua.md`): el video muestra en vivo la configuración y los
escenarios de prueba de los endpoints, los repositorios de código y el ambiente en GitHub y AWS para la
integración y el despliegue continuo, sin dejar dudas de qué requisito se cumplió. Mostrar o leer solo el PDF
no cuenta como sustentación, y lo que pase del minuto 10 no se califica.

| Parte | Integrante | Tiempo | Tema |
|---|---|---|---|
| 1 | Marcelo Torres | 0:00–2:15 | Presentación, repositorio, archivos de configuración y Postman contra Fargate |
| 2 | Héctor Melgarejo | 2:15–4:30 | Configuración manual en Fargate y configuración del CI/CD |
| 3 | Juan Sebastián Páez | 4:30–6:45 | CI y CD exitosos disparados por un commit en `main` |
| 4 | Jean Pierre Betancourt | 6:45–9:15 | CI fallido, cambio a canario, CD fallido con reversión y cierre |

Cada parte la presenta quien construyó o ejecutó la pieza. Tareas de grabación del tablero: 4.2 (#222) es la
parte 1, 4.3 (#223) la parte 2 y 4.4 (#224) las partes 3 y 4. Las ejecuciones se recorren desde el historial de
cada servicio; no se esperan en vivo. Los valores `[PENDIENTE: …]` se completan cuando terminen la 2.5 (#209) y la
2.6 (#210).

Decisión del equipo del 10 de noviembre de 2026: el grupo de despliegue usa `CodeDeployDefault.ECSCanary10Percent5Minutes`
de forma permanente, en lugar de `ECSAllAtOnce`. La 2.3 se ejecutó con `ECSAllAtOnce`; la 2.5 y la 2.6 corren con el
canario. La 2.5 mostró que el canario tampoco revisa la salud de la versión nueva antes del primer 10 % del tráfico
(`docs/ci/entrega-3/2.5-cd-fallido.md`); por eso la 2.6 agrega una verificación de salud del contenedor en
`taskdef.json` (votación del 10 de noviembre).

## 1. Marcelo Torres · 0:00–2:15 · Presentación, configuración y Postman

Rúbrica: pipeline, punto 1, archivos de configuración con las pruebas en el build (10 %); aplicación en Fargate
accesible vía Postman.

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 0:00–0:20 | GitHub | Repositorio en `main`, README | Hola, somos el grupo Blacklist DevOps: Marcelo Torres, Héctor Melgarejo, Juan Sebastián Páez y Jean Pierre Betancourt. En esta entrega el microservicio de lista negra pasa a contenedores en AWS Fargate, y el pipeline, además de probar y construir, despliega solo. Yo soy Marcelo y voy a mostrar el repositorio, los archivos de configuración y la aplicación funcionando. |
| 1.1 | 0:20–0:40 | GitHub, *Settings → Rules → Rulesets* | `protect-main` (PR, 1 aprobación, merge commit, `solo-desde-dev`) y `protect-dev` (PR, 1 aprobación, squash, `no-desde-main`) | El código sigue en GitHub, como lo confirmó el curso, y el pipeline lo toma por una conexión autorizada solo para este repositorio. Los cambios entran a dev por pull request revisado, y solo dev se promueve a main. Cada commit que llega a main dispara el pipeline completo. |
| 1.2 | 0:40–1:00 | GitHub, `tests/` | `test_blacklist_api.py` (POST 201, 400, 409; GET), `test_authentication.py` (401), `test_ping.py`; `docs/pruebas/2.1-escenarios-por-endpoint.md` | Las pruebas unitarias son las de la entrega anterior: cada endpoint tiene escenarios para todas las respuestas del contrato, incluidos los errores y la falta de token. Son 156 pruebas con cobertura del cien por ciento, y el pipeline las ejecuta antes de construir la imagen. |
| 1.3 | 1:00–1:35 | GitHub, raíz de `main` | `Dockerfile` (`python:3.13.16-slim`, Gunicorn en el 8000, usuario sin privilegios); `buildspec.yml` (pruebas primero, `docker build`, envío a ECR, `imageDetail.json`; artefactos con `taskdef.json` y `appspec.yaml`); `taskdef.json` (Fargate, 256 CPU y 512 MB, `<IMAGE1_NAME>`, secretos por referencia, `healthCheck` contra `/ping` en el 8000); `appspec.yaml` (contenedor `blacklist-devops`, puerto 8000) | Estos cuatro archivos están versionados en la raíz del repositorio. El Dockerfile empaqueta el microservicio. El archivo de construcción corre primero las pruebas; si una falla, no se construye ninguna imagen. Si pasan, construye la imagen con la versión del commit, la envía al registro y deja el archivo que dice qué imagen desplegar. La definición de la tarea y el appspec le dicen a CodeDeploy qué contenedor desplegar y en qué puerto recibe el tráfico; la definición además revisa la salud del contenedor con /ping. Los secretos no están en el repositorio: la tarea los toma de Parameter Store. |
| 1.4 | 1:35–2:00 | Postman, *Runner* con `blacklist-fargate` | Colección de 11 escenarios contra el balanceador; *Run collection*, 1 iteración → 22 de 22, 0 errores (8 de noviembre). Corrida final: `[PENDIENTE: 2.6 (#210)]`. No abrir el token | La aplicación corre en Fargate detrás de un balanceador. Esta es la colección de Postman de las entregas anteriores, ahora contra la dirección del balanceador: altas, duplicados, validaciones, consultas y falta de token. Pasan las 22 pruebas. |
| 1.5 | 2:00–2:15 | Navegador | `http://blacklist-devops-alb-663902063.us-east-2.elb.amazonaws.com/ping` → `{"version": "[PENDIENTE: 2.6 (#210)]"}` | La versión que responde es el commit de main que desplegó el pipeline. Héctor muestra cómo está montado el ambiente. |

## 2. Héctor Melgarejo · 2:15–4:30 · Fargate y configuración del CI/CD

Rúbrica: configuración del despliegue en Fargate, ambiente, despliegue manual y validación (20 %); pipeline,
puntos 2 y 3, configuración.

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 2:15–2:25 | Consola de AWS, `us-east-2` | Página de ECS | Soy Héctor Melgarejo. Primero muestro el ambiente que configuramos a mano en Fargate y después cómo el pipeline lo actualiza. |
| 2.1 | 2:25–2:45 | ECR | Repositorio privado `blacklist-devops`: etiquetas mutables, ciclo de vida de 10 imágenes; `f224bef` (subida a mano) y las del pipeline | El registro de imágenes es privado y conserva las diez últimas. La primera imagen la construimos y subimos a mano para el despliegue manual. Las siguientes las sube el pipeline con dos etiquetas: el commit y latest. |
| 2.2 | 2:45–3:20 | ECS | Clúster `blacklist-devops-cluster`; `blacklist-devops-task` revisión 1 (manual, `f224bef`) y `:4` (`db6e990`): 0,25 vCPU y 512 MB, puerto 8000, rol de ejecución, secretos solo por nombre, registros en `/ecs/blacklist-devops`; servicio `blacklist-devops-service` con controlador `CODE_DEPLOY`, 1 tarea, subredes públicas | El clúster solo usa Fargate: no administramos servidores. La primera revisión de la tarea la registramos a mano con la imagen que subimos; con ella creamos el servicio y validamos que la API respondía. La tarea fija la CPU, la memoria y el puerto, y recibe los secretos desde Parameter Store sin que queden en el archivo. El servicio mantiene una tarea en ejecución y le entrega los despliegues a CodeDeploy. |
| 2.3 | 3:20–3:45 | EC2, balanceadores y grupos de destino | `blacklist-devops-alb` con *listener* HTTP:80; `blacklist-devops-tg-azul` y `-verde` (tipo IP, puerto 8000, salud en `/ping`); `blacklist-devops-alb-sg` (80) → `blacklist-devops-tareas-sg` (8000) → `blacklist-db-sg` (5432) | El balanceador recibe el tráfico en el puerto 80 y lo envía a uno de los dos grupos de destino, que revisan la salud con /ping. Las tareas solo aceptan tráfico del balanceador, y la base de datos solo de las tareas. Los dos grupos son los que usa el despliegue azul/verde. |
| 2.4 | 3:45–4:00 | CodeBuild | `blacklist-devops-ci-build`: modo privilegiado, `AWS_ACCOUNT_ID`, rol `blacklist-devops-codebuild-role` | El proyecto de construcción es el de la entrega anterior, ahora en modo privilegiado para poder construir imágenes, y con permiso para subirlas solo a este registro. |
| 2.5 | 4:00–4:30 | CodeDeploy y CodePipeline | `blacklist-devops-app` y `blacklist-devops-dg` (azul/verde, `CodeDeployDefault.ECSCanary10Percent5Minutes`, 2 minutos de espera, reversión automática); en `blacklist-devops-task`, la verificación de salud del contenedor contra `/ping` `[PENDIENTE: 2.6 (#210)]`; `blacklist-devops-ci-pipeline` (V2) con *Source*, *Build* y *Deploy* (`CodeDeployToECS`); desencadenador solo *push* a `main`. Salir con *Cancel* | CodeDeploy despliega con azul y verde, en modo canario: levanta la versión nueva junto a la actual, le pasa el diez por ciento del tráfico durante cinco minutos y después todo. Después del despliegue fallido agregamos a la tarea una verificación de salud con /ping, para que ECS no dé por lista una tarea que no responde. Si el despliegue falla, CodeDeploy revierte solo. El pipeline tiene tres etapas y se dispara con cada commit en main. Juan Sebastián muestra una ejecución completa. |

## 3. Juan Sebastián Páez · 4:30–6:45 · CI y CD exitosos

Rúbrica: pipeline, punto 2, build automático con la imagen (10 %); punto 3, despliegue continuo automático
(40 %); documento, punto 2 (8 %).

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 4:30–4:40 | GitHub | PR #250, promoción de `dev` a `main`, fusionado el 9 de noviembre a las 17:59 | Soy Juan Sebastián Páez y voy a mostrar una ejecución exitosa de punta a punta: del commit en main a la versión nueva en Fargate, sin intervención manual. |
| 3.1 | 4:40–5:05 | GitHub y CodePipeline | Merge commit `db6e990`; ejecución `31b06edb`, desencadenador `PUSH_BRANCH`, tres etapas en *Succeeded*, 8 min 19 s (*Source* 5 s, *Build* 3 min 35 s, *Deploy* 4 min 37 s) | Al fusionar la promoción quedó este commit en main. Tres segundos después, el pipeline arrancó solo y pasó por las tres etapas. Es la primera ejecución que inicia un commit, sin que nadie la lance. |
| 3.2 | 5:05–5:40 | CodeBuild (build 28) y ECR | Fases en *Succeeded*, origen `db6e990`; registro: Python 3.13.16, `156 passed`, cobertura 100 %, `docker build`, envío de `db6e990` y `latest`, `imageDetail.json`; ECR: `latest, db6e990`, 18:03:11, mismo *digest* | El build corrió las 156 pruebas con cobertura del cien por ciento y, como pasaron, construyó la imagen y la subió al registro con la etiqueta del commit y latest. Aquí está en ECR. |
| 3.3 | 5:40–6:20 | CodeDeploy, ECS y EC2 | `d-UKCBNTBGL`: cuatro pasos, 100 % del tráfico en el conjunto de sustitución, *Succeeded* de 18:03:21 a 18:07:29 (refrescar la tabla de conjuntos de tareas); servicio con `blacklist-devops-task:4`; *listener* → `blacklist-devops-tg-azul`. Esta ejecución se hizo con la configuración inicial, `ECSAllAtOnce` | La etapa de despliegue registró una revisión nueva de la tarea con esa imagen y creó este despliegue en CodeDeploy; la consola lo muestra como acción de usuario porque lo pidió el pipeline por la API. Esta ejecución usó la configuración inicial, que pasa todo el tráfico de una vez: la versión nueva arrancó en el grupo azul y recibió todo el tráfico, y dos minutos después se terminó la tarea anterior. |
| 3.4 | 6:20–6:45 | GitHub, `docs/ci/entrega-3/2.3-pipeline-exitoso.md` | Línea de tiempo: `/ping` respondió `168dd91` hasta las 18:05:20 y `db6e990` desde las 18:05:53, sin consultas fallidas | Mientras corría el despliegue consultamos /ping por el balanceador. Respondió la versión anterior hasta el cambio de tráfico y la nueva desde entonces, sin ninguna falla. La versión se puede rastrear hasta el commit: la etiqueta de la imagen, la tarea y /ping dicen db6e990. Jean Pierre muestra qué pasa cuando algo falla. |

## 4. Jean Pierre Betancourt · 6:45–9:15 · Ejecuciones fallidas, cambio a canario y cierre

Rúbrica: documento, punto 1, CI fallido (4 %); punto 3, CI exitoso y CD fallido (8 %).

| Paso | Tiempo | Herramienta | En pantalla | Qué decir |
|---|---|---|---|---|
| Intro | 6:45–6:55 | GitHub | PR #253, fusionado en `dev`, con la prueba que falla a propósito | Soy Jean Pierre Betancourt y voy a mostrar dos fallas: una en la integración continua y otra en el despliegue. |
| 4.1 | 6:55–7:20 | GitHub y CodePipeline | `test_intentional_failure_for_the_pipeline`, promovida a `main` por el flujo de ramas: PR #253 a `dev` y promoción #254, *merge commit* `299125d` (9 de noviembre, 22:58:01); ejecución `e363652d`: *Source* en *Succeeded*, *Build* en *Failed*, *Deploy* «No se ejecutó»; 3 min 42 s | Agregamos una prueba que siempre falla y la llevamos a main por el flujo normal de ramas. El commit disparó el pipeline, que se detuvo en la construcción: el despliegue no se ejecutó. |
| 4.2 | 7:20–7:40 | CodeBuild, ECR y GitHub | Build 29: `FAILED tests/test_ping.py::test_intentional_failure_for_the_pipeline` (`assert 200 == 500`), `1 failed, 156 passed`, sin `docker build`; ECR sin `299125d` (la última sigue siendo `latest, db6e990`); `docs/despliegues/entrega-3/2.4-ci-fallido.csv`: 360 consultas a `/ping`, todas 200 con `db6e990` | El registro dice qué prueba falló. Las pruebas son el primer paso de la construcción: como fallaron, CodeBuild detuvo la fase y no se construyó ni se subió ninguna imagen. Fargate siguió con la versión anterior. |
| 4.3 | 7:40–8:05 | ECS, CodeDeploy y documentación de AWS | Eventos del servicio en la 2.3: la tarea nueva registrada en `tg-azul` a las 18:03:56 y estable a las 18:04:05, sin verificación de salud (necesita al menos 30 s); guía de AWS «Troubleshoot Amazon ECS deployment issues»; grupo `blacklist-devops-dg` con `ECSCanary10Percent5Minutes` (cambio del 10 de noviembre) | Antes de provocar el despliegue fallido revisamos los eventos de la ejecución exitosa: con la configuración inicial, el balanceador no revisó la salud de la versión nueva antes de pasarle el tráfico. Con un contenedor roto, la aplicación habría quedado caída y el despliegue, marcado como exitoso. AWS lo documenta. Por eso el equipo cambió el grupo a canario, que según la guía de AWS revisaría la salud antes de pasar el tráfico. |
| 4.4 | 8:05–8:35 | GitHub, CodePipeline, CodeDeploy y ECS | PR #258 de la 2.5 (#209): retira la prueba que falla y cambia el puerto de Gunicorn a `8001`; promoción #261, *merge commit* `69e12b8` (10 de noviembre, 22:34:51); ejecución `035b42d2` con *Source* y *Build* en *Succeeded* y *Deploy* en *Failed*, 11 min 59 s; imagen `69e12b8` en ECR y `blacklist-devops-task:5`; despliegue `d-SYHBSF3HL`: `Install` 1 min 42 s, `AllowTraffic` de 22:40:56 a 22:45:57, *Failed* a las 22:46:40 con `ECS_UPDATE_ERROR` («CodeDeploy detected that the replacement task set is unhealthy»); reversión automática `d-2TNRGN3HL` (22:46:41–22:46:43); eventos de ECS: «port 8000 is unhealthy in target-group blacklist-devops-tg-verde» y «replaced 1 tasks due to an unhealthy status»; el servicio sigue en `blacklist-devops-task:4` | Ahora las pruebas pasan, así que el build construye y sube la imagen, pero el contenedor escucha en un puerto distinto del que espera el balanceador. ECS volvió a dar la tarea por lista sin revisar su salud, y el canario le pasó el diez por ciento del tráfico. Ahí el balanceador la marcó en mal estado y ECS la reemplazó varias veces. A los cinco minutos CodeDeploy pasó todo el tráfico, detectó que el conjunto nuevo no estaba sano y revirtió solo, en dos segundos, a la versión anterior, que seguía corriendo. |
| 4.5 | 8:35–8:55 | GitHub (`docs/ci/entrega-3/2.5-cd-fallido.md`, `docs/despliegues/entrega-3/2.5-cd-fallido.csv`) y CloudWatch | Monitor de `/ping`: 40 de 361 consultas con 502 durante la ejecución (18 sueltas con el 10 %, 22 seguidas con el 100 %); `HTTPCode_ELB_502_Count`: 77 en el balanceador; las respuestas buenas, siempre `db6e990`. Reversión por el flujo de ramas con la verificación de salud del contenedor, PR `[PENDIENTE: #, 2.6 (#210)]`, y despliegue exitoso con canario `[PENDIENTE]` | El costo fue real: con el diez por ciento hubo errores sueltos durante cinco minutos, y al pasar todo el tráfico, unos cuarenta y cuatro segundos sin servicio hasta la reversión. La causa es que nada revisaba la tarea antes de darle tráfico. Por eso, al revertir el cambio por el flujo de ramas, agregamos una verificación de salud del contenedor, y con ella se desplegó la versión buena: es la que probó Marcelo al inicio. |
| 4.6 | 8:55–9:15 | CodePipeline, historial | La exitosa `31b06edb`, la de CI fallido, la de CD fallido y la de la versión final | En resumen: el microservicio corre en Fargate, configurado a mano y validado con Postman; cada commit en main prueba, construye la imagen y despliega solo con azul y verde en modo canario. Mostramos un CI fallido, un CI y CD exitosos y un CD fallido con reversión automática, y lo que corregimos a partir de él. Gracias. |

## Cobertura de la rúbrica

| Requisito del enunciado | Peso | Pasos |
|---|---|---|
| Configuración manual del ambiente, despliegue manual y validación en Fargate | 20 % | 1.4, 1.5, 2.1 a 2.3 |
| Archivos de configuración para CodeDeploy, con las pruebas unitarias en la construcción | 10 % | 1.2, 1.3, 3.2 |
| Cada commit en la rama principal ejecuta el build con la creación de la imagen | 10 % | 2.4, 2.5, 3.1, 3.2 |
| Despliegue continuo automático en Fargate tras un CI exitoso | 40 % | 2.5, 3.1, 3.3, 3.4 |
| Documento 1: CI fallido con hallazgos y capturas | 4 % | 4.1, 4.2 |
| Documento 2: CI y CD exitosos con hallazgos y capturas | 8 % | 3.1 a 3.4 |
| Documento 3: CI exitoso y CD fallido con hallazgos y capturas | 8 % | 4.3 a 4.5 |
| Aplicación en Fargate accesible vía Postman | Entregable | 1.4, 1.5 |
| Repositorio y flujo de ramas (en GitHub, confirmado por el curso) | Entregable | Intro, 1.1, 3.1, 4.1 |
| Evidencia en vivo, máximo 10 minutos | Condición | Todo el video, 9:15 |

## Preparación

Antes de grabar:

- 2.6 (#210) ejecutada y documentada, para completar los pendientes. La 2.5 (#209) ya está documentada en
  `docs/ci/entrega-3/2.5-cd-fallido.md`: el despliegue falló a los 7 min 30 s y la ejecución duró 11 min 59 s.
- Servicio con la versión de la 2.6, una tarea sana en el grupo activo, balanceador activo y RDS disponible.
- En ECR siguen las imágenes que se muestran (`f224bef`, `db6e990` y la de la 2.5): el ciclo de vida conserva 10.
- Token cargado solo como valor actual en `blacklist-fargate`, con tipo *secret*.
- Pestañas abiertas en el orden del guion, consola de AWS en `us-east-2`.
- Ensayo con cronómetro: cada parte dentro de su tiempo; total por debajo de 9:30.
- Cada integrante graba su parte en pantalla completa, con audio claro, y la entrega a Marcelo.
- Marcelo une las cuatro partes en este orden, revisa el video completo, lo publica como en las entregas
  anteriores y verifica el enlace con otra cuenta (4.5, #225).
- Después de aprobar el video: apagar el ambiente (4.7, #227).

No mostrar en pantalla:

- Valores de los parámetros de Parameter Store: solo sus nombres.
- El token en Postman o en los encabezados.
- El archivo `.env` local.
- La barra de favoritos, los paneles laterales de chat de las aplicaciones, la marca de agua de activación de
  Windows y los datos personales de las cuentas.
- No guardar cambios al abrir la edición del pipeline, del grupo de despliegue o del servicio: salir con *Cancel*.
