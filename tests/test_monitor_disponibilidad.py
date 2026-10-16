import csv
import io
import urllib.error
from datetime import datetime, timedelta, timezone

import pytest

from scripts import monitor_disponibilidad as monitor

URL_BASE = "http://entorno.ejemplo.com/"
URL_PING = "http://entorno.ejemplo.com/ping"
INICIO = datetime(2026, 10, 16, 14, 0, 0, tzinfo=timezone.utc)
VERSION_ANTERIOR = "v1.1"
VERSION_NUEVA = "v2-allatonce"


def marca(segundos):
    return INICIO + timedelta(seconds=segundos)


def registro(segundos, codigo=200, version=VERSION_ANTERIOR):
    return monitor.Registro(marca(segundos), codigo, version if codigo == 200 else "", 12.0)


class RespuestaFalsa(io.BytesIO):
    def __init__(self, cuerpo, status=200):
        super().__init__(cuerpo)
        self.status = status


def reloj_falso(*valores):
    pendientes = list(valores)
    return lambda: pendientes.pop(0)


def test_extrae_la_version_del_cuerpo_json():
    assert monitor.extraer_version(b'{"version": "v1.1"}') == "v1.1"


@pytest.mark.parametrize("cuerpo", [b"no es json", b"[1, 2]", b"{}"])
def test_version_vacia_si_el_cuerpo_no_la_trae(cuerpo):
    assert monitor.extraer_version(cuerpo) == ""


def test_consulta_exitosa_registra_codigo_version_y_latencia():
    llamadas = []

    def abrir(url, timeout):
        llamadas.append((url, timeout))
        return RespuestaFalsa(b'{"version": "v1.1"}')

    resultado = monitor.consultar_ping(URL_BASE, 3.0, abrir=abrir, reloj=reloj_falso(1.0, 1.045), ahora=lambda: INICIO)

    assert llamadas == [(URL_PING, 3.0)]
    assert resultado.codigo_http == 200
    assert resultado.version == VERSION_ANTERIOR
    assert resultado.latencia_ms == pytest.approx(45.0)
    assert resultado.exitoso
    assert resultado.error == ""


def test_consulta_con_error_http_registra_el_codigo():
    def abrir(url, timeout):
        raise urllib.error.HTTPError(url, 503, "Service Unavailable", {}, io.BytesIO(b""))

    resultado = monitor.consultar_ping(URL_BASE, 3.0, abrir=abrir, reloj=reloj_falso(0.0, 0.1), ahora=lambda: INICIO)

    assert resultado.codigo_http == 503
    assert resultado.error == "HTTP 503"
    assert resultado.version == ""
    assert not resultado.exitoso


@pytest.mark.parametrize(
    "falla, texto",
    [
        (urllib.error.URLError("connection refused"), "URLError: connection refused"),
        (TimeoutError("timed out"), "TimeoutError: timed out"),
    ],
)
def test_consulta_sin_respuesta_registra_codigo_cero(falla, texto):
    def abrir(url, timeout):
        raise falla

    resultado = monitor.consultar_ping(URL_BASE, 3.0, abrir=abrir, reloj=reloj_falso(0.0, 3.0), ahora=lambda: INICIO)

    assert resultado.codigo_http == monitor.CODIGO_SIN_RESPUESTA
    assert resultado.error == texto
    assert not resultado.exitoso


def test_fila_del_csv_usa_hora_utc_con_milisegundos():
    fila = monitor.Registro(INICIO, 200, VERSION_ANTERIOR, 45.04).como_fila()

    assert fila == ["2026-10-16T14:00:00.000Z", "200", VERSION_ANTERIOR, "45.0", ""]


def test_monitorea_hasta_el_limite_y_escribe_el_csv(tmp_path):
    ruta = tmp_path / "despliegues" / "estrategia.csv"
    respuestas = iter([registro(0), registro(1, codigo=503), registro(2, version=VERSION_NUEVA)])
    esperas = []
    lineas = []

    registros = monitor.monitorear(
        URL_BASE,
        ruta,
        [],
        intervalo=1.0,
        limite=3,
        consultar=lambda url, espera: next(respuestas),
        dormir=esperas.append,
        reloj=lambda: 0.0,
        mostrar=lineas.append,
    )

    filas = list(csv.reader(ruta.open(encoding="utf-8")))
    assert len(registros) == 3
    assert filas[0] == list(monitor.COLUMNAS_CSV)
    assert [fila[1] for fila in filas[1:]] == ["200", "503", "200"]
    assert esperas == [1.0, 1.0]
    assert lineas[1] == "14:00:01 503 - 12 ms"


def test_agrega_filas_sin_repetir_el_encabezado(tmp_path):
    ruta = tmp_path / "estrategia.csv"
    for segundos in (0, 1):
        monitor.monitorear(
            URL_BASE,
            ruta,
            [],
            limite=1,
            consultar=lambda url, espera, s=segundos: registro(s),
            mostrar=lambda texto: None,
        )

    filas = list(csv.reader(ruta.open(encoding="utf-8")))
    assert filas.count(list(monitor.COLUMNAS_CSV)) == 1
    assert len(filas) == 3


