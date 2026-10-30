import io
import urllib.error

import pytest

from scripts import ambiente_aws as ambiente

ENTORNO_ID = "e-prueba"
GRUPO_ID = "sg-prueba"
ENTORNO_LISTO = {"Status": "Ready", "EnvironmentId": ENTORNO_ID, "Health": "Green", "VersionLabel": "b0e9d03"}
ENTORNO_TERMINADO = {"Status": "Terminated", "EnvironmentId": "e-anterior", "DateUpdated": "2026-10-30T00:42:18Z"}
ENTORNO_TERMINADO_ANTIGUO = {"Status": "Terminated", "EnvironmentId": "e-antiguo", "DateUpdated": "2026-10-17T23:15:00Z"}
COMANDOS_DE_LECTURA = ("describe-", "check-dns-availability")


class AwsFalso:
    def __init__(self, entornos=(ENTORNO_LISTO,), base_datos="available", plantillas=(), snapshots=(), url=False):
        self.llamadas = []
        self.entornos = list(entornos)
        self.base_datos = base_datos
        self.plantillas = list(plantillas)
        self.snapshots = list(snapshots)
        self.url = url

    def __call__(self, argumentos):
        self.llamadas.append(argumentos)
        accion = argumentos[1]
        if accion == "describe-environments":
            return {"Environments": self.entornos}
        if accion == "describe-db-instances":
            if not self.base_datos:
                raise ambiente.ErrorAws("DBInstanceNotFound")
            return {"DBInstances": [{"DBInstanceStatus": self.base_datos}]}
        if accion == "describe-applications":
            return {"Applications": [{"ConfigurationTemplates": self.plantillas}]}
        if accion == "describe-db-snapshots":
            return {"DBSnapshots": [{"DBSnapshotIdentifier": nombre} for nombre in self.snapshots]}
        if accion == "describe-security-groups":
            return {"SecurityGroups": [{"GroupId": GRUPO_ID}]}
        if accion == "check-dns-availability":
            return {"Available": self.url}
        if accion == "terminate-environment":
            self.entornos = [ENTORNO_TERMINADO]
        if accion in ("create-environment", "rebuild-environment"):
            self.entornos = [ENTORNO_LISTO]
        return {}

    def acciones(self):
        return [llamada[1] for llamada in self.llamadas if not llamada[1].startswith(COMANDOS_DE_LECTURA)]


def estado(**valores):
    return ambiente.Estado(**valores)


def acciones(plan):
    return [paso.comando[1] if paso.comando else "esperar" for paso in plan.pasos]


def test_consulta_el_estado_completo():
    aws = AwsFalso(
        entornos=[ENTORNO_TERMINADO_ANTIGUO, ENTORNO_TERMINADO, ENTORNO_LISTO],
        plantillas=[ambiente.PLANTILLA],
        snapshots=[ambiente.SNAPSHOT_RESPALDO],
    )

    leido = ambiente.consultar_estado(aws)

    assert leido == ambiente.Estado(
        entorno="Ready",
        entorno_id=ENTORNO_ID,
        terminado_id="e-anterior",
        salud="Green",
        version="b0e9d03",
        base_datos="available",
        plantilla=True,
        snapshots=(ambiente.SNAPSHOT_RESPALDO,),
        grupo_base_datos=GRUPO_ID,
        url_disponible=False,
    )


def test_sin_rds_ni_entorno_activo():
    leido = ambiente.consultar_estado(AwsFalso(entornos=[ENTORNO_TERMINADO], base_datos="", url=True))

    assert not leido.entorno_activo
    assert leido.base_datos == ""
    assert leido.url_disponible
    assert "no existe" in ambiente.formatear_estado(leido)


