"""Genera 'Proyecto 1 entrega <N> – Documento.pdf' a partir del documento de la entrega en docs/.

Uso, desde la raíz del repositorio:
    python scripts/generar_pdf.py --entrega 2                # deja el PDF en docs/pdf/
    python scripts/generar_pdf.py --entrega 1 --completo     # entrega 1 con todas las capturas
    python scripts/generar_pdf.py --entrega 2 --si-cambia    # no genera si el PDF ya está al día
    python scripts/generar_pdf.py --en-curso                 # imprime el número de la entrega en curso

Documento de cada entrega: docs/documento-entrega-<N>.md (la entrega 1 usa docs/documento-entrega.md).
Si el documento no existe o no tiene contenido, no genera nada y termina sin error.

Necesita la CLI de GitHub (`gh`) con sesión iniciada (o GH_TOKEN definido) y Google Chrome, Chromium
o Microsoft Edge. Con pymupdf instalado, además guarda en el PDF la huella de las fuentes (documento,
imágenes y este script), que usa --si-cambia, y verifica el resultado (páginas, imágenes y etiquetas).

Códigos de salida: 0 generado o nada que generar; 1 error; 2 generado con puntos por revisar.
"""
import argparse
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
SALIDA = DOCS / "pdf"
ENTREGAS = (1, 2, 3, 4)
# fecha oficial de cada entrega; vence a las 23:59 hora de Colombia (UTC-5, sin horario de verano)
FECHAS_ENTREGA = {1: date(2026, 10, 18), 2: date(2026, 11, 1), 3: date(2026, 11, 15), 4: date(2026, 11, 29)}
HORA_COLOMBIA = timezone(timedelta(hours=-5))
PLANTILLA_NOMBRE = "Proyecto 1 entrega {n} \u2013 Documento"
PREFIJO_HUELLA = "huella-fuentes:"
CLAVES_METADATOS = {"title", "author", "subject", "keywords", "creator", "producer", "creationDate", "modDate"}
NAVEGADORES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge",
]

# Capturas de la entrega 1 que se omiten en la versión compacta: ninguna es la única evidencia de su punto.
CAPTURAS_REPETIDAS = {
    "3a-rds-capa-gratuita.png", "3a-rds-credenciales.png", "3a-rds-grupo-seguridad.png",
    "3a-rds-supervision.png", "3a-rds-opciones.png", "3a-rds-mantenimiento.png",
    "5g-eb-subredes-elb.png",
    "2.4a-versiones-antes.png", "2.4a-implementar.png", "2.4a-ping.png",
    "2.4b-rolling-version-lista.png", "2.4b-rolling-despliegue-completado.png",
    "2.4b-rolling-ping-final-recorte.png",
    "2.4c-rollingbatch-version-lista.png", "2.4c-rollingbatch-despliegue-completado.png",
    "2.4d-immutable-version-lista.png", "2.4d-immutable-despliegue-completado.png",
}

CSS = """
@page { size: A4; margin: %MARGEN%; }
html { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: %FUENTE%; line-height: 1.4; color: #1a1a1a; }
body { margin: 0; }
h1 { font-size: 22pt; margin: 0 0 10pt; line-height: 1.15; }
h2 { font-size: 15pt; margin: 20pt 0 6pt; padding-bottom: 3pt; border-bottom: 1.5pt solid #333; break-after: avoid; }
h3 { font-size: 12pt; margin: 14pt 0 4pt; break-after: avoid; }
p, li, td { text-align: justify; text-justify: inter-word; hyphens: auto; -webkit-hyphens: auto; }
th, h1, h2, h3 { text-align: left; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt; break-inside: avoid; }
tr { break-inside: avoid; }
th, td { border: 0.6pt solid #888; padding: 3pt 5pt; vertical-align: top; overflow-wrap: break-word; }
th { background: #e9edee; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.9em; background: #f0f2f3; padding: 0 2pt; overflow-wrap: break-word; }
pre { background: #f0f2f3; padding: 6pt 8pt; font-size: 8.5pt; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; text-align: left; }
pre code { background: none; padding: 0; }
figure { margin: 8pt 0 12pt; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: %ALTO%; border: 0.6pt solid #bbb; }
figcaption { font-size: 8.5pt; color: #444; margin-top: 3pt; text-align: center; }
a { color: #0b5d63; overflow-wrap: anywhere; }
td:first-child, th:first-child { white-space: nowrap; }
td:first-child code { white-space: nowrap; }
table.texto td, table.texto td:first-child, table.texto td:first-child code { white-space: normal; text-align: left; }
"""


