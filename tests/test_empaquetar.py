import zipfile

import pytest

from scripts import empaquetar

ETIQUETA = "v2-rolling"
CONTENIDO_VERSION_LOCAL = "local\n"

ARCHIVOS_ESPERADOS = {
    "application.py",
    "app/__init__.py",
    "app/config.py",
    "requirements.txt",
    "Procfile",
    ".ebextensions/01-health-check.config",
    "VERSION",
}
ARCHIVOS_NO_INCLUIBLES = [
    ".env",
    ".venv/lib/modulo.py",
    "tests/test_algo.py",
    "docs/enunciado.md",
    "postman/coleccion.json",
    "dist/app-anterior.zip",
    "app/__pycache__/config.cpython-313.pyc",
    "app/modulo.pyc",
    "app/local.db",
    "app/notas.txt",
    ".ebextensions/secreto.env",
    ".pytest_cache/estado",
    ".ajustes-locales/preferencias.json",
]
ETIQUETAS_INVALIDAS = ["", "con espacio", "../fuera", "con/barra", "x" * 51]


def crear_archivo(raiz, ruta, contenido="contenido"):
    destino = raiz / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")


@pytest.fixture
def repositorio(tmp_path):
    for ruta in ARCHIVOS_ESPERADOS - {"VERSION"}:
        crear_archivo(tmp_path, ruta)
    crear_archivo(tmp_path, "VERSION", CONTENIDO_VERSION_LOCAL)
    for ruta in ARCHIVOS_NO_INCLUIBLES:
        crear_archivo(tmp_path, ruta)
    return tmp_path


def nombres_del_paquete(paquete):
    with zipfile.ZipFile(paquete) as zip_paquete:
        return set(zip_paquete.namelist())


def test_package_contains_only_expected_files(repositorio):
    paquete = empaquetar.construir_paquete(repositorio, ETIQUETA)

    assert nombres_del_paquete(paquete) == ARCHIVOS_ESPERADOS


def test_package_is_named_after_label_inside_dist(repositorio):
    paquete = empaquetar.construir_paquete(repositorio, ETIQUETA)

    assert paquete == repositorio / empaquetar.CARPETA_DISTRIBUCION / f"app-{ETIQUETA}.zip"


def test_package_version_file_has_the_label(repositorio):
    paquete = empaquetar.construir_paquete(repositorio, ETIQUETA)

    with zipfile.ZipFile(paquete) as zip_paquete:
        assert zip_paquete.read("VERSION").decode("utf-8").strip() == ETIQUETA


def test_package_does_not_change_repository_version_file(repositorio):
    empaquetar.construir_paquete(repositorio, ETIQUETA)

    assert (repositorio / "VERSION").read_text(encoding="utf-8") == CONTENIDO_VERSION_LOCAL


def test_package_keeps_entry_file_at_the_root(repositorio):
    paquete = empaquetar.construir_paquete(repositorio, ETIQUETA)

    assert empaquetar.ARCHIVO_ENTRADA in nombres_del_paquete(paquete)


@pytest.mark.parametrize("etiqueta", ETIQUETAS_INVALIDAS)
def test_invalid_label_is_rejected(repositorio, etiqueta):
    with pytest.raises(ValueError):
        empaquetar.construir_paquete(repositorio, etiqueta)

    assert not (repositorio / empaquetar.CARPETA_DISTRIBUCION / f"app-{etiqueta}.zip").exists()


def test_missing_entry_is_reported(repositorio):
    (repositorio / "Procfile").unlink()

    with pytest.raises(FileNotFoundError):
        empaquetar.construir_paquete(repositorio, ETIQUETA)


def test_main_builds_package_when_tests_are_skipped(repositorio):
    codigo = empaquetar.main([ETIQUETA, empaquetar.OPCION_OMITIR_PRUEBAS], raiz=repositorio)

    assert codigo == empaquetar.CODIGO_EXITO
    assert (repositorio / empaquetar.CARPETA_DISTRIBUCION / f"app-{ETIQUETA}.zip").is_file()


def test_main_does_not_build_package_when_tests_fail(repositorio, monkeypatch):
    monkeypatch.setattr(empaquetar, "ejecutar_pruebas", lambda raiz: False)

    codigo = empaquetar.main([ETIQUETA], raiz=repositorio)

    assert codigo == empaquetar.CODIGO_ERROR
    assert not (repositorio / empaquetar.CARPETA_DISTRIBUCION / f"app-{ETIQUETA}.zip").exists()


def test_main_runs_tests_before_building_package(repositorio, monkeypatch):
    ejecuciones = []
    monkeypatch.setattr(empaquetar, "ejecutar_pruebas", lambda raiz: ejecuciones.append(raiz) or True)

    codigo = empaquetar.main([ETIQUETA], raiz=repositorio)

    assert codigo == empaquetar.CODIGO_EXITO
    assert ejecuciones == [repositorio]


def test_main_rejects_invalid_label(repositorio):
    codigo = empaquetar.main(["etiqueta invalida", empaquetar.OPCION_OMITIR_PRUEBAS], raiz=repositorio)

    assert codigo == empaquetar.CODIGO_ERROR
