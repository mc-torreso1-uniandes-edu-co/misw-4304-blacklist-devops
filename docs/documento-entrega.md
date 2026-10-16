# Proyecto 1 · Entrega 1: Despliegue manual de un microservicio en AWS Elastic Beanstalk

| | |
|---|---|
| Curso | MISW 4304 · DevOps · Universidad de los Andes (periodo 202615) |
| Entrega | Entrega 1: despliegue manual de un microservicio sobre un servicio PaaS |
| Grupo | Blacklist DevOps |
| Integrantes | Marcelo César Torres · Héctor José Melgarejo · Juan Sebastián Páez · Jean Pierre Betancourt |
| Fecha | 18 de octubre de 2026 |

## Contenido

1. Descripción del microservicio
2. Arquitectura del despliegue
3. Enlaces de la entrega
4. Paso a paso de la creación y el despliegue en AWS Elastic Beanstalk (punto 1 del documento, 10 %)
5. Estrategias de despliegue (punto 2 del documento, 20 %)
6. Pruebas del API
7. Limitaciones y decisiones
8. Conclusiones

## 1. Descripción del microservicio

*Contexto de la verificación funcional (70 %): qué hace el servicio y su contrato.*

El microservicio administra la lista negra global de emails de la organización. Los sistemas internos
lo usan para agregar un email a la lista y para consultar si un email está en ella. Es un único
servicio REST en Python con Flask, protegido con un token Bearer, que persiste la información en
PostgreSQL sobre Amazon RDS.

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| POST | `/blacklists` | Agrega un email a la lista negra. Cuerpo: `email`, `app_uuid` (UUID obligatorio) y `blocked_reason` (opcional, máximo 255 caracteres). Guarda además la IP de origen y la fecha y hora de la solicitud | 201 con `msg` e `id`; 400 con `msg` y `errors`; 401 sin token o con token inválido; 409 si el email ya está |
| GET | `/blacklists/<string:email>` | Indica si el email está en la lista y el motivo | 200 con `is_blacklisted` y `blocked_reason`; 401 sin token o con token inválido |
| GET | `/ping` | Health check del balanceador. No requiere token ni consulta la base | 200 con `{"version": ...}` |

Stack: Python 3.13, Flask 3.1.3, Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.1.4), Flask-RESTful 0.3.10,
Flask-Marshmallow 1.5.0 (marshmallow 4.3.1), Flask-JWT-Extended 4.7.4, Werkzeug 3.1.9, PostgreSQL 16
con el driver psycopg 3 y Gunicorn 26.2.0 como servidor WSGI.

El código está organizado por capas: `domain` (entidad, validación del email, errores y reloj),
`application` (casos de uso *agregar* y *consultar*, y el puerto del repositorio) e `infrastructure`
(recursos HTTP, esquema de validación, autenticación y repositorio SQLAlchemy). El email se normaliza a
minúsculas y sin espacios al guardar y al consultar.

## 2. Arquitectura del despliegue

*Soporta la verificación funcional (70 %) y el punto 1 del documento: recursos de AWS y cómo se
guarda la IP del cliente que pide el POST.*

```
Cliente (Postman / sistemas internos)
        │  HTTP, Authorization: Bearer <token>
        ▼
Application Load Balancer (público, 3 zonas de us-east-2)
        │  health check GET /ping → 200
        ▼
Auto Scaling group: 3 a 6 instancias t3.micro (Amazon Linux 2023)
  nginx → Gunicorn (2 workers) → Flask
        │  PostgreSQL 5432, solo desde el grupo de las instancias
        ▼
Amazon RDS PostgreSQL 16 (db.t4g.micro, sin acceso público)
```