def fallar(mensaje):
    print("ERROR:", mensaje)
    sys.exit(1)


def entrega_en_curso(ahora=None):
    """Primera entrega cuya fecha oficial aún no ha pasado; None si ya pasaron todas."""
    hoy = (ahora or datetime.now(timezone.utc)).astimezone(HORA_COLOMBIA).date()
    return next((n for n in ENTREGAS if hoy <= FECHAS_ENTREGA[n]), None)


def documento_de(entrega):
    if entrega == 1 and not (DOCS / "documento-entrega-1.md").exists():
        return DOCS / "documento-entrega.md"
    return DOCS / ("documento-entrega-%d.md" % entrega)


def tiene_contenido(markdown):
    """Hay contenido si queda alguna línea que no sea un título, un comentario o un separador."""
    sin_comentarios = re.sub(r"<!--.*?-->", "", markdown, flags=re.S)
    return any(linea.strip() and not re.match(r"\s*(#|---|\*\*\*)", linea)
               for linea in sin_comentarios.splitlines())


def imagenes_de(markdown):
    rutas = re.findall(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)", markdown)
    rutas += re.findall(r'<img[^>]+src="([^"]+)"', markdown)
    return sorted(set(r for r in rutas if not re.match(r"[a-z]+:", r)))


def calcular_huella(ruta_documento, markdown, modo):
    h = hashlib.sha256()
    h.update(modo.encode())
    h.update(Path(__file__).read_text(encoding="utf-8").encode("utf-8"))
    h.update(markdown.encode("utf-8"))
    for ruta in imagenes_de(markdown):
        archivo = ruta_documento.parent / ruta
        h.update(ruta.encode("utf-8"))
        h.update(archivo.read_bytes() if archivo.is_file() else b"no-existe")
    return h.hexdigest()


def cargar_pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        return None


def leer_huella(ruta_pdf):
    pymupdf = cargar_pymupdf()
    if not pymupdf or not ruta_pdf.exists():
        return None
    with pymupdf.open(str(ruta_pdf)) as doc:
        claves = (doc.metadata or {}).get("keywords") or ""
    return claves[len(PREFIJO_HUELLA):] if claves.startswith(PREFIJO_HUELLA) else None


def guardar_huella(ruta_pdf, huella):
    pymupdf = cargar_pymupdf()
    if not pymupdf:
        print("(pymupdf no está instalado: el PDF queda sin huella de las fuentes)")
        return
    with pymupdf.open(str(ruta_pdf)) as doc:
        metadatos = {k: v for k, v in (doc.metadata or {}).items() if k in CLAVES_METADATOS and v}
        metadatos["keywords"] = PREFIJO_HUELLA + huella
        doc.set_metadata(metadatos)
        doc.saveIncr()


def renderizar_markdown(ruta):
    gh = shutil.which("gh")
    if not gh:
        fallar("No se encuentra la CLI de GitHub (gh). Instálala e inicia sesión con 'gh auth login'.")
    r = subprocess.run([gh, "api", "markdown", "-F", "text=@" + str(ruta), "-f", "mode=gfm"],
                       capture_output=True, timeout=120)
    if r.returncode != 0 or not r.stdout:
        fallar("gh no pudo renderizar el Markdown: " + r.stderr.decode("utf-8", "replace")[:300])
    return r.stdout.decode("utf-8")


