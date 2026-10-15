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
| Configuración | `DATABASE_URL`, `JWT_SECRET_KEY` y `APP_ENV` como propiedades del entorno; ningún secreto en el repositorio |
| Configuración reproducible | Configuración guardada `blacklist-base`, con la que se recrea el entorno con la misma URL |

Para guardar la IP del cliente y no la del balanceador, la aplicación lee el encabezado
`X-Forwarded-For` con `ProxyFix` de Werkzeug. Se verificó en local con un proxy simulado (sección 6).
[PENDIENTE: resultado de la verificación en el entorno de Beanstalk, donde la solicitud pasa por el
balanceador y por nginx (#35).]

## 3. Enlaces de la entrega

| Recurso | Enlace |
|---|---|
| Repositorio de GitHub | https://github.com/mc-torreso1-uniandes-edu-co/misw-4304-blacklist-devops |
| URL del entorno | http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com |
| Workspace de Postman | https://www.postman.com/misw-4304-202615-devops/blacklist-devops/overview |
| Documentación publicada del API | https://documenter.getpostman.com/view/58851546/2sBYHRVMSR |
| Video de sustentación | [PENDIENTE: enlace del video] |

El entorno se enciende solo durante el trabajo y la grabación del video, según la aclaración del
tutor sobre los recursos de AWS. La configuración guardada permite volver a proveerlo con la misma URL
si se cita a una sustentación síncrona.

## 4. Paso a paso de la creación y el despliegue en AWS Elastic Beanstalk

*Cubre el punto 1 del documento (10 %): a. configuración de RDS, b. configuración del proyecto en
Beanstalk y c. configuración de los health checks.*

La infraestructura se creó manualmente por la consola de AWS, sin servicios de CI/CD. Antes de crear
los recursos se verificó la cuenta, la región y la cuota de vCPU, que limita cuántas instancias
pueden existir a la vez durante las estrategias que agregan instancias.

![Figura 1. Cuenta y región us-east-2](capturas/2-cuenta-region.png)

![Figura 2. Cuota de vCPU On-Demand de la cuenta (32)](capturas/2-cuota-vcpu.png)

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

![Figura 3. Selección del motor PostgreSQL](capturas/3a-rds-motor-postgresql.png)

![Figura 4. Plantilla de capa gratuita](capturas/3a-rds-capa-gratuita.png)

![Figura 5. Identificador de la base y usuario maestro](capturas/3a-rds-identificador.png)

![Figura 6. Credenciales autoadministradas](capturas/3a-rds-credenciales.png)

![Figura 7. Clase de instancia y almacenamiento](capturas/3a-rds-clase-almacenamiento.png)

![Figura 8. Conectividad, sin acceso público](capturas/3a-rds-conectividad.png)

![Figura 9. Grupo de seguridad de la base](capturas/3a-rds-grupo-seguridad.png)

![Figura 10. Supervisión](capturas/3a-rds-supervision.png)

![Figura 11. Opciones de base de datos](capturas/3a-rds-opciones.png)

![Figura 12. Mantenimiento](capturas/3a-rds-mantenimiento.png)

![Figura 13. Base de datos creada](capturas/3a-rds-creada.png)

![Figura 14. Regla de entrada de blacklist-db-sg: 5432 desde blacklist-app-sg](capturas/3b-rds-sg-entrada.png)

La cadena de conexión se registra solo como propiedad `DATABASE_URL` del entorno de Beanstalk. Las
tablas las crea la aplicación al iniciar.

### 4.b Configuración del proyecto en AWS Beanstalk

Antes del entorno se creó el grupo de seguridad de las instancias, `blacklist-app-sg`, sin reglas de
entrada. Se conserva entre ventanas de trabajo para que la regla de la base siga vigente cada vez que
se recrea el entorno.

![Figura 15. Grupo de seguridad de las instancias](capturas/4-app-sg.png)

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
| Propiedades del entorno | `APP_ENV`, `DATABASE_URL`, `JWT_SECRET_KEY` (valores fuera del documento) |

![Figura 16. Modo estándar y nombre del entorno](capturas/5a-eb-general.png)

![Figura 17. Opciones de la plataforma, rol de servicio y perfil de instancia](capturas/5b-eb-opciones-plataforma-roles.png)

![Figura 18. Escalado de 3 a 6 instancias y balanceador](capturas/5c-eb-escalado.png)

![Figura 19. Cómputo: t3.micro, x86_64](capturas/5d-eb-computo.png)

![Figura 20. Redes, subredes y grupo de seguridad de las instancias](capturas/5e-eb-redes.png)

![Figura 21. Subredes del balanceador](capturas/5g-eb-subredes-elb.png)

![Figura 22. Entorno en estado Ok y configuración guardada](capturas/5h-eb-entorno-ok.png)

La versión `v1` se empaquetó desde `main` con el script del repositorio (`scripts/empaquetar.py`),
que genera el `.zip` con el archivo `VERSION` que devuelve `/ping`. El paquete se probó antes de
cargarlo y se desplegó como versión de aplicación `v1`.

[PENDIENTE: captura del entorno con la versión `v1` desplegada, salud *Ok* con 3 instancias y `/ping`
respondiendo `{"version": "v1"}` (#35).]

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

![Figura 23. Comprobación de estado del proceso default: /ping, código 200](capturas/5f-eb-healthcheck.png)

[PENDIENTE: captura de la pestaña *Health* del entorno con las 3 instancias en *Ok* (#35).]

## 5. Estrategias de despliegue

*Cubre el punto 2 del documento (20 %): cuatro estrategias con más de una instancia, cada una con los
puntos a–f.*

Las estrategias se ejecutaron sobre el mismo entorno, con Auto Scaling de mínimo 3 y máximo 6
instancias, en este orden: All at once (`v2-allatonce`), Rolling (`v3-rolling`), Rolling with
additional batch (`v4-rollingbatch`) e Immutable (`v5-immutable`). Cada versión cambia la etiqueta que
devuelve `/ping`, lo que permite ver qué instancias atienden la versión nueva durante el despliegue.

**Método de medición, común a las cuatro estrategias:**
- Tiempo total: desde el evento de inicio del despliegue hasta el evento de finalización en la pestaña
  *Events* del entorno.
- Instancias: lista de instancias del entorno en EC2 antes, durante y después del despliegue.
- Disponibilidad: un monitor consulta `/ping` a intervalos regulares durante todo el despliegue y
  registra el código HTTP y la versión de cada respuesta. Los registros se guardan en
  `docs/despliegues/`.

### 5.1 All at once (`v2-allatonce`)

| Dato | Valor |
|---|---|
| Política y lote | `AllAtOnce` |
| Versión anterior → nueva | [PENDIENTE] |
| Fecha y hora de inicio | [PENDIENTE] |
| (a) Instancias antes / máximo durante / después | [PENDIENTE] |
| (c) Tiempo total | [PENDIENTE: __ min __ s] |
| (d) Instancias iniciales o nuevas | [PENDIENTE: IDs antes y después] |
| Solicitudes del monitor: total / no 200 | [PENDIENTE] |

**(b) Cómo se validó que el despliegue estaba en ejecución:** [PENDIENTE: eventos, pestaña *Health* y
monitor de `/ping`.]

**(e) Capturas:** [PENDIENTE: política de despliegue, eventos de inicio y fin, *Health* durante el
despliegue, instancias EC2 antes y después, resumen del monitor.]

**(f) Hallazgos:** [PENDIENTE: disponibilidad, capacidad durante el despliegue, duración comparada,
costo, riesgo y *rollback*, cuándo se recomienda.]

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
| All at once | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Rolling | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Rolling with additional batch | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Immutable | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

## 6. Pruebas del API

La colección de Postman `Blacklist API – Lista negra global` tiene 11 escenarios con 2 tests cada uno.
Cubren el POST válido, el POST sin motivo, el duplicado (409), el email con formato inválido, el
`app_uuid` que no es UUID y el motivo de más de 255 caracteres (400), la falta de token (401), la
consulta de un email que está y de uno que no está, y el health check. Cada endpoint está documentado
con ejemplos de solicitud y respuesta en la documentación publicada (sección 3). La colección y los
environments `blacklist-local` y `blacklist-aws` están versionados en `postman/`; entre ellos solo
cambia `base_url`.

| Prueba | Entorno | Resultado |
|---|---|---|
| Pruebas automáticas (pytest) | SQLite en memoria | 50 pruebas aprobadas, cobertura del 100 % |
| Colección de Postman | Aplicación local con SQLite | 22 de 22 tests aprobados |
| Colección de Postman | Gunicorn y PostgreSQL en contenedores | 22 de 22 tests aprobados |
| IP del cliente con `X-Forwarded-For` | Gunicorn y PostgreSQL en contenedores | Se guarda la IP del cliente enviada en el encabezado |
| Persistencia después de reiniciar | Gunicorn y PostgreSQL en contenedores | Los registros se conservan y el GET responde 200 |
| Paquete `v1` antes de cargarlo | Contenido del `.zip` | Paquete verificado y cargado con el mismo SHA-256 |
| Colección de Postman | Entorno de Beanstalk | [PENDIENTE: resultado del runner contra la URL del entorno (#43)] |
| IP del cliente detrás del balanceador | Entorno de Beanstalk | [PENDIENTE: IP guardada en RDS (#35)] |

El detalle de las pruebas locales y del paquete está en `docs/pruebas/2.3-pruebas-locales.md` y
`docs/pruebas/2.5-prueba-paquete-v1.md`.

## 7. Limitaciones y decisiones

**Plan gratuito de AWS.** La cuenta del equipo usa el plan gratuito, que impone restricciones:
- Una sola región: todo el despliegue está en `us-east-2` (Ohio).
- Sin grupos de IAM: los permisos se asignan con los roles del proyecto y las personas se agregan por
  la página del equipo de la cuenta.
- Algunas opciones de la consola muestran el aviso de "características avanzadas" y no se activan. Se
  verificó que la política de despliegue *Rolling* se puede elegir sin ese aviso.
  [PENDIENTE: otras opciones bloqueadas encontradas durante las estrategias.]
- Para controlar el costo, el entorno se enciende solo en ventanas de trabajo y se apaga al cerrarlas:
  se termina el entorno y se detiene la RDS. La configuración guardada `blacklist-base` y las
  versiones cargadas permiten recrearlo con la misma URL. El costo de referencia con el entorno
  encendido es de unos 0,07 USD por hora, y el balanceador es el componente que más pesa.

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

**Configuración de la aplicación.** `APP_ENV` acepta `development`, `production` o `testing`; si queda
vacía se usa `development`. En el entorno de Beanstalk vale `production`.

## 8. Conclusiones

[PENDIENTE: conclusiones a partir de los resultados de las estrategias y de las pruebas contra AWS.
Puntos a cubrir: estrategia recomendada para este servicio y por qué, compromiso entre tiempo,
disponibilidad y costo observado, y lecciones del despliegue manual.]