| Componente | Configuración |
|---|---|
| Cuenta y región | `misw-4304-202615-blacklist-devops`, región `us-east-2` (Ohio) |
| Aplicación y entorno | `blacklist-devops` / `Blacklist-devops-env` |
| Plataforma | Python 3.13 running on 64bit Amazon Linux 2023, versión `4.13.10` (Python 3.13.16) |
| Balanceador | Application Load Balancer público, subredes públicas en `us-east-2a`, `-2b` y `-2c` |
| Cómputo | Auto Scaling de 3 a 6 instancias `t3.micro` (`x86_64`) |
| Base de datos | RDS `blacklist-db`, PostgreSQL 16.13, `db.t4g.micro`, 20 GB gp3, una zona, sin acceso público |
| Red | `blacklist-app-sg` para las instancias; `blacklist-db-sg` solo admite 5432 desde `blacklist-app-sg` |
| Roles de IAM | Servicio: `blacklist-eb-service-rol`. Instancias: `blacklist-ec2-instance-rol` |
| Configuración | `DATABASE_URL`, `JWT_SECRET_KEY`, `APP_ENV` y `PROXY_FIX_X_FOR` como propiedades del entorno; ningún secreto en el repositorio |
| Configuración reproducible | Configuración guardada `blacklist-base`, con la que se recrea el entorno con la misma URL |

Para guardar la IP del cliente y no la del balanceador, la aplicación lee el encabezado
`X-Forwarded-For` con `ProxyFix` de Werkzeug. En Beanstalk la solicitud pasa por el balanceador y por
el nginx de la instancia, y cada uno agrega una entrada al encabezado (`cliente, balanceador`). La
primera versión desplegada (`v1`) tomaba un solo salto y guardó la IP privada del balanceador
(`172.31.21.107`). La versión `v1.1` lee el número de saltos de la propiedad `PROXY_FIX_X_FOR`, que en
el entorno vale `2`, y guarda la IP pública del cliente. Con dos saltos, una entrada falsa enviada por
el cliente queda a la izquierda y no se toma. La consulta de la tabla desde una instancia muestra los
dos registros:

![Figura 1. IP guardada en RDS: con v1.1, la del cliente (181.237.182.151); con v1, la del balanceador (172.31.21.107)](capturas/1.7b-ip-guardada.png)

## 3. Enlaces de la entrega

*Soporta la verificación funcional (70 %): la aplicación en ejecución, el repositorio y la URL
publicada de la documentación de Postman que pide el enunciado.*

| Recurso | Enlace |
|---|---|
| Repositorio de GitHub | https://github.com/mc-torreso1-uniandes-edu-co/misw-4304-blacklist-devops |
| URL del entorno | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| Documentación publicada del API | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Video de sustentación | [PENDIENTE: enlace del video] |

Según la aclaración del tutor sobre los recursos de AWS, el entorno solo está encendido durante el
trabajo y la grabación del video: se encendió el 15 de octubre de 2026 para el primer despliegue y se
apaga después de grabar. La configuración guardada y las versiones cargadas permiten volver a proveerlo
con la misma URL si se cita a una sustentación síncrona.

## 4. Paso a paso de la creación y el despliegue en AWS Elastic Beanstalk

*Cubre el punto 1 del documento (10 %): a. configuración de RDS, b. configuración del proyecto en
Beanstalk y c. configuración de los health checks.*

La infraestructura se creó y se desplegó manualmente, con la consola de AWS y la AWS CLI, sin
servicios de CI/CD. Antes de crear
los recursos se verificó la cuenta, la región y la cuota de vCPU, que limita cuántas instancias
pueden existir a la vez durante las estrategias que agregan instancias.

![Figura 2. Cuenta y región us-east-2](capturas/2-cuenta-region.png)

![Figura 3. Cuota de vCPU On-Demand de la cuenta (32)](capturas/2-cuota-vcpu.png)

### 4.a Configuración de RDS

Base de datos PostgreSQL creada con la plantilla de capa gratuita, sin acceso público y con un grupo
de seguridad que solo admite conexiones desde las instancias de la aplicación.

