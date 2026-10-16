import argparse
import csv
import http.client
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

RUTA_PING = "/ping"
CAMPO_VERSION = "version"
CODIGO_HTTP_EXITO = 200
CODIGO_SIN_RESPUESTA = 0
INTERVALO_POR_DEFECTO = 1.0
TIEMPO_ESPERA_POR_DEFECTO = 3.0
COLUMNAS_CSV = ("marca_tiempo_utc", "codigo_http", "version", "latencia_ms", "error")
FORMATO_HORA = "%H:%M:%S"

ARGUMENTO_URL = "url"
ARGUMENTO_CSV = "csv"
OPCION_INTERVALO = "--intervalo"
OPCION_TIEMPO_ESPERA = "--tiempo-espera"
OPCION_SOLICITUDES = "--solicitudes"

CODIGO_EXITO = 0
CODIGO_ERROR = 1

DESCRIPCION_URL = "URL base del entorno, por ejemplo http://blacklist-devops-misw.us-east-2.elasticbeanstalk.com"
DESCRIPCION_CSV = "Archivo CSV de salida; si existe, se agregan filas."
DESCRIPCION_INTERVALO = "Segundos entre solicitudes (por defecto 1)."
DESCRIPCION_TIEMPO_ESPERA = "Segundos máximos de espera por solicitud (por defecto 3)."
DESCRIPCION_SOLICITUDES = "Detiene el monitor después de este número de solicitudes; sin la opción, sigue hasta Ctrl+C."

MENSAJE_INICIO = "Monitoreando {url} cada {intervalo:g} s. Detener con Ctrl+C."
MENSAJE_LINEA = "{hora} {codigo} {version} {latencia:.0f} ms {error}"
MENSAJE_SIN_REGISTROS = "No se registró ninguna solicitud."


@dataclass(frozen=True)
class Registro:
    marca_tiempo: datetime
    codigo_http: int
    version: str
    latencia_ms: float
    error: str = ""

    @property
    def exitoso(self) -> bool:
        return self.codigo_http == CODIGO_HTTP_EXITO

    def como_fila(self) -> List[str]:
        return [
            formatear_marca(self.marca_tiempo),
            str(self.codigo_http),
            self.version,
            f"{self.latencia_ms:.1f}",
            self.error,
        ]


@dataclass(frozen=True)
class VersionObservada:
    cantidad: int
    primera: datetime
    ultima: datetime


@dataclass(frozen=True)
class Caida:
    solicitudes: int
    inicio: datetime
    ultima_falla: datetime
    recuperacion: Optional[datetime]


@dataclass(frozen=True)
class Resumen:
    total: int
    exitosas: int
    inicio: Optional[datetime] = None
    fin: Optional[datetime] = None
    versiones: Dict[str, VersionObservada] = field(default_factory=dict)
    caida: Optional[Caida] = None
    convivencia_inicio: Optional[datetime] = None
    convivencia_fin: Optional[datetime] = None

    @property
    def fallidas(self) -> int:
        return self.total - self.exitosas

    @property
    def disponibilidad(self) -> float:
        return 100.0 * self.exitosas / self.total if self.total else 0.0


def formatear_marca(marca: datetime) -> str:
    return marca.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def extraer_version(cuerpo: bytes) -> str:
    try:
        datos = json.loads(cuerpo)
    except ValueError:
        return ""
    if not isinstance(datos, dict):
        return ""
    return str(datos.get(CAMPO_VERSION, ""))


def consultar_ping(
    url_base: str,
    tiempo_espera: float,
    abrir: Callable = urllib.request.urlopen,
    reloj: Callable[[], float] = time.perf_counter,
    ahora: Callable[[], datetime] = ahora_utc,
) -> Registro:
    url = url_base.rstrip("/") + RUTA_PING
    marca = ahora()
    inicio = reloj()
    version = ""
    error = ""
    try:
        with abrir(url, timeout=tiempo_espera) as respuesta:
            codigo = respuesta.status
            version = extraer_version(respuesta.read())
    except urllib.error.HTTPError as falla:
        codigo = falla.code
        error = f"HTTP {falla.code}"
        falla.close()
    except (OSError, http.client.HTTPException) as falla:
        codigo = CODIGO_SIN_RESPUESTA
        motivo = getattr(falla, "reason", falla)
        error = f"{type(falla).__name__}: {motivo}"
    latencia = (reloj() - inicio) * 1000
    return Registro(marca, codigo, version, latencia, error)


