import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

REGION = "us-east-2"
APLICACION = "blacklist-devops"
ENTORNO = "Blacklist-devops-env"
PREFIJO_URL = "blacklist-devops-misw"
BASE_DATOS = "blacklist-db"
CLASE_BASE_DATOS = "db.t4g.micro"
GRUPO_BASE_DATOS = "blacklist-db-sg"
SUBREDES_BASE_DATOS = "default-vpc-0aa0061c21894873c"
PLANTILLA = "blacklist-entrega-2"
VERSION_POR_DEFECTO = "b0e9d03"
SNAPSHOT_RESPALDO = "blacklist-db-fin-entrega-2"
SNAPSHOT_FINAL = "blacklist-db-final-entrega-2"
OPCION_INVALIDA = "Namespace=aws:elasticbeanstalk:managedactions,OptionName=ServiceRoleForManagedUpdates"
URL_PING = f"http://{PREFIJO_URL}.{REGION}.elasticbeanstalk.com/ping"

ENTORNO_LISTO = "Ready"
ENTORNO_TERMINADO = "Terminated"
SALUD_CORRECTA = "Green"
RDS_DISPONIBLE = "available"
RDS_DETENIDA = "stopped"
SEVERIDAD_ERROR = "error"
CODIGO_HTTP_EXITO = 200

PAUSA_SONDEO = 20
INTENTOS_SONDEO = 90
INTENTOS_PING = 6
TIEMPO_ESPERA_PING = 10

COMANDO_ESTADO = "estado"
COMANDO_APAGAR = "apagar"
COMANDO_LEVANTAR = "levantar"
COMANDO_ELIMINAR_RDS = "eliminar-rds"
OPCION_APLICAR = "--aplicar"
OPCION_VERSION = "--version"
OPCION_SNAPSHOT = "--snapshot"

CODIGO_EXITO = 0
CODIGO_ERROR = 1

DESCRIPCION = "Apaga y vuelve a levantar el entorno de Beanstalk y la RDS. Sin --aplicar solo muestra los pasos."
DESCRIPCION_ESTADO = "Muestra el estado del entorno, la RDS, la plantilla y los snapshots."
DESCRIPCION_APAGAR = "Guarda la plantilla, crea un snapshot de respaldo, termina el entorno y detiene la RDS."
DESCRIPCION_LEVANTAR = "Inicia o restaura la RDS y crea el entorno desde la plantilla."
DESCRIPCION_ELIMINAR_RDS = "Elimina la RDS con snapshot final (después de la fecha oficial de la entrega)."
DESCRIPCION_APLICAR = "Ejecuta los pasos en AWS; sin la opción es una prueba en seco."
DESCRIPCION_VERSION = f"Versión de la aplicación que se despliega (por defecto {VERSION_POR_DEFECTO})."
DESCRIPCION_SNAPSHOT = "Snapshot del que se restaura la RDS si no existe, o nombre del snapshot final al eliminarla."

MENSAJE_PRUEBA_EN_SECO = "Prueba en seco: no se cambió nada. Para ejecutar, repetir con --aplicar."
MENSAJE_SIN_PASOS = "No hay nada que hacer."
MENSAJE_PASO = "{numero}. {descripcion}"
MENSAJE_COMANDO = "   aws {comando}"
MENSAJE_ERROR = "ERROR: {mensaje}"
MENSAJE_SIN_PLANTILLA = f"No existe la plantilla {PLANTILLA}: se crea con 'apagar' mientras el entorno está activo."
MENSAJE_URL_OCUPADA = f"El prefijo de URL {PREFIJO_URL} no está disponible."
MENSAJE_SIN_SNAPSHOT = "No existe la RDS ni el snapshot {snapshot} para restaurarla."
MENSAJE_SIN_GRUPO = f"No existe el grupo de seguridad {GRUPO_BASE_DATOS} para restaurar la RDS."
MENSAJE_RDS_EN_TRANSICION = "La RDS está en estado {estado}: esperar a que termine y repetir."
MENSAJE_RDS_NO_DISPONIBLE = "La RDS debe estar disponible para eliminarla con snapshot final (estado: {estado})."
MENSAJE_SNAPSHOT_EXISTE = "Ya existe el snapshot {snapshot}: elegir otro nombre con --snapshot."
MENSAJE_PLANTILLA_INVALIDA = "La plantilla no pasó la validación: {detalle}"
MENSAJE_ESPERA_AGOTADA = "El entorno no llegó al estado {objetivo} a tiempo (último: {estado})."
MENSAJE_PING_FALLIDO = f"{URL_PING} no respondió 200."
MENSAJE_PING_CORRECTO = "/ping responde {cuerpo}"
MENSAJE_IRREVERSIBLE = "Terminar el entorno no se puede deshacer: se vuelve a crear con 'levantar'."