| Parámetro | Valor |
|---|---|
| Identificador | `blacklist-db` |
| Motor | PostgreSQL 16.13 |
| Clase y almacenamiento | `db.t4g.micro` (2 vCPU, 1 GiB), 20 GB gp3 sin escalado automático |
| Usuario y base inicial | `blacklist` / `blacklist` (contraseña autoadministrada, fuera del repositorio) |
| Disponibilidad | Una zona (`us-east-2c`), sin Multi-AZ |
| Acceso público | Desactivado |
| Grupo de seguridad | `blacklist-db-sg`: PostgreSQL 5432 solo desde `blacklist-app-sg` |
| Supervisión | Monitoreo mejorado desactivado |

![Figura 4. Selección del motor PostgreSQL](capturas/3a-rds-motor-postgresql.png)

![Figura 5. Plantilla de capa gratuita](capturas/3a-rds-capa-gratuita.png)

![Figura 6. Identificador de la base y usuario maestro](capturas/3a-rds-identificador.png)

![Figura 7. Credenciales autoadministradas](capturas/3a-rds-credenciales.png)

![Figura 8. Clase de instancia y almacenamiento](capturas/3a-rds-clase-almacenamiento.png)

![Figura 9. Conectividad, sin acceso público](capturas/3a-rds-conectividad.png)

![Figura 10. Grupo de seguridad de la base](capturas/3a-rds-grupo-seguridad.png)

![Figura 11. Supervisión](capturas/3a-rds-supervision.png)

![Figura 12. Opciones de base de datos](capturas/3a-rds-opciones.png)

![Figura 13. Mantenimiento](capturas/3a-rds-mantenimiento.png)

![Figura 14. Base de datos creada](capturas/3a-rds-creada.png)

![Figura 15. Regla de entrada de blacklist-db-sg: 5432 desde blacklist-app-sg](capturas/3b-rds-sg-entrada.png)

La cadena de conexión se registra solo como propiedad `DATABASE_URL` del entorno de Beanstalk. Las
tablas las crea la aplicación al iniciar.

![Figura 16. blacklist-db disponible el 15 de octubre de 2026, antes del primer despliegue](capturas/1.7b-rds-available.png)

### 4.b Configuración del proyecto en AWS Beanstalk

Antes del entorno se creó el grupo de seguridad de las instancias, `blacklist-app-sg`, sin reglas de
entrada. Se conserva aunque se termine el entorno, para que la regla de la base siga vigente cada vez
que se recrea.

![Figura 17. Grupo de seguridad de las instancias](capturas/4-app-sg.png)

El entorno se creó en modo estándar con estos parámetros:

| Parámetro | Valor |
|---|---|
| Aplicación / entorno | `blacklist-devops` / `Blacklist-devops-env` |
| Prefijo de URL | `blacklist-devops-misw` |
| Plataforma | Python 3.13 running on 64bit Amazon Linux 2023, `4.13.10` |
| Proxy y WSGI | nginx; la aplicación arranca con el `Procfile` (`gunicorn --bind :8000 --workers 2 application:application`) |
| Acceso al servicio | Rol de servicio `blacklist-eb-service-rol` y perfil de instancia `blacklist-ec2-instance-rol`; sin par de llaves EC2 |
| Red | VPC por defecto, IP pública en las instancias, 3 zonas de disponibilidad |
| Instancias | `t3.micro`, `x86_64`, grupo `blacklist-app-sg` |
| Capacidad | Auto Scaling con balanceo de carga, mínimo 3 y máximo 6 instancias |
| Balanceador | Application Load Balancer público |
| Actualizaciones administradas | Desactivadas |
| Registros en CloudWatch | Desactivados |
| Propiedades del entorno | `APP_ENV`, `DATABASE_URL`, `JWT_SECRET_KEY` (valores fuera del documento) y `PROXY_FIX_X_FOR = 2` |

![Figura 18. Modo estándar y nombre del entorno](capturas/5a-eb-general.png)

![Figura 19. Opciones de la plataforma, rol de servicio y perfil de instancia](capturas/5b-eb-opciones-plataforma-roles.png)

![Figura 20. Escalado de 3 a 6 instancias y balanceador](capturas/5c-eb-escalado.png)

![Figura 21. Cómputo: t3.micro, x86_64](capturas/5d-eb-computo.png)

