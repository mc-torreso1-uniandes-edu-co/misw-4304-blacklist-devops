import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List, Optional

RAIZ_REPOSITORIO = Path(__file__).resolve().parent.parent

PATRON_ETIQUETA = re.compile(r"[A-Za-z0-9._-]{1,50}")
CARPETA_DISTRIBUCION = "dist"
PLANTILLA_NOMBRE_PAQUETE = "app-{etiqueta}.zip"
ARCHIVO_VERSION = "VERSION"
ARCHIVO_ENTRADA = "application.py"
ENTRADAS_INCLUIDAS = ("application.py", "app", "requirements.txt", "Procfile", ".ebextensions")
EXTENSIONES_PERMITIDAS_EN_CARPETAS = frozenset({".py", ".config"})

ARGUMENTO_ETIQUETA = "etiqueta"
OPCION_OMITIR_PRUEBAS = "--omitir-pruebas"
COMANDO_PRUEBAS = [sys.executable, "-m", "pytest", "-q"]

CODIGO_EXITO = 0
CODIGO_ERROR = 1

MENSAJE_ETIQUETA_INVALIDA = "La etiqueta debe tener entre 1 y 50 caracteres: letras, números, punto, guion y guion bajo."
MENSAJE_ENTRADA_FALTANTE = "Falta en el repositorio: {entrada}"
MENSAJE_SIN_ARCHIVO_ENTRADA = "El paquete debe tener application.py en la raíz."
MENSAJE_PRUEBAS_FALLIDAS = "Las pruebas fallaron; no se genera el paquete."
MENSAJE_PAQUETE_GENERADO = "Generado {ruta} con {cantidad} archivos."
DESCRIPCION_ETIQUETA = "Etiqueta de la versión, por ejemplo v1 o v2-rolling."
DESCRIPCION_OMITIR_PRUEBAS = "Genera el paquete sin ejecutar las pruebas."


def validar_etiqueta(etiqueta: str) -> str:
    if not PATRON_ETIQUETA.fullmatch(etiqueta):
        raise ValueError(MENSAJE_ETIQUETA_INVALIDA)
    return etiqueta


def es_archivo_de_carpeta_incluible(archivo: Path) -> bool:
    return archivo.is_file() and archivo.suffix in EXTENSIONES_PERMITIDAS_EN_CARPETAS


def reunir_archivos(raiz: Path) -> List[Path]:
    archivos = []
    for entrada in ENTRADAS_INCLUIDAS:
        ruta = raiz / entrada
        if not ruta.exists():
            raise FileNotFoundError(MENSAJE_ENTRADA_FALTANTE.format(entrada=entrada))
        if ruta.is_file():
            archivos.append(ruta)
        else:
            archivos.extend(archivo for archivo in ruta.rglob("*") if es_archivo_de_carpeta_incluible(archivo))
    return sorted(archivos)


def construir_paquete(raiz: Path, etiqueta: str) -> Path:
    validar_etiqueta(etiqueta)
    archivos = reunir_archivos(raiz)
    destino = raiz / CARPETA_DISTRIBUCION
    destino.mkdir(exist_ok=True)
    paquete = destino / PLANTILLA_NOMBRE_PAQUETE.format(etiqueta=etiqueta)
    with zipfile.ZipFile(paquete, "w", zipfile.ZIP_DEFLATED) as zip_paquete:
        for archivo in archivos:
            zip_paquete.write(archivo, archivo.relative_to(raiz).as_posix())
        zip_paquete.writestr(ARCHIVO_VERSION, f"{etiqueta}\n")
        if ARCHIVO_ENTRADA not in zip_paquete.namelist():
            raise FileNotFoundError(MENSAJE_SIN_ARCHIVO_ENTRADA)
    return paquete


def ejecutar_pruebas(raiz: Path) -> bool:
    return subprocess.call(COMANDO_PRUEBAS, cwd=raiz) == 0


def leer_argumentos(argumentos: Optional[List[str]]) -> argparse.Namespace:
    analizador = argparse.ArgumentParser()
    analizador.add_argument(ARGUMENTO_ETIQUETA, help=DESCRIPCION_ETIQUETA)
    analizador.add_argument(OPCION_OMITIR_PRUEBAS, action="store_true", help=DESCRIPCION_OMITIR_PRUEBAS)
    return analizador.parse_args(argumentos)


def main(argumentos: Optional[List[str]] = None, raiz: Path = RAIZ_REPOSITORIO) -> int:
    leidos = leer_argumentos(argumentos)
    try:
        validar_etiqueta(leidos.etiqueta)
        if not leidos.omitir_pruebas and not ejecutar_pruebas(raiz):
            print(MENSAJE_PRUEBAS_FALLIDAS)
            return CODIGO_ERROR
        paquete = construir_paquete(raiz, leidos.etiqueta)
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return CODIGO_ERROR
    with zipfile.ZipFile(paquete) as zip_paquete:
        cantidad = len(zip_paquete.namelist())
    print(MENSAJE_PAQUETE_GENERADO.format(ruta=paquete.relative_to(raiz), cantidad=cantidad))
    return CODIGO_EXITO


if __name__ == "__main__":
    sys.exit(main())
