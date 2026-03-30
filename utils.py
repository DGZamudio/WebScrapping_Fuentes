import hashlib
import re
from datetime import datetime
from io import BytesIO

try:
    from fpdf import FPDF  # type: ignore
except ImportError:  # pragma: no cover
    FPDF = None  # type: ignore


def make_doc_id(title):
    return hashlib.sha1(title.encode()).hexdigest()

def extract_filename(disposition, content_type, url, opt_title):
    if disposition:
        match = re.search(r'filename="?([^"]+)"?', disposition)
        if match:
            filename = match.group(1)
            # Extract extension from filename
            ext = "." + filename.split(".")[-1] if "." in filename else ""
            return {"filename": filename.split(".")[0], "extension": ext}

    if "rtf" in content_type.lower():
        ext = ".rtf"
    elif "pdf" in content_type.lower():
        ext = ".pdf"
    elif "word" in content_type.lower() or "officedocument" in content_type.lower():
        ext = ".docx"
    else:
        ext = ""

    return {"filename": url.split("/")[-1] or opt_title, "extension": ext}


def _escape_pdf_string(value: str) -> str:
    """Escape text so it can be safely embedded in a PDF string."""
    # PDF strings need backslashes and parentheses escaped.
    return (
        value.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\n", "\\n")
    )


def generate_pdf_report(path: str, rows: list[dict], title: str = "Inventario") -> None:
    """Generate a PDF report from a list of row dictionaries.

    If `fpdf` is available, we use it for proper layout (tables, line wrapping).
    Otherwise we fall back to a minimal embedded-PDF generator.
    """

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prefer fpdf for better formatting
    if FPDF is not None:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, title, ln=1)

        pdf.set_font("Helvetica", size=10)
        pdf.cell(0, 8, f"Generado: {created_at}", ln=1)
        pdf.ln(4)

        with pdf.table() as table:
            # Table Header
            pdf.set_font("Helvetica", "B", 10)
            row = table.row()
            row.cell("Descargado")
            row.cell("Fuente")
            row.cell("Título")

            pdf.set_font("Helvetica", size=9)
            for r in rows:
                row = table.row()
                row.cell(str(r.get("downloaded_at", ""))[:20])
                row.cell(str(r.get("source", ""))[:20])
                row.cell(str(r.get("title", "")))

        pdf.output(path)
        return

    # Fallback: minimal handmade PDF (single-line layout)
    lines = [
        title,
        f"Generado: {created_at}",
        "",
    ]

    for r in rows:
        lines.append(f"{r.get('downloaded_at')} | {r.get('source')} | {r.get('title')}")

    page_width = 595
    page_height = 842
    margin_x = 40
    margin_y = 40

    stream_lines = [
        "BT",
        "/F1 10 Tf",
        f"{margin_x} {page_height - margin_y} Td",
        "1 0 0 1 0 -14 Tm",  # line spacing
    ]

    for line in lines:
        stream_lines.append(f"({_escape_pdf_string(line)}) Tj")
        stream_lines.append("T*")

    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>\nendobj\n"
    )
    objects.append(
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )
    objects.append(
        b"5 0 obj\n<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream\nendobj\n"
    )

    pdf = BytesIO()
    pdf.write(b"%PDF-1.3\n")

    xref_positions = []
    for obj in objects:
        xref_positions.append(pdf.tell())
        pdf.write(obj)

    xref_start = pdf.tell()
    pdf.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for pos in xref_positions:
        pdf.write(b"%010d 00000 n \n" % pos)

    pdf.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%EOF\n"
        % (len(objects) + 1, xref_start)
    )

    with open(path, "wb") as f:
        f.write(pdf.getvalue())

def get_asp_data(soup):
    viewstate = soup.select_one("input[name='__VIEWSTATE']")["value"]    
    eventvalidation = soup.select_one("input[name='__EVENTVALIDATION']")["value"]
    viewstate_generator = soup.select_one("input[name='__VIEWSTATEGENERATOR']")["value"] # Datos asp.net

    return {"__VIEWSTATE":viewstate, "__EVENTVALIDATION":eventvalidation, "__VIEWSTATEGENERATOR":viewstate_generator}

def parse_ajax_response(response_text):
    # El formato AJAX de ASP.NET es: longitud|tipo|id|contenido|
    # Queremos el contenido que pertenece al updatePanel
    partes = response_text.split('|')
    
    # Buscamos el ViewState nuevo que SIEMPRE cambia en el POST
    new_asp_data = {}
    for i in range(len(partes)):
        if partes[i] in ["__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR"]:
            new_asp_data[partes[i]] = partes[i+1]
            
    # Intentamos extraer el HTML del bloque 'updatePanel'
    html_content = ""
    if "updatePanel" in partes:
        idx = partes.index("updatePanel")
        html_content = partes[idx + 2] # El HTML suele estar 2 posiciones después
        
    return html_content, new_asp_data