![Figura 22. Redes, subredes y grupo de seguridad de las instancias](capturas/5e-eb-redes.png)

![Figura 23. Subredes del balanceador](capturas/5g-eb-subredes-elb.png)

![Figura 24. Entorno en estado Ok y configuración guardada](capturas/5h-eb-entorno-ok.png)

**Primer despliegue (15 de octubre de 2026).** La versión `v1` se empaquetó desde `main` con el script
del repositorio (`scripts/empaquetar.py`), que ejecuta las pruebas y genera el `.zip` con el archivo
`VERSION` que devuelve `/ping`. El paquete se probó en una carpeta limpia antes de cargarlo y se cargó
una sola vez como versión de aplicación `v1`. Después se inició la RDS y se creó el entorno desde la
configuración guardada `blacklist-base` con esa versión. La creación tomó 3 min 13 s y terminó con
salud *Ok* en las 3 instancias.

![Figura 25. Eventos de la creación del entorno: lanzado con éxito en 3 minutos](capturas/1.7b-eb-eventos.png)

![Figura 26. Historial de implementaciones: creación del entorno con v1, 3 min 13 s](capturas/1.7b-eb-version-v1.png)

![Figura 27. /ping en la URL del entorno responde la versión v1](capturas/1.7b-ping-v1.png)

Al recrear el entorno desde la consola, el formulario propone el rol de servicio
`aws-elasticbeanstalk-service-role` en lugar de `blacklist-eb-service-rol`, y la creación falla
porque la configuración guardada usa este último para las actualizaciones administradas. El entorno se
creó con la AWS CLI desde `blacklist-base`, que conserva los roles de la plantilla. El procedimiento
quedó en `docs/despliegues/1.7-infraestructura-reproducible.md`.

**Versión `v1.1`.** La verificación en AWS mostró que `v1` guardaba la IP del balanceador (sección 2).
Se generó `v1.1` desde `main`, que ya leía `PROXY_FIX_X_FOR`, y se desplegó junto con la propiedad
`PROXY_FIX_X_FOR = 2` en una sola actualización del entorno (política *All at once*, 1 minuto). La
propiedad también se agregó a `blacklist-base`. Con `v1.1` en las 3 instancias, el POST y el GET
responden contra RDS desde Postman con el environment de AWS:

![Figura 28. POST /blacklists contra el entorno de Beanstalk: 201 Created](capturas/1.7b-postman-post-v1.1.png)

![Figura 29. GET /blacklists/<email> con el email agregado: 200, is_blacklisted true y el motivo](capturas/1.7b-postman-get-v1.1.png)

### 4.c Configuración de los health checks

El balanceador comprueba cada instancia con `GET /ping`. Ese endpoint no requiere token y no consulta
la base, así que mide si la aplicación responde sin depender de credenciales ni de RDS. La misma ruta
se fija también en el paquete, en `.ebextensions/01-health-check.config`, para que cada despliegue
conserve la configuración:

```yaml
option_settings:
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /ping
    MatcherHTTPCode: "200"
```

| Parámetro del proceso `default` | Valor |
|---|---|
| Puerto y protocolo | 80, HTTP |
| Ruta de comprobación | `/ping` |
| Código HTTP esperado | 200 |
| Tiempo de espera | 5 s |
| Intervalo | 15 s |
| Umbral de buen estado / mal estado | 3 / 5 comprobaciones |
| Demora en la anulación del registro | 20 s |
| Informes de salud | Mejorados (*enhanced*) |

![Figura 30. Comprobación de estado del proceso default: /ping, código 200](capturas/5f-eb-healthcheck.png)

Con el entorno en ejecución, la pestaña *Estado y supervisión* muestra la salud *Ok* del entorno y de
las 3 instancias, que reciben las comprobaciones del balanceador y las solicitudes de los clientes:

![Figura 31. Estado y supervisión: entorno Ok y 3 instancias en Ok con el mismo despliegue](capturas/1.7b-eb-entorno-ok.png)