def test_resumen_sin_fallas_ni_convivencia():
    resumen = monitor.resumir([registro(0), registro(1), registro(2)])

    assert resumen.total == 3
    assert resumen.fallidas == 0
    assert resumen.disponibilidad == 100.0
    assert resumen.racha_fallas == 0
    assert resumen.convivencia_inicio is None
    assert resumen.versiones[VERSION_ANTERIOR].cantidad == 3


def test_resumen_con_caida_y_convivencia_de_versiones():
    registros = [
        registro(0),
        registro(1, codigo=503),
        registro(2, codigo=0),
        registro(3, codigo=503),
        registro(4),
        registro(5, codigo=502),
        registro(6, version=VERSION_NUEVA),
        registro(7),
        registro(8, version=VERSION_NUEVA),
        registro(9, version=VERSION_NUEVA),
    ]

    resumen = monitor.resumir(registros)

    assert resumen.exitosas == 6
    assert resumen.fallidas == 4
    assert resumen.disponibilidad == pytest.approx(60.0)
    assert (resumen.racha_fallas, resumen.racha_inicio, resumen.racha_fin) == (3, marca(1), marca(3))
    assert (resumen.convivencia_inicio, resumen.convivencia_fin) == (marca(6), marca(7))
    assert resumen.versiones[VERSION_NUEVA].primera == marca(6)
    assert resumen.versiones[VERSION_ANTERIOR].ultima == marca(7)


def test_sin_convivencia_si_la_version_nueva_aparece_despues_de_la_anterior():
    resumen = monitor.resumir([registro(0), registro(1, codigo=503), registro(2, version=VERSION_NUEVA)])

    assert resumen.convivencia_inicio is None
    assert set(resumen.versiones) == {VERSION_ANTERIOR, VERSION_NUEVA}


def test_resumen_vacio():
    resumen = monitor.resumir([])

    assert resumen.total == 0
    assert resumen.disponibilidad == 0.0
    assert monitor.formatear_resumen(resumen) == monitor.MENSAJE_SIN_REGISTROS


def test_texto_del_resumen_incluye_caida_versiones_y_convivencia():
    texto = monitor.formatear_resumen(
        monitor.resumir([registro(0), registro(1, codigo=503), registro(2, version=VERSION_NUEVA), registro(3)])
    )

    assert "Solicitudes: 4; respuestas 200: 3; no-200: 1; disponibilidad: 75.00 %" in texto
    assert "Mayor racha de no-200: 1 solicitudes seguidas" in texto
    assert f"  {VERSION_ANTERIOR}: 2 respuestas" in texto
    assert f"  {VERSION_NUEVA}: 1 respuestas" in texto
    assert "Convivencia de versiones: de 2026-10-16T14:00:02.000Z a 2026-10-16T14:00:03.000Z (1 s)" in texto


def test_texto_del_resumen_sin_fallas():
    texto = monitor.formatear_resumen(monitor.resumir([registro(0), registro(1)]))

    assert "Sin respuestas no-200." in texto
    assert "Sin convivencia de versiones." in texto


def test_main_con_limite_imprime_el_resumen(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(monitor, "consultar_ping", lambda url, espera: registro(0))
    monkeypatch.setattr(monitor.time, "sleep", lambda segundos: None)
    ruta = tmp_path / "estrategia.csv"

    codigo = monitor.main([URL_BASE, str(ruta), "--solicitudes", "2", "--intervalo", "0"])

    salida = capsys.readouterr().out
    assert codigo == monitor.CODIGO_EXITO
    assert "Solicitudes: 2; respuestas 200: 2" in salida
    assert ruta.exists()


def test_main_detenido_con_ctrl_c_conserva_lo_registrado(tmp_path, monkeypatch, capsys):
    llamadas = []

    def consultar(url, espera):
        if llamadas:
            raise KeyboardInterrupt
        llamadas.append(url)
        return registro(0)

    monkeypatch.setattr(monitor, "consultar_ping", consultar)
    monkeypatch.setattr(monitor.time, "sleep", lambda segundos: None)

    codigo = monitor.main([URL_BASE, str(tmp_path / "estrategia.csv")])

    assert codigo == monitor.CODIGO_EXITO
    assert "Solicitudes: 1; respuestas 200: 1" in capsys.readouterr().out


def test_main_sin_registros_devuelve_error(tmp_path, monkeypatch, capsys):
    def consultar(url, espera):
        raise KeyboardInterrupt

    monkeypatch.setattr(monitor, "consultar_ping", consultar)

    codigo = monitor.main([URL_BASE, str(tmp_path / "estrategia.csv")])

    assert codigo == monitor.CODIGO_ERROR
    assert monitor.MENSAJE_SIN_REGISTROS in capsys.readouterr().out