def abrir_csv(ruta: Path):
    nuevo = not ruta.exists() or ruta.stat().st_size == 0
    ruta.parent.mkdir(parents=True, exist_ok=True)
    archivo = ruta.open("a", newline="", encoding="utf-8")
    escritor = csv.writer(archivo)
    if nuevo:
        escritor.writerow(COLUMNAS_CSV)
    return archivo, escritor


def monitorear(
    url_base: str,
    ruta_csv: Path,
    registros: List[Registro],
    intervalo: float = INTERVALO_POR_DEFECTO,
    tiempo_espera: float = TIEMPO_ESPERA_POR_DEFECTO,
    limite: Optional[int] = None,
    consultar: Callable[[str, float], Registro] = consultar_ping,
    dormir: Callable[[float], None] = time.sleep,
    reloj: Callable[[], float] = time.monotonic,
    mostrar: Callable[[str], None] = print,
) -> List[Registro]:
    archivo, escritor = abrir_csv(ruta_csv)
    try:
        while limite is None or len(registros) < limite:
            inicio = reloj()
            registro = consultar(url_base, tiempo_espera)
            registros.append(registro)
            escritor.writerow(registro.como_fila())
            archivo.flush()
            mostrar(
                MENSAJE_LINEA.format(
                    hora=registro.marca_tiempo.strftime(FORMATO_HORA),
                    codigo=registro.codigo_http,
                    version=registro.version or "-",
                    latencia=registro.latencia_ms,
                    error=registro.error,
                ).rstrip()
            )
            if limite is None or len(registros) < limite:
                dormir(max(0.0, intervalo - (reloj() - inicio)))
    finally:
        archivo.close()
    return registros


def calcular_mayor_caida(registros: List[Registro]) -> Optional[Caida]:
    caidas: List[Caida] = []
    cantidad, inicio, ultima = 0, None, None
    for registro in registros:
        if registro.exitoso:
            if cantidad:
                caidas.append(Caida(cantidad, inicio, ultima, registro.marca_tiempo))
                cantidad, inicio, ultima = 0, None, None
            continue
        cantidad += 1
        inicio = inicio or registro.marca_tiempo
        ultima = registro.marca_tiempo
    if cantidad:
        caidas.append(Caida(cantidad, inicio, ultima, None))
    return max(caidas, key=lambda caida: caida.solicitudes, default=None)


def agrupar_versiones(registros: List[Registro]) -> Dict[str, VersionObservada]:
    versiones: Dict[str, VersionObservada] = {}
    for registro in registros:
        if not registro.exitoso or not registro.version:
            continue
        previa = versiones.get(registro.version)
        if previa is None:
            versiones[registro.version] = VersionObservada(1, registro.marca_tiempo, registro.marca_tiempo)
        else:
            versiones[registro.version] = VersionObservada(previa.cantidad + 1, previa.primera, registro.marca_tiempo)
    return versiones


def calcular_convivencia(versiones: Dict[str, VersionObservada]):
    if len(versiones) < 2:
        return None, None
    ordenadas = sorted(versiones.values(), key=lambda observada: observada.primera)
    inicio = ordenadas[-1].primera
    fin = max(observada.ultima for observada in ordenadas[:-1])
    if fin <= inicio:
        return None, None
    return inicio, fin


def resumir(registros: List[Registro]) -> Resumen:
    if not registros:
        return Resumen(total=0, exitosas=0)
    versiones = agrupar_versiones(registros)
    convivencia_inicio, convivencia_fin = calcular_convivencia(versiones)
    return Resumen(
        total=len(registros),
        exitosas=sum(1 for registro in registros if registro.exitoso),
        inicio=registros[0].marca_tiempo,
        fin=registros[-1].marca_tiempo,
        versiones=versiones,
        caida=calcular_mayor_caida(registros),
        convivencia_inicio=convivencia_inicio,
        convivencia_fin=convivencia_fin,
    )