## 5. Estrategias de despliegue

*Cubre el punto 2 del documento (20 %): cuatro estrategias con más de una instancia, cada una con los
puntos a–f.*

Las estrategias se ejecutaron sobre el mismo entorno, con Auto Scaling de mínimo 3 y máximo 6
instancias, en este orden: All at once (`v2-allatonce`), Rolling (`v3-rolling`), Rolling with
additional batch (`v4-rollingbatch`) e Immutable (`v5-immutable`). Cada versión cambia la etiqueta que
devuelve `/ping`, lo que permite ver qué instancias atienden la versión nueva durante el despliegue.

**Método de medición, común a las cuatro estrategias:**
- Tiempo total: desde el evento de inicio del despliegue hasta el evento de finalización en la pestaña
  *Eventos* del entorno.
- Instancias: lista de instancias del entorno en EC2 antes, durante y después del despliegue.
- Disponibilidad: el monitor del repositorio (`scripts/monitor_disponibilidad.py`) consulta `/ping`
  cada segundo durante todo el despliegue y registra la hora, el código HTTP, la versión y la latencia
  de cada respuesta en un CSV de `docs/despliegues/`. Un corte de conexión se registra como código 0
  y no detiene el monitor. Al detenerlo resume las respuestas que no fueron 200, la mayor caída (desde
  la primera respuesta que no fue 200 hasta la siguiente respuesta 200), las versiones observadas y la
  ventana en la que respondieron dos versiones.
- Paquetes: cada versión se generó desde `main` y se probó en una carpeta limpia antes de cargarla. Las
  cuatro tienen el mismo código que `v1.1` y solo cambian la etiqueta de `VERSION`.

### 5.1 All at once (`v2-allatonce`)

| Dato | Valor |
|---|---|
| Política y lote | `AllAtOnce` (sin lotes: se actualiza el 100 % de las instancias) |
| Versión anterior → nueva | `v1.1` → `v2-allatonce` |
| Fecha y hora de inicio | 15 de octubre de 2026, 21:51:25 (UTC-5) |
| (a) Instancias antes / máximo durante / después | 3 / 3 / 3 (`t3.micro`, una por zona); no se crearon instancias adicionales |
| (c) Tiempo total | **0 min 21 s**: de "Environment update is starting" (21:51:25) a "Environment update completed successfully" (21:51:46) |
| (d) Instancias iniciales o nuevas | **Iniciales**: los mismos 3 IDs antes y después (`i-087c560a12e0ffa07`, `i-05159b8ef3f935e9d` e `i-0f7acc80fdc24a7d3`), lanzados el 15 de octubre a las 14:44:09 |
| Solicitudes del monitor: total / no 200 | 480 / 5: 475 con `200` y 5 con `502`; disponibilidad del 98,96 % |
| Caída observada | 5 s: de 21:51:34.9 hasta la siguiente respuesta `200` a las 21:51:39.9 |
| Ventana con dos versiones respondiendo | Ninguna |

**(b) Cómo se validó que el despliegue estaba en ejecución:** con cuatro fuentes. El monitor
consultó `/ping` cada segundo y registró la versión de cada respuesta: `v1.1` hasta las 21:51:33 y
`v2-allatonce` desde las 21:51:39. Los eventos del entorno marcan el inicio, el despliegue en las
instancias y el final. La pestaña *Estado y supervisión* mostró las 3 instancias en *Ok* con la
implementación 3. Y `/ping` respondió `{"version": "v2-allatonce"}` al terminar.

**(e) Capturas:**

![Figura 32. Política de implementación AllAtOnce](capturas/2.4a-politica.png)

![Figura 33. EC2: las 3 instancias antes de desplegar](capturas/2.4a-instancias-antes.png)

![Figura 34. v2-allatonce seleccionada; v1.1 implementada en el entorno](capturas/2.4a-versiones-antes.png)

![Figura 35. Ventana Implementar: v2-allatonce en Blacklist-devops-env](capturas/2.4a-implementar.png)