def test_apagado_completo_guarda_plantilla_respalda_termina_y_detiene():
    actual = estado(entorno="Ready", entorno_id=ENTORNO_ID, base_datos="available")

    plan = ambiente.planear_apagado(actual, AwsFalso())

    assert acciones(plan) == [
        "create-configuration-template",
        "update-configuration-template",
        "validate-configuration-settings",
        "create-db-snapshot",
        "wait",
        "terminate-environment",
        "esperar",
        "stop-db-instance",
    ]
    assert ENTORNO_ID in plan.pasos[0].comando
    assert ambiente.OPCION_INVALIDA in plan.pasos[1].comando
    assert plan.avisos == [ambiente.MENSAJE_IRREVERSIBLE]


def test_apagado_no_repite_la_plantilla_ni_el_snapshot():
    actual = estado(
        entorno="Ready", base_datos="available", plantilla=True, snapshots=(ambiente.SNAPSHOT_RESPALDO,)
    )

    plan = ambiente.planear_apagado(actual, AwsFalso())

    assert acciones(plan) == ["validate-configuration-settings", "terminate-environment", "esperar", "stop-db-instance"]


def test_apagado_con_todo_apagado_solo_valida_la_plantilla():
    plan = ambiente.planear_apagado(estado(base_datos="stopped", plantilla=True), AwsFalso())

    assert acciones(plan) == ["validate-configuration-settings"]
    assert plan.avisos == []


def test_la_validacion_falla_solo_con_mensajes_de_error():
    ambiente.verificar_validacion({"Messages": [{"Severity": "warning", "Message": "aviso"}]})

    with pytest.raises(ambiente.ErrorAws, match="ServiceRoleForManagedUpdates"):
        ambiente.verificar_validacion(
            {"Messages": [{"Severity": "error", "Message": "Invalid option ServiceRoleForManagedUpdates"}]}
        )


def test_levantar_con_rds_detenida_la_inicia_y_crea_el_entorno():
    actual = estado(base_datos="stopped", plantilla=True, url_disponible=True)

    plan = ambiente.planear_levantamiento(actual, AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL)

    assert acciones(plan) == ["start-db-instance", "wait", "create-environment", "esperar"]
    creacion = plan.pasos[2].comando
    assert creacion[creacion.index("--cname-prefix") + 1] == ambiente.PREFIJO_URL
    assert creacion[creacion.index("--template-name") + 1] == ambiente.PLANTILLA
    assert creacion[creacion.index("--version-label") + 1] == "b0e9d03"


def test_levantar_sin_rds_la_restaura_privada_con_su_grupo():
    actual = estado(
        plantilla=True, url_disponible=True, snapshots=(ambiente.SNAPSHOT_FINAL,), grupo_base_datos=GRUPO_ID
    )

    plan = ambiente.planear_levantamiento(actual, AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL)

    restauracion = plan.pasos[0].comando
    assert restauracion[1] == "restore-db-instance-from-db-snapshot"
    assert "--no-publicly-accessible" in restauracion
    assert restauracion[restauracion.index("--vpc-security-group-ids") + 1] == GRUPO_ID
    assert restauracion[restauracion.index("--db-snapshot-identifier") + 1] == ambiente.SNAPSHOT_FINAL


def test_levantar_con_todo_encendido_no_hace_nada():
    plan = ambiente.planear_levantamiento(
        estado(entorno="Ready", base_datos="available"), AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL
    )

    assert plan.pasos == []


@pytest.mark.parametrize(
    "actual, mensaje",
    [
        (estado(plantilla=True, url_disponible=True, grupo_base_datos=GRUPO_ID), "snapshot"),
        (estado(plantilla=True, url_disponible=True, snapshots=(ambiente.SNAPSHOT_FINAL,)), "grupo de seguridad"),
        (estado(base_datos="stopping", plantilla=True, url_disponible=True), "stopping"),
        (estado(base_datos="available", url_disponible=True), "plantilla"),
        (estado(base_datos="available", plantilla=True), "prefijo de URL"),
    ],
)
def test_levantar_se_detiene_si_falta_algo(actual, mensaje):
    with pytest.raises(ambiente.ErrorAws, match=mensaje):
        ambiente.planear_levantamiento(actual, AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL)