def segundos_entre(inicio: datetime, fin: datetime) -> float:
    return (fin - inicio).total_seconds()


def formatear_resumen(resumen: Resumen) -> str:
    if not resumen.total:
        return MENSAJE_SIN_REGISTROS
    lineas = [
        "Resumen del monitoreo",
        f"Periodo: {formatear_marca(resumen.inicio)} a {formatear_marca(resumen.fin)} "
        f"({segundos_entre(resumen.inicio, resumen.fin):.0f} s)",
        f"Solicitudes: {resumen.total}; respuestas 200: {resumen.exitosas}; no-200: {resumen.fallidas}; "
        f"disponibilidad: {resumen.disponibilidad:.2f} %",
    ]
    caida = resumen.caida
    if caida is None:
        lineas.append("Sin respuestas no-200.")
    elif caida.recuperacion is None:
        lineas.append(
            f"Mayor caída: {caida.solicitudes} solicitudes no-200 seguidas desde {formatear_marca(caida.inicio)}; "
            f"al detener el monitor no había vuelto a responder 200 (última falla: {formatear_marca(caida.ultima_falla)})"
        )
    else:
        lineas.append(
            f"Mayor caída: {caida.solicitudes} solicitudes no-200 seguidas, desde {formatear_marca(caida.inicio)} "
            f"hasta la siguiente respuesta 200 a las {formatear_marca(caida.recuperacion)} "
            f"({segundos_entre(caida.inicio, caida.recuperacion):.0f} s)"
        )
    lineas.append("Versiones observadas:")
    for version, observada in sorted(resumen.versiones.items(), key=lambda item: item[1].primera):
        lineas.append(
            f"  {version}: {observada.cantidad} respuestas, de {formatear_marca(observada.primera)} "
            f"a {formatear_marca(observada.ultima)}"
        )
    if resumen.convivencia_inicio:
        lineas.append(
            f"Convivencia de versiones: de {formatear_marca(resumen.convivencia_inicio)} a "
            f"{formatear_marca(resumen.convivencia_fin)} "
            f"({segundos_entre(resumen.convivencia_inicio, resumen.convivencia_fin):.0f} s)"
        )
    else:
        lineas.append("Sin convivencia de versiones.")
    return "\n".join(lineas)


def leer_argumentos(argumentos: Optional[List[str]]) -> argparse.Namespace:
    analizador = argparse.ArgumentParser()
    analizador.add_argument(ARGUMENTO_URL, help=DESCRIPCION_URL)
    analizador.add_argument(ARGUMENTO_CSV, type=Path, help=DESCRIPCION_CSV)
    analizador.add_argument(OPCION_INTERVALO, type=float, default=INTERVALO_POR_DEFECTO, help=DESCRIPCION_INTERVALO)
    analizador.add_argument(
        OPCION_TIEMPO_ESPERA, type=float, default=TIEMPO_ESPERA_POR_DEFECTO, help=DESCRIPCION_TIEMPO_ESPERA
    )
    analizador.add_argument(OPCION_SOLICITUDES, type=int, default=None, help=DESCRIPCION_SOLICITUDES)
    return analizador.parse_args(argumentos)


def main(argumentos: Optional[List[str]] = None) -> int:
    leidos = leer_argumentos(argumentos)
    registros: List[Registro] = []
    print(MENSAJE_INICIO.format(url=leidos.url, intervalo=leidos.intervalo))
    try:
        monitorear(
            leidos.url,
            leidos.csv,
            registros,
            intervalo=leidos.intervalo,
            tiempo_espera=leidos.tiempo_espera,
            limite=leidos.solicitudes,
            consultar=consultar_ping,
            dormir=time.sleep,
        )
    except KeyboardInterrupt:
        pass
    print(formatear_resumen(resumir(registros)))
    return CODIGO_EXITO if registros else CODIGO_ERROR


if __name__ == "__main__":
    sys.exit(main())