![Figura 36. Eventos del despliegue, de 21:51:25 a 21:51:50](capturas/2.4a-eventos.png)

![Figura 37. Estado y supervisión: v2-allatonce, 3 instancias en Ok con la implementación 3](capturas/2.4a-salud-despues.png)

![Figura 38. Historial de implementaciones: All at once, 21 s](capturas/2.4a-implementaciones.png)

![Figura 39. EC2: los mismos 3 IDs después del despliegue](capturas/2.4a-instancias-despues.png)

![Figura 40. /ping responde v2-allatonce](capturas/2.4a-ping.png)

El registro completo del monitor está en `docs/despliegues/v2-allatonce.csv` y el detalle en
`docs/despliegues/2.4a-all-at-once.md`.

**(f) Hallazgos:**
- **Disponibilidad:** hubo una caída total de 5 s (5 solicitudes seguidas con `502`) entre la última
  respuesta de `v1.1` y la primera de `v2-allatonce`. Las 3 instancias reiniciaron la aplicación al
  mismo tiempo y el balanceador no tuvo ninguna instancia sana a la cual enviar las solicitudes.
- **Capacidad:** durante la caída atendían 0 de 3 instancias; antes y después, las 3.
- **Duración:** 21 s, la más corta, porque no crea instancias ni actualiza por lotes.
- **Costo:** sin instancias adicionales.
- **Rollback:** volver a `v1.1` exige otro despliegue completo, con otra caída.
- **Salud del entorno:** la salud mejorada pasó a *Info* 4 s después de terminar el despliegue y
  volvió a *Ok* un minuto más tarde. La consola no muestra la caída; el monitor sí la registra.
- **Cuándo conviene:** entornos de desarrollo o pruebas, o ventanas de mantenimiento en las que se
  acepta una interrupción breve.

### 5.2 Rolling (`v3-rolling`)

| Dato | Valor |
|---|---|
| Política y lote | `Rolling`, [PENDIENTE: tipo y tamaño de lote] |
| Versión anterior → nueva | [PENDIENTE] |
| Fecha y hora de inicio | [PENDIENTE] |
| (a) Instancias antes / máximo durante / después | [PENDIENTE] |
| (c) Tiempo total | [PENDIENTE: __ min __ s] |
| (d) Instancias iniciales o nuevas | [PENDIENTE: IDs antes y después] |
| Solicitudes del monitor: total / no 200 | [PENDIENTE] |
| Ventana con dos versiones respondiendo | [PENDIENTE] |

**(b) Cómo se validó que el despliegue estaba en ejecución:** [PENDIENTE]

**(e) Capturas:** [PENDIENTE]

**(f) Hallazgos:** [PENDIENTE]

### 5.3 Rolling with additional batch (`v4-rollingbatch`)

| Dato | Valor |
|---|---|
| Política y lote | `RollingWithAdditionalBatch`, [PENDIENTE: tipo y tamaño de lote] |
| Versión anterior → nueva | [PENDIENTE] |
| Fecha y hora de inicio | [PENDIENTE] |
| (a) Instancias antes / máximo durante / después | [PENDIENTE] |
| (c) Tiempo total | [PENDIENTE: __ min __ s] |
| (d) Instancias iniciales o nuevas | [PENDIENTE: IDs antes y después] |
| Solicitudes del monitor: total / no 200 | [PENDIENTE] |
| Ventana con dos versiones respondiendo | [PENDIENTE] |

**(b) Cómo se validó que el despliegue estaba en ejecución:** [PENDIENTE]

**(e) Capturas:** [PENDIENTE]

**(f) Hallazgos:** [PENDIENTE]

### 5.4 Immutable (`v5-immutable`)

| Dato | Valor |
|---|---|
| Política | `Immutable` |
| Versión anterior → nueva | [PENDIENTE] |
| Fecha y hora de inicio | [PENDIENTE] |
| (a) Instancias antes / máximo durante / después | [PENDIENTE] |
| (c) Tiempo total | [PENDIENTE: __ min __ s] |
| (d) Instancias iniciales o nuevas | [PENDIENTE: IDs antes y después] |
| Solicitudes del monitor: total / no 200 | [PENDIENTE] |
| Ventana con dos versiones respondiendo | [PENDIENTE] |

