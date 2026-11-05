import sys
from datetime import datetime, timezone

import pytest

from scripts import generar_pdf

DOCUMENTO_CON_CAPTURA = "# Documento\n\nTexto.\n\n![Figura 1. Captura](capturas/a.png)\n"


@pytest.fixture
def docs(tmp_path, monkeypatch):
    carpeta = tmp_path / "docs"
    (carpeta / "capturas").mkdir(parents=True)
    monkeypatch.setattr(generar_pdf, "RAIZ", tmp_path)
    monkeypatch.setattr(generar_pdf, "DOCS", carpeta)
    monkeypatch.setattr(generar_pdf, "SALIDA", carpeta / "pdf")
    return carpeta


def ejecutar(monkeypatch, *argumentos):
    monkeypatch.setattr(sys, "argv", ["generar_pdf.py", *argumentos])
    generar_pdf.main()


@pytest.mark.parametrize("instante_utc, entrega", [
    ("2026-10-05T12:00", 1),
    ("2026-10-19T04:59", 1),   # domingo 18 de octubre, 23:59 en Colombia
    ("2026-10-19T05:00", 2),   # lunes 19 de octubre, 00:00 en Colombia
    ("2026-10-29T16:00", 2),
    ("2026-11-02T04:59", 2),
    ("2026-11-02T05:00", 3),
    ("2026-11-16T05:00", 4),
    ("2026-11-30T04:59", 4),
])
def test_entrega_en_curso_segun_la_fecha_oficial(instante_utc, entrega):
    ahora = datetime.fromisoformat(instante_utc).replace(tzinfo=timezone.utc)
    assert generar_pdf.entrega_en_curso(ahora) == entrega


def test_sin_entrega_en_curso_despues_de_la_ultima():
    assert generar_pdf.entrega_en_curso(datetime(2026, 11, 30, 5, 0, tzinfo=timezone.utc)) is None


def test_en_curso_imprime_el_numero(monkeypatch, capsys):
    monkeypatch.setattr(generar_pdf, "entrega_en_curso", lambda: 3)
    ejecutar(monkeypatch, "--en-curso")
    assert capsys.readouterr().out.strip() == "3"


def test_documento_de_la_entrega_1_sin_numero(docs):
    assert generar_pdf.documento_de(1) == docs / "documento-entrega.md"


def test_documento_de_la_entrega_1_con_numero_si_existe(docs):
    (docs / "documento-entrega-1.md").write_text("# E1\ntexto\n", encoding="utf-8")
    assert generar_pdf.documento_de(1) == docs / "documento-entrega-1.md"


@pytest.mark.parametrize("entrega", [2, 3, 4])
def test_documento_de_las_demas_entregas(docs, entrega):
    assert generar_pdf.documento_de(entrega) == docs / ("documento-entrega-%d.md" % entrega)


@pytest.mark.parametrize("markdown", ["", "\n  \n", "# Título\n\n## Sección\n", "<!--\npendiente\n-->\n---\n"])
def test_sin_contenido(markdown):
    assert not generar_pdf.tiene_contenido(markdown)


def test_con_contenido():
    assert generar_pdf.tiene_contenido("# Título\n\nUn párrafo.\n")


def test_imagenes_del_documento_sin_enlaces_externos():
    markdown = ('![a](capturas/a.png)\n<img src="capturas/d.png" alt="d">\n'
                "![e](https://ejemplo.com/e.png)\n![a otra vez](capturas/a.png)\n")
    assert generar_pdf.imagenes_de(markdown) == ["capturas/a.png", "capturas/d.png"]


def test_huella_cambia_con_las_capturas_y_el_modo(docs):
    documento = docs / "documento-entrega-2.md"
    captura = docs / "capturas" / "a.png"
    captura.write_bytes(b"imagen-1")
    inicial = generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "compacto")

    assert generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "compacto") == inicial
    assert generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "completo") != inicial
    captura.write_bytes(b"imagen-2")
    assert generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "compacto") != inicial
    captura.unlink()
    assert generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "compacto") != inicial


def test_sin_documento_no_genera_nada(docs, monkeypatch, capsys):
    ejecutar(monkeypatch, "--entrega", "3")

    assert "no se genera nada" in capsys.readouterr().out
    assert not (docs / "pdf").exists()


def test_documento_vacio_no_genera_nada(docs, monkeypatch, capsys):
    (docs / "documento-entrega-4.md").write_text("# Documento\n\n## Pendiente\n", encoding="utf-8")

    ejecutar(monkeypatch, "--entrega", "4")

    assert "no tiene contenido" in capsys.readouterr().out
    assert not (docs / "pdf").exists()


def test_si_cambia_no_genera_cuando_la_huella_coincide(docs, monkeypatch, capsys):
    documento = docs / "documento-entrega-2.md"
    documento.write_text(DOCUMENTO_CON_CAPTURA, encoding="utf-8")
    (docs / "capturas" / "a.png").write_bytes(b"imagen")
    huella = generar_pdf.calcular_huella(documento, DOCUMENTO_CON_CAPTURA, "compacto")
    monkeypatch.setattr(generar_pdf, "leer_huella", lambda ruta: huella)
    monkeypatch.setattr(generar_pdf, "renderizar_markdown", lambda ruta: pytest.fail("no debe renderizar"))

    ejecutar(monkeypatch, "--entrega", "2", "--si-cambia")

    assert "ya está al día" in capsys.readouterr().out
