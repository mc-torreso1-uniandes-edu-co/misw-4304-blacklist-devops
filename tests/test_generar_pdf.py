import sys

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