**(b) Cómo se validó que el despliegue estaba en ejecución:** [PENDIENTE]

**(e) Capturas:** [PENDIENTE]

**(f) Hallazgos:** [PENDIENTE]

### 5.5 Comparación de las estrategias

| Estrategia | Tiempo total | Instancias (antes / máx. / después) | Caída observada | Instancias iniciales o nuevas |
|---|---|---|---|---|
| All at once | 0 min 21 s | 3 / 3 / 3 | Sí: 5 s, 5 respuestas `502` | Iniciales |
| Rolling | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Rolling with additional batch | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Immutable | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

## 6. Pruebas del API

*Soporta la verificación funcional (70 %): POST /blacklists (45 %) y GET /blacklists/<email> (25 %),
probados con Postman contra la aplicación desplegada.*

La colección de Postman `Blacklist API – Lista negra global` tiene 11 escenarios con 2 tests cada uno.
Cubren el POST válido, el POST sin motivo, el duplicado (409), el email con formato inválido, el
`app_uuid` que no es UUID y el motivo de más de 255 caracteres (400), la falta de token (401), la
consulta de un email que está y de uno que no está, y el health check. Cada endpoint está documentado
con ejemplos de solicitud y respuesta en la documentación publicada (sección 3). La colección y los
environments `blacklist-local` y `blacklist-aws` están versionados en `postman/`; entre ellos solo
cambia `base_url`.

| Prueba | Entorno | Resultado |
|---|---|---|
| Pruebas automáticas (pytest) | SQLite en memoria | 85 pruebas aprobadas (60 de la aplicación y 25 del monitor de disponibilidad), cobertura del 100 % de `app/` |
| Colección de Postman | Aplicación local con SQLite | 22 de 22 tests aprobados |
| Colección de Postman | Gunicorn y PostgreSQL en contenedores | 22 de 22 tests aprobados |
| IP del cliente con `X-Forwarded-For` | Gunicorn y PostgreSQL en contenedores | Se guarda la IP del cliente enviada en el encabezado |
| Persistencia después de reiniciar | Gunicorn y PostgreSQL en contenedores | Los registros se conservan y el GET responde 200 |
| Paquete `v1` antes de cargarlo | Carpeta limpia, Gunicorn en contenedor | Paquete verificado y cargado con el mismo SHA-256 |
| Paquetes `v2-allatonce` a `v5-immutable` antes de cargarlos | Carpeta limpia, Gunicorn en contenedor | `/ping` con su etiqueta, POST 201, GET 200 y 401 sin token en los cuatro |
| POST y GET | Entorno de Beanstalk con `v1.1` | 201 y 200 contra RDS (figuras 28 y 29) |
| Colección de Postman | Entorno de Beanstalk con `v1.1` | 22 de 22 tests aprobados, 0 errores, respuesta promedio de 129 ms |
| IP del cliente detrás del balanceador | Entorno de Beanstalk | Con `v1`, la del balanceador; con `v1.1` y `PROXY_FIX_X_FOR = 2`, la del cliente (figura 1) |

![Figura 41. Runner de Postman contra el entorno de Beanstalk: 22 de 22 tests aprobados](capturas/2.3b-runner-aws.png)

El detalle está en `docs/pruebas/2.3-pruebas-locales.md` (local), `docs/pruebas/2.5-prueba-paquete-v1.md`
(paquete) y `docs/pruebas/2.3b-pruebas-aws.md` (AWS).

## 7. Limitaciones y decisiones

*Complementa los puntos 1 y 2 del documento: restricciones del plan gratuito y decisiones técnicas del
equipo.*

**Plan gratuito de AWS.** La cuenta del equipo usa el plan gratuito, que impone restricciones:
- Una sola región: todo el despliegue está en `us-east-2` (Ohio).
- Sin grupos de IAM: los permisos se asignan con los roles del proyecto y las personas se agregan por
  la página del equipo de la cuenta.