class ErrorAws(Exception):
    pass


ConsultaAws = Callable[[List[str]], Dict]


@dataclass(frozen=True)
class Estado:
    entorno: str = ""
    entorno_id: str = ""
    salud: str = ""
    version: str = ""
    base_datos: str = ""
    plantilla: bool = False
    snapshots: Tuple[str, ...] = ()
    grupo_base_datos: str = ""
    url_disponible: bool = False

    @property
    def entorno_activo(self) -> bool:
        return bool(self.entorno) and self.entorno != ENTORNO_TERMINADO


@dataclass(frozen=True)
class Paso:
    descripcion: str
    comando: Optional[List[str]] = None
    verificar: Optional[Callable[[Dict], None]] = None
    esperar: Optional[Callable[[], None]] = None


@dataclass
class Plan:
    pasos: List[Paso] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)


def llamar_aws(argumentos: List[str]) -> Dict:
    entorno = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    resultado = subprocess.run(
        ["aws", *argumentos, "--region", REGION, "--output", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=entorno,
    )
    if resultado.returncode != 0:
        raise ErrorAws(resultado.stderr.strip())
    return json.loads(resultado.stdout) if resultado.stdout.strip() else {}


def consultar_entorno(aws: ConsultaAws) -> Dict:
    entornos = aws(
        ["elasticbeanstalk", "describe-environments", "--application-name", APLICACION, "--environment-names", ENTORNO]
    ).get("Environments", [])
    activos = [entorno for entorno in entornos if entorno.get("Status") != ENTORNO_TERMINADO]
    return activos[0] if activos else {}


def consultar_estado(aws: ConsultaAws) -> Estado:
    entorno = consultar_entorno(aws)
    try:
        instancias = aws(["rds", "describe-db-instances", "--db-instance-identifier", BASE_DATOS])["DBInstances"]
        base_datos = instancias[0]["DBInstanceStatus"]
    except ErrorAws:
        base_datos = ""
    aplicaciones = aws(["elasticbeanstalk", "describe-applications", "--application-names", APLICACION])
    plantillas = aplicaciones["Applications"][0].get("ConfigurationTemplates", [])
    snapshots = aws(["rds", "describe-db-snapshots", "--snapshot-type", "manual"]).get("DBSnapshots", [])
    grupos = aws(
        ["ec2", "describe-security-groups", "--filters", f"Name=group-name,Values={GRUPO_BASE_DATOS}"]
    ).get("SecurityGroups", [])
    url = aws(["elasticbeanstalk", "check-dns-availability", "--cname-prefix", PREFIJO_URL])
    return Estado(
        entorno=entorno.get("Status", ""),
        entorno_id=entorno.get("EnvironmentId", ""),
        salud=entorno.get("Health", ""),
        version=entorno.get("VersionLabel", ""),
        base_datos=base_datos,
        plantilla=PLANTILLA in plantillas,
        snapshots=tuple(snapshot["DBSnapshotIdentifier"] for snapshot in snapshots),
        grupo_base_datos=grupos[0]["GroupId"] if grupos else "",
        url_disponible=bool(url.get("Available")),
    )


def formatear_estado(estado: Estado) -> str:
    entorno = f"{estado.entorno}, salud {estado.salud}, versión {estado.version}" if estado.entorno_activo else "no existe"
    return "\n".join(
        [
            f"Entorno {ENTORNO}: {entorno}",
            f"RDS {BASE_DATOS}: {estado.base_datos or 'no existe'}",
            f"Plantilla {PLANTILLA}: {'existe' if estado.plantilla else 'no existe'}",
            f"Snapshots manuales: {', '.join(estado.snapshots) or 'ninguno'}",
            f"Prefijo de URL {PREFIJO_URL}: {'libre' if estado.url_disponible else 'en uso'}",
        ]
    )


def verificar_validacion(resultado: Dict) -> None:
    errores = [
        mensaje.get("Message", "")
        for mensaje in resultado.get("Messages", [])
        if mensaje.get("Severity") == SEVERIDAD_ERROR
    ]
    if errores:
        raise ErrorAws(MENSAJE_PLANTILLA_INVALIDA.format(detalle="; ".join(errores)))


def esperar_entorno(
    aws: ConsultaAws,
    objetivo: str,
    dormir: Callable[[float], None] = time.sleep,
    intentos: int = INTENTOS_SONDEO,
) -> None:
    estado = ""
    for _ in range(intentos):
        estado = consultar_entorno(aws).get("Status", ENTORNO_TERMINADO)
        if estado == objetivo:
            return
        dormir(PAUSA_SONDEO)
    raise ErrorAws(MENSAJE_ESPERA_AGOTADA.format(objetivo=objetivo, estado=estado))


def planear_apagado(estado: Estado, aws: ConsultaAws) -> Plan:
    plan = Plan()
    if estado.entorno_activo and not estado.plantilla:
        plan.pasos += [
            Paso(
                f"Guardar la configuración del entorno como la plantilla {PLANTILLA}",
                ["elasticbeanstalk", "create-configuration-template", "--application-name", APLICACION,
                 "--template-name", PLANTILLA, "--environment-id", estado.entorno_id],
            ),
            Paso(
                "Quitar de la plantilla la opción ServiceRoleForManagedUpdates, que la consola rechaza",
                ["elasticbeanstalk", "update-configuration-template", "--application-name", APLICACION,
                 "--template-name", PLANTILLA, "--options-to-remove", OPCION_INVALIDA],
            ),
        ]
    if estado.entorno_activo or estado.plantilla:
        plan.pasos.append(
            Paso(
                f"Validar la plantilla {PLANTILLA}",
                ["elasticbeanstalk", "validate-configuration-settings", "--application-name", APLICACION,
                 "--template-name", PLANTILLA],
                verificar=verificar_validacion,
            )
        )
    if estado.base_datos == RDS_DISPONIBLE and SNAPSHOT_RESPALDO not in estado.snapshots:
        plan.pasos += [
            Paso(
                f"Crear el snapshot de respaldo {SNAPSHOT_RESPALDO}",
                ["rds", "create-db-snapshot", "--db-instance-identifier", BASE_DATOS,
                 "--db-snapshot-identifier", SNAPSHOT_RESPALDO],
            ),
            Paso(
                "Esperar a que el snapshot esté disponible",
                ["rds", "wait", "db-snapshot-available", "--db-snapshot-identifier", SNAPSHOT_RESPALDO],
            ),
        ]
    if estado.entorno_activo:
        plan.avisos.append(MENSAJE_IRREVERSIBLE)
        plan.pasos += [
            Paso(
                f"Terminar el entorno {ENTORNO}",
                ["elasticbeanstalk", "terminate-environment", "--environment-name", ENTORNO],
            ),
            Paso("Esperar a que el entorno quede terminado", esperar=lambda: esperar_entorno(aws, ENTORNO_TERMINADO)),
        ]
    if estado.base_datos == RDS_DISPONIBLE:
        plan.pasos.append(
            Paso(
                f"Detener la RDS {BASE_DATOS} (AWS la vuelve a iniciar a los 7 días)",
                ["rds", "stop-db-instance", "--db-instance-identifier", BASE_DATOS],
            )
        )
    return plan


def planear_levantamiento(estado: Estado, aws: ConsultaAws, version: str, snapshot: str) -> Plan:
    plan = Plan()
    if estado.base_datos == RDS_DETENIDA:
        plan.pasos.append(
            Paso(f"Iniciar la RDS {BASE_DATOS}", ["rds", "start-db-instance", "--db-instance-identifier", BASE_DATOS])
        )
    elif not estado.base_datos:
        if snapshot not in estado.snapshots:
            raise ErrorAws(MENSAJE_SIN_SNAPSHOT.format(snapshot=snapshot))
        if not estado.grupo_base_datos:
            raise ErrorAws(MENSAJE_SIN_GRUPO)
        plan.pasos.append(
            Paso(
                f"Restaurar la RDS {BASE_DATOS} desde el snapshot {snapshot}",
                ["rds", "restore-db-instance-from-db-snapshot", "--db-instance-identifier", BASE_DATOS,
                 "--db-snapshot-identifier", snapshot, "--db-instance-class", CLASE_BASE_DATOS,
                 "--no-publicly-accessible", "--vpc-security-group-ids", estado.grupo_base_datos,
                 "--db-subnet-group-name", SUBREDES_BASE_DATOS],
            )
        )
    elif estado.base_datos != RDS_DISPONIBLE:
        raise ErrorAws(MENSAJE_RDS_EN_TRANSICION.format(estado=estado.base_datos))
    if estado.base_datos != RDS_DISPONIBLE:
        plan.pasos.append(
            Paso(
                "Esperar a que la RDS esté disponible",
                ["rds", "wait", "db-instance-available", "--db-instance-identifier", BASE_DATOS],
            )
        )
    if not estado.entorno_activo:
        if not estado.plantilla:
            raise ErrorAws(MENSAJE_SIN_PLANTILLA)
        if not estado.url_disponible:
            raise ErrorAws(MENSAJE_URL_OCUPADA)
        plan.pasos += [
            Paso(
                f"Crear el entorno {ENTORNO} desde {PLANTILLA} con la versión {version}",
                ["elasticbeanstalk", "create-environment", "--application-name", APLICACION,
                 "--environment-name", ENTORNO, "--cname-prefix", PREFIJO_URL, "--template-name", PLANTILLA,
                 "--version-label", version],
            ),
            Paso("Esperar a que el entorno esté listo", esperar=lambda: esperar_entorno(aws, ENTORNO_LISTO)),
        ]
    return plan


def planear_eliminacion_rds(estado: Estado, snapshot: str) -> Plan:
    if estado.base_datos != RDS_DISPONIBLE:
        raise ErrorAws(MENSAJE_RDS_NO_DISPONIBLE.format(estado=estado.base_datos or "no existe"))
    if snapshot in estado.snapshots:
        raise ErrorAws(MENSAJE_SNAPSHOT_EXISTE.format(snapshot=snapshot))
    return Plan(
        pasos=[
            Paso(
                f"Eliminar la RDS {BASE_DATOS} con el snapshot final {snapshot}",
                ["rds", "delete-db-instance", "--db-instance-identifier", BASE_DATOS,
                 "--final-db-snapshot-identifier", snapshot],
            )
        ]
    )


def mostrar_plan(plan: Plan, mostrar: Callable[[str], None] = print) -> None:
    for aviso in plan.avisos:
        mostrar(aviso)
    if not plan.pasos:
        mostrar(MENSAJE_SIN_PASOS)
    for numero, paso in enumerate(plan.pasos, start=1):
        mostrar(MENSAJE_PASO.format(numero=numero, descripcion=paso.descripcion))
        if paso.comando:
            mostrar(MENSAJE_COMANDO.format(comando=" ".join(paso.comando)))


def ejecutar_plan(plan: Plan, aws: ConsultaAws, mostrar: Callable[[str], None] = print) -> None:
    for numero, paso in enumerate(plan.pasos, start=1):
        mostrar(MENSAJE_PASO.format(numero=numero, descripcion=paso.descripcion))
        if paso.comando:
            resultado = aws(paso.comando)
            if paso.verificar:
                paso.verificar(resultado)
        if paso.esperar:
            paso.esperar()


def verificar_ping(
    abrir: Callable = urllib.request.urlopen,
    dormir: Callable[[float], None] = time.sleep,
    intentos: int = INTENTOS_PING,
) -> str:
    for _ in range(intentos):
        try:
            with abrir(URL_PING, timeout=TIEMPO_ESPERA_PING) as respuesta:
                if respuesta.status == CODIGO_HTTP_EXITO:
                    return respuesta.read().decode("utf-8")
        except (urllib.error.URLError, OSError):
            pass
        dormir(PAUSA_SONDEO)
    raise ErrorAws(MENSAJE_PING_FALLIDO)


def leer_argumentos(argumentos: Optional[List[str]]) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(description=DESCRIPCION)
    comandos = analizador.add_subparsers(dest="comando", required=True)
    comandos.add_parser(COMANDO_ESTADO, help=DESCRIPCION_ESTADO)
    for nombre, ayuda, snapshot in (
        (COMANDO_APAGAR, DESCRIPCION_APAGAR, None),
        (COMANDO_LEVANTAR, DESCRIPCION_LEVANTAR, SNAPSHOT_FINAL),
        (COMANDO_ELIMINAR_RDS, DESCRIPCION_ELIMINAR_RDS, SNAPSHOT_FINAL),
    ):
        subcomando = comandos.add_parser(nombre, help=ayuda)
        subcomando.add_argument(OPCION_APLICAR, action="store_true", help=DESCRIPCION_APLICAR)
        if snapshot:
            subcomando.add_argument(OPCION_SNAPSHOT, default=snapshot, help=DESCRIPCION_SNAPSHOT)
        if nombre == COMANDO_LEVANTAR:
            subcomando.add_argument(OPCION_VERSION, default=VERSION_POR_DEFECTO, help=DESCRIPCION_VERSION)
    return analizador.parse_args(argumentos)


def main(
    argumentos: Optional[List[str]] = None,
    aws: ConsultaAws = llamar_aws,
    ping: Callable[[], str] = verificar_ping,
    mostrar: Callable[[str], None] = print,
) -> int:
    leidos = leer_argumentos(argumentos)
    try:
        estado = consultar_estado(aws)
        mostrar(formatear_estado(estado))
        if leidos.comando == COMANDO_ESTADO:
            return CODIGO_EXITO
        if leidos.comando == COMANDO_APAGAR:
            plan = planear_apagado(estado, aws)
        elif leidos.comando == COMANDO_LEVANTAR:
            plan = planear_levantamiento(estado, aws, leidos.version, leidos.snapshot)
        else:
            plan = planear_eliminacion_rds(estado, leidos.snapshot)
        if not leidos.aplicar:
            mostrar_plan(plan, mostrar)
            mostrar(MENSAJE_PRUEBA_EN_SECO)
            return CODIGO_EXITO
        ejecutar_plan(plan, aws, mostrar)
        if leidos.comando == COMANDO_LEVANTAR:
            mostrar(MENSAJE_PING_CORRECTO.format(cuerpo=ping()))
        mostrar(formatear_estado(consultar_estado(aws)))
    except ErrorAws as error:
        mostrar(MENSAJE_ERROR.format(mensaje=error))
        return CODIGO_ERROR
    return CODIGO_EXITO


if __name__ == "__main__":
    sys.exit(main())