def construir_cuerpo(cuerpo, omitir):
    nuevo_numero = {}
    contador = [0]

    def figura(m):
        src = m.group(1)
        alt = html.unescape(m.group(2))
        if os.path.basename(src) in omitir:
            return ""
        contador[0] += 1
        # "Figura 6.1." (numeración por capítulo) se conserva; solo se renumera "Figura N."
        viejo = re.match(r"Figura (\d+)\.(?!\d)", alt)
        if viejo:
            nuevo_numero[int(viejo.group(1))] = contador[0]
            alt = re.sub(r"^Figura \d+\.", "Figura %d." % contador[0], alt)
        return ('<figure><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>'
                % (src, html.escape(alt, quote=True), html.escape(alt)))

    cuerpo = re.sub(r'<p>\s*<img src="([^"]+)" alt="([^"]*)"[^>]*>\s*</p>', figura, cuerpo)
    cuerpo = re.sub(r'<img src="([^"]+)" alt="([^"]*)"[^>]*>', figura, cuerpo)
    cuerpo = re.sub(r'<a id="user-content-[^"]*" class="anchor"[^>]*>.*?</a>', "", cuerpo, flags=re.S)

    def referencia(m):
        a = nuevo_numero.get(int(m.group(2)))
        b = nuevo_numero.get(int(m.group(3))) if m.group(3) else None
        if a is None or (m.group(3) and b is None):
            fallar("Una referencia del texto apunta a una figura omitida: " + m.group(0))
        return "%s %d y %d" % (m.group(1), a, b) if m.group(3) else "%s %d" % (m.group(1), a)

    cuerpo = re.sub(r"\b(figuras?) (\d+)(?!\d|\.\d)(?: y (\d+)(?!\d|\.\d))?", referencia, cuerpo)
    # tablas largas pueden partirse entre páginas; las etiquetas que terminan en ':' no quedan solas
    cuerpo = re.sub(r"<table.*?</table>",
                    lambda m: m.group(0).replace("<table", '<table style="break-inside:auto"', 1)
                    if m.group(0).count("<tr") > 9 else m.group(0), cuerpo, flags=re.S)

    # tablas con frases en la primera columna: sin nowrap y alineadas a la izquierda
    def tabla_texto(m):
        primeras = re.findall(r"<tr>\s*<td[^>]*>(.*?)</td>", m.group(0), flags=re.S)
        if any(len(re.sub(r"<[^>]+>", "", c)) > 45 and not c.lstrip().startswith("<code")
               for c in primeras):
            return m.group(0).replace("<table", '<table class="texto"', 1)
        return m.group(0)

    cuerpo = re.sub(r"<table.*?</table>", tabla_texto, cuerpo, flags=re.S)
    cuerpo = re.sub(r"<p>(<strong>[^<]*:</strong>)</p>",
                    lambda m: '<p style="break-after:avoid">' + m.group(1) + "</p>", cuerpo)
    # texto justificado: los saltos de línea del Markdown no fuerzan corte; número y unidad van juntos
    cuerpo = re.sub(r"<br>\s*", " ", cuerpo)
    cuerpo = re.sub(r"(\d) (min|s|ms|MB|KB|vCPU)\b", lambda m: m.group(1) + "&nbsp;" + m.group(2), cuerpo)
    cuerpo = re.sub(r"(min) (\d+&nbsp;s)", lambda m: m.group(1) + "&nbsp;" + m.group(2), cuerpo)
    return cuerpo, contador[0]


def buscar_navegador():
    for n in NAVEGADORES:
        ruta = n if os.path.isabs(n) else shutil.which(n)
        if ruta and os.path.exists(ruta):
            return ruta
    return None


def imprimir_pdf(ruta_html, ruta_pdf):
    navegador = buscar_navegador()
    if not navegador:
        fallar("No se encontró Chrome, Chromium ni Edge.")
    if ruta_pdf.exists():
        ruta_pdf.unlink()
    opciones = ["--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw", "--virtual-time-budget=20000"]
    if os.environ.get("CI"):
        # los ejecutores de CI no permiten el sandbox del navegador; solo se imprime HTML propio
        opciones.append("--no-sandbox")
    subprocess.run([navegador, *opciones, "--print-to-pdf=" + str(ruta_pdf), ruta_html.as_uri()],
                   capture_output=True, timeout=180)
    if not ruta_pdf.exists():
        fallar("El navegador no generó el PDF.")


# Referencias a tareas o issues del tablero ("la 1.6", "tareas 1.6 a 1.16", "(2.6, #210)", "(#199)"),
# que el tutor no puede consultar. No cuenta versiones (3.13.16), secciones ni figuras, que llevan su
# palabra delante, ni los PR ("PR #253", "promoción #254").
TAREAS_DEL_TABLERO = (
    re.compile(r"\b(?:las?|tareas?)\s+[1-4]\.\d{1,2}(?![.\d])", flags=re.I),
    re.compile(r"\([1-4]\.\d{1,2}(?![.\d])"),
    re.compile(r"\(#\d+\)"),
)


def referencias_a_tareas(markdown):
    """Referencias a tareas del tablero fuera de bloques e incisos de código (valores literales)."""
    texto = re.sub(r"```.*?```", "", markdown, flags=re.S)
    texto = re.sub(r"`[^`\n]*`", "", texto)
    return sorted({" ".join(m.group(0).split())
                   for patron in TAREAS_DEL_TABLERO for m in patron.finditer(texto)})