- Algunas opciones de la consola muestran el aviso de "características avanzadas" y no se activan. Se
  verificó que la política de despliegue *Rolling* se puede elegir sin ese aviso, y se aplicó con lote
  fijo de 1. *All at once* es la política por defecto del entorno.
  [PENDIENTE: confirmar si *Rolling with additional batch* e *Immutable* se aplican sin el aviso.]
- Para controlar el costo, el entorno solo está encendido mientras se trabaja: se encendió para el
  primer despliegue y sigue así durante las pruebas contra AWS y las estrategias, hasta grabar el
  video. Después se termina el entorno y se elimina la RDS con un snapshot final. La configuración
  guardada `blacklist-base`, el snapshot y las versiones cargadas permiten recrearlo con la misma URL.
  El costo de referencia con el entorno encendido es de unos 0,07 USD por hora, y el balanceador es el
  componente que más pesa.

**Postman gratuito.** El workspace es público y pertenece al equipo de Postman del grupo, como lo
permite el enunciado. Para colaborar, la colección y los environments se exportan en formato JSON y se
versionan en `postman/`. El token solo se carga como valor actual de la variable, nunca como valor
inicial, para que no quede publicado.

**Versión de Flask.** El enunciado permite usar las versiones que el equipo prefiera. Se eligió Flask
3.1 (3.1.3) sobre Python 3.13 para trabajar con versiones con soporte, en lugar de Flask 1.1.4. La
migración implicó estos cambios:
- `@jwt_required()` con paréntesis (Flask-JWT-Extended 4.x).
- Manejadores de token ausente o inválido que responden 401, porque Flask-JWT-Extended 4.x responde
  422 por defecto. `PROPAGATE_EXCEPTIONS = True` para que Flask-RESTful no convierta esos errores en
  500.
- Consultas con la sintaxis de SQLAlchemy 2 (`db.select`) y fechas con zona horaria.
- Driver psycopg 3 en lugar de psycopg2, con URL `postgresql://`.

**Token estático.** El enunciado permite definir el token "por simplicidad" de forma estática. El
equipo usa un único token firmado con la clave del entorno (`JWT_SECRET_KEY`), sin expiración, generado
una vez con `scripts/generar_token.py`. No hay endpoints de registro, inicio de sesión ni renovación.

**Health check `/ping`.** Responde solo `{"version": ...}`, sin token y sin consultar la base. Así el
balanceador no marca las instancias como no saludables por un problema de credenciales o de la base, y
la versión permite seguir cada estrategia de despliegue.

**IP del cliente detrás del balanceador.** La prueba local simulaba un solo proxy, pero en Beanstalk
hay dos: el balanceador y el nginx de cada instancia. Con `v1` se guardaba la IP del balanceador. En
lugar de fijar otro valor en el código, el número de saltos se configura con la propiedad
`PROXY_FIX_X_FOR` (por defecto 1), que en el entorno vale 2. No se usa un valor mayor que el número
real de proxies, porque un cliente podría enviar un `X-Forwarded-For` falso y se guardaría esa IP. El
hallazgo se corrigió con `v1.1` antes de las estrategias, así que las cuatro versiones guardan la IP
del cliente.

**Configuración de la aplicación.** `APP_ENV` acepta `development`, `production` o `testing`; si queda
vacía se usa `development`. En el entorno de Beanstalk vale `production`. `PROXY_FIX_X_FOR` debe ser un
entero mayor o igual a 1; otro valor detiene el arranque con un mensaje claro.

## 8. Conclusiones

*Cierra el punto 2 del documento (20 %) con la comparación de las estrategias.*

[PENDIENTE: conclusiones a partir de los resultados de las estrategias y de las pruebas contra AWS.
Puntos a cubrir: estrategia recomendada para este servicio y por qué, compromiso entre tiempo,
disponibilidad y costo observado, y lecciones del despliegue manual.]