def test_eliminar_rds_usa_el_snapshot_final():
    plan = ambiente.planear_eliminacion_rds(estado(base_datos="available"), ambiente.SNAPSHOT_FINAL)

    comando = plan.pasos[0].comando
    assert comando[1] == "delete-db-instance"
    assert comando[comando.index("--final-db-snapshot-identifier") + 1] == ambiente.SNAPSHOT_FINAL


@pytest.mark.parametrize(
    "actual",
    [estado(base_datos="stopped"), estado(base_datos="available", snapshots=(ambiente.SNAPSHOT_FINAL,))],
)
def test_eliminar_rds_exige_rds_disponible_y_snapshot_nuevo(actual):
    with pytest.raises(ambiente.ErrorAws):
        ambiente.planear_eliminacion_rds(actual, ambiente.SNAPSHOT_FINAL)


def test_espera_hasta_que_el_entorno_llega_al_estado():
    respuestas = [[{"Status": "Launching"}], [{"Status": "Launching"}], [ENTORNO_LISTO]]
    pausas = []

    def aws(argumentos):
        return {"Environments": respuestas.pop(0)}

    ambiente.esperar_entorno(aws, "Ready", dormir=pausas.append)

    assert pausas == [ambiente.PAUSA_SONDEO, ambiente.PAUSA_SONDEO]


def test_la_espera_se_agota():
    with pytest.raises(ambiente.ErrorAws, match="Terminated"):
        ambiente.esperar_entorno(AwsFalso(), "Terminated", dormir=lambda segundos: None, intentos=2)


def test_prueba_en_seco_no_cambia_nada():
    aws = AwsFalso(plantillas=[ambiente.PLANTILLA])
    salida = []

    codigo = ambiente.main(["apagar"], aws=aws, mostrar=salida.append)

    assert codigo == ambiente.CODIGO_EXITO
    assert aws.acciones() == []
    assert salida[-1] == ambiente.MENSAJE_PRUEBA_EN_SECO
    assert any("aws elasticbeanstalk terminate-environment" in linea for linea in salida)


def test_apagar_aplicado_ejecuta_los_pasos_en_orden():
    aws = AwsFalso(plantillas=[ambiente.PLANTILLA], snapshots=[ambiente.SNAPSHOT_RESPALDO])

    codigo = ambiente.main(["apagar", "--aplicar"], aws=aws, mostrar=lambda linea: None)

    assert codigo == ambiente.CODIGO_EXITO
    assert aws.acciones() == ["validate-configuration-settings", "terminate-environment", "stop-db-instance"]


def test_levantar_aplicado_crea_el_entorno_y_verifica_ping():
    aws = AwsFalso(entornos=[], base_datos="stopped", plantillas=[ambiente.PLANTILLA], url=True)
    salida = []

    codigo = ambiente.main(
        ["levantar", "--aplicar", "--version", "v5-immutable"],
        aws=aws,
        ping=lambda: '{"version": "v5-immutable"}',
        mostrar=salida.append,
    )

    assert codigo == ambiente.CODIGO_EXITO
    assert aws.acciones() == ["start-db-instance", "wait", "create-environment"]
    creacion = next(llamada for llamada in aws.llamadas if llamada[1] == "create-environment")
    assert creacion[-1] == "v5-immutable"
    assert any("/ping responde" in linea for linea in salida)


def test_un_error_de_aws_termina_con_codigo_de_error():
    salida = []

    codigo = ambiente.main(
        ["levantar"], aws=AwsFalso(entornos=[], base_datos="available"), mostrar=salida.append
    )

    assert codigo == ambiente.CODIGO_ERROR
    assert salida[-1].startswith("ERROR:")


def test_estado_solo_consulta():
    aws = AwsFalso()

    assert ambiente.main(["estado"], aws=aws, mostrar=lambda linea: None) == ambiente.CODIGO_EXITO
    assert aws.acciones() == []


class RespuestaFalsa(io.BytesIO):
    def __init__(self, cuerpo, status=200):
        super().__init__(cuerpo)
        self.status = status