def verificar(markdown, ruta_pdf):
    problemas = []
    etiquetas = re.findall(r"^\*\*([^*\n]*:)\*\*$", markdown, flags=re.M)
    md_refs = re.findall(r"[\w./-]*\w\.md\b", markdown)
    print("Marcadores [PENDIENTE] en el documento:", markdown.count("PENDIENTE"))
    if md_refs:
        problemas.append("el documento cita archivos .md: %s" % sorted(set(md_refs)))
    tareas = referencias_a_tareas(markdown)
    if tareas:
        problemas.append("el documento cita tareas del tablero, que el tutor no ve: %s" % tareas)
    pymupdf = cargar_pymupdf()
    if not pymupdf:
        print("(pymupdf no está instalado: se omite la verificación del PDF)")
        return problemas
    with pymupdf.open(str(ruta_pdf)) as doc:
        texto = "\n".join(p.get_text() for p in doc)
        imagenes = sum(len(p.get_images()) for p in doc)
        paginas = doc.page_count
    numeros = sorted(set(int(x) for x in re.findall(r"Figura (\d+)\.(?!\d)", texto)))
    por_capitulo = set(re.findall(r"Figura (\d+\.\d+)\.", texto))
    total = len(numeros) + len(por_capitulo)
    faltan = [e for e in etiquetas if e not in texto]
    print("PDF: %d páginas, %d imágenes, %d figuras con pie, %.1f MB" % (
        paginas, imagenes, total, ruta_pdf.stat().st_size / 1048576))
    if numeros != list(range(1, len(numeros) + 1)):
        problemas.append("las figuras no están numeradas de seguido")
    if total != imagenes:
        problemas.append("hay %d imágenes y %d pies de figura" % (imagenes, total))
    if faltan:
        problemas.append("faltan etiquetas en el PDF: %s" % faltan)
    if re.search(r"[\x00-\x08]", texto):
        problemas.append("el PDF tiene caracteres de control")
    return problemas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--entrega", type=int, choices=ENTREGAS, help="número de la entrega")
    grupo.add_argument("--en-curso", action="store_true",
                       help="solo imprime el número de la entrega en curso (vacío si ya pasaron todas)")
    ap.add_argument("--completo", action="store_true", help="entrega 1: incluye todas las capturas")
    ap.add_argument("--si-cambia", action="store_true",
                    help="no genera si el PDF existente tiene la misma huella de las fuentes")
    ap.add_argument("--salida", type=Path, default=SALIDA, help="carpeta del PDF (docs/pdf por defecto)")
    args = ap.parse_args()
    if args.en_curso:
        print(entrega_en_curso() or "")
        return
    titulo = PLANTILLA_NOMBRE.format(n=args.entrega)
    documento = documento_de(args.entrega)
    ruta_pdf = args.salida / (titulo + ".pdf")

    if not documento.exists():
        print("No existe %s: no hay documento de la entrega %d y no se genera nada."
              % (documento.relative_to(RAIZ).as_posix(), args.entrega))
        return
    markdown = documento.read_text(encoding="utf-8")
    if not tiene_contenido(markdown):
        print("%s no tiene contenido: no se genera nada." % documento.relative_to(RAIZ).as_posix())
        return

    completo = args.completo and args.entrega == 1
    omitir = CAPTURAS_REPETIDAS if args.entrega == 1 and not completo else set()
    huella = calcular_huella(documento, markdown, "completo" if completo else "compacto")
    if args.si_cambia and leer_huella(ruta_pdf) == huella:
        print("El PDF ya está al día con las fuentes (%s): no se genera de nuevo." % ruta_pdf.name)
        return

    print("Rama:", subprocess.run(["git", "-C", str(RAIZ), "branch", "--show-current"],
                                 capture_output=True, text=True).stdout.strip())
    cuerpo, figuras = construir_cuerpo(renderizar_markdown(documento), omitir)
    css = (CSS.replace("%MARGEN%", "18mm 16mm" if completo else "14mm 14mm")
              .replace("%FUENTE%", "10.5pt" if completo else "10pt")
              .replace("%ALTO%", "215mm" if completo else "95mm"))
    base = documento.parent.as_uri() + "/"
    pagina = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><base href="%s">'
              "<title>%s</title><style>%s</style></head><body>%s</body></html>"
              % (base, titulo, css, cuerpo))
    args.salida.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as trabajo:
        ruta_html = Path(trabajo) / ("documento-%d.html" % args.entrega)
        ruta_html.write_text(pagina, encoding="utf-8")
        imprimir_pdf(ruta_html, ruta_pdf)
    guardar_huella(ruta_pdf, huella)
    print("Figuras en el PDF:", figuras, "(completo)" if completo else "(compacto)")
    problemas = verificar(markdown, ruta_pdf)
    print("\nPDF generado:", ruta_pdf)
    if problemas:
        print("\nREVISAR:")
        for p in problemas:
            print(" -", p)
        sys.exit(2)
    print("Verificación: sin problemas.")


if __name__ == "__main__":
    main()