def test_ping_reintenta_hasta_responder():
    respuestas = [urllib.error.URLError("sin conexión"), RespuestaFalsa(b'{"version": "b0e9d03"}')]

    def abrir(url, timeout):
        respuesta = respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    assert ambiente.verificar_ping(abrir=abrir, dormir=lambda segundos: None) == '{"version": "b0e9d03"}'


def test_ping_falla_despues_de_los_intentos():
    def abrir(url, timeout):
        return RespuestaFalsa(b"", status=503)

    with pytest.raises(ambiente.ErrorAws):
        ambiente.verificar_ping(abrir=abrir, dormir=lambda segundos: None, intentos=2)


def test_eliminar_rds_en_seco_muestra_el_snapshot_final():
    salida = []

    codigo = ambiente.main(["eliminar-rds"], aws=AwsFalso(), mostrar=salida.append)

    assert codigo == ambiente.CODIGO_EXITO
    assert any(f"--final-db-snapshot-identifier {ambiente.SNAPSHOT_FINAL}" in linea for linea in salida)


def test_plan_vacio_lo_indica():
    salida = []

    ambiente.mostrar_plan(ambiente.Plan(), salida.append)

    assert salida == [ambiente.MENSAJE_SIN_PASOS]


class ProcesoFalso:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_llama_a_la_cli_en_la_region_del_proyecto(monkeypatch):
    llamadas = []

    def ejecutar(comando, **opciones):
        llamadas.append(comando)
        return ProcesoFalso(stdout='{"Available": true}')

    monkeypatch.setattr(ambiente.subprocess, "run", ejecutar)

    assert ambiente.llamar_aws(["elasticbeanstalk", "check-dns-availability"]) == {"Available": True}
    assert llamadas[0][:3] == ["aws", "elasticbeanstalk", "check-dns-availability"]
    assert llamadas[0][-4:] == ["--region", ambiente.REGION, "--output", "json"]


def test_salida_vacia_y_error_de_la_cli(monkeypatch):
    respuestas = [ProcesoFalso(), ProcesoFalso(returncode=255, stderr="DBInstanceNotFound\n")]
    monkeypatch.setattr(ambiente.subprocess, "run", lambda comando, **opciones: respuestas.pop(0))

    assert ambiente.llamar_aws(["rds", "stop-db-instance"]) == {}
    with pytest.raises(ambiente.ErrorAws, match="DBInstanceNotFound"):
        ambiente.llamar_aws(["rds", "describe-db-instances"])


def test_consulta_los_entornos_terminados_de_las_ultimas_seis_semanas():
    aws = AwsFalso()
    ahora = ambiente.datetime(2026, 10, 30, 12, 0, tzinfo=ambiente.timezone.utc)

    ambiente.consultar_entornos(aws, ahora=lambda: ahora)

    consulta = aws.llamadas[0]
    assert "--include-deleted" in consulta
    assert consulta[consulta.index("--included-deleted-back-to") + 1] == "2026-09-18T12:00:00Z"


def test_levantar_sin_plantilla_restaura_el_entorno_terminado():
    actual = estado(base_datos="available", terminado_id="e-anterior", url_disponible=True)

    plan = ambiente.planear_levantamiento(actual, AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL)

    assert acciones(plan) == ["rebuild-environment", "esperar"]
    assert plan.pasos[0].comando[-1] == "e-anterior"


def test_levantar_prefiere_la_plantilla_a_la_restauracion():
    actual = estado(base_datos="available", plantilla=True, terminado_id="e-anterior", url_disponible=True)

    plan = ambiente.planear_levantamiento(actual, AwsFalso(), "b0e9d03", ambiente.SNAPSHOT_FINAL)

    assert acciones(plan) == ["create-environment", "esperar"]


def test_levantar_aplicado_restaura_el_entorno_terminado():
    aws = AwsFalso(entornos=[ENTORNO_TERMINADO], base_datos="stopped", url=True)

    codigo = ambiente.main(["levantar", "--aplicar"], aws=aws, ping=lambda: "{}", mostrar=lambda linea: None)

    assert codigo == ambiente.CODIGO_EXITO
    assert aws.acciones() == ["start-db-instance", "wait", "rebuild-environment"]
