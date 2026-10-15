"""PDF bytes -> per-page text (pdfminer via pdfplumber), optional OCR (pypdfium2 render + Tesseract)."""
import csv, io, time
import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError
from . import config


class PdfError(Exception):
    pass


def open_reader(data, password=None):
    if not data.lstrip()[:5].startswith(b"%PDF"):
        raise PdfError("not a PDF (missing %PDF header)")
    try:
        r = PdfReader(io.BytesIO(data))
    except (PdfReadError, ValueError) as e:
        raise PdfError(f"unreadable PDF: {e}")
    encrypted = r.is_encrypted
    if encrypted:
        ok = 0
        try:
            ok = r.decrypt(password or "")
        except Exception as e:
            raise PdfError(f"cannot decrypt: {e}")
        if not ok:
            raise PdfError("encrypted PDF: password required" if not password else "encrypted PDF: wrong password")
    return r, encrypted


def metadata(reader):
    md = {}
    try:
        info = reader.metadata or {}
        for k in ("/Title", "/Author", "/Subject", "/Creator", "/Producer", "/CreationDate", "/ModDate"):
            v = info.get(k)
            if v:
                md[k[1:].lower()] = str(v)
    except Exception:
        pass
    return md


def ocr_page(pdf, idx, lang, dpi=config.OCR_DPI):
    import pytesseract
    page = pdf[idx]
    img = page.render(scale=dpi / 72).to_pil()
    t = time.monotonic()
    txt = pytesseract.image_to_string(img, lang=lang, timeout=config.OCR_PAGE_TIMEOUT_S)
    return txt, time.monotonic() - t


def clean_table(tbl):
    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in tbl if r]
    w = max((len(r) for r in rows), default=0)
    return [r + [""] * (w - len(r)) for r in rows]


def table_csv(tbl):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(clean_table(tbl))
    return buf.getvalue()


def table_md(tbl):
    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in tbl if r]
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def extract_pdf(data, password=None, ocr_mode="auto", ocr_lang="eng", min_chars=25, max_pages=200, tables=(), max_ocr_pages=None, deadline=None):
    """tables: iterable of formats, subset of {"csv", "markdown"}; empty = no table extraction."""
    if tables is True:
        tables = ("csv", "markdown")
    tables = tuple(tables or ())
    reader, encrypted = open_reader(data, password)
    n = len(reader.pages)
    todo = min(n, max_pages)
    pages = []
    try:
        plumber = pdfplumber.open(io.BytesIO(data), password=password or "")
    except Exception as e:
        raise PdfError(f"text extraction failed to open: {e}")
    pdf = None
    ocr_done = 0
    with plumber:
        for i in range(todo):
            p = plumber.pages[i]
            try:
                text = p.extract_text() or ""
            except Exception as e:
                text = ""
            rec = {"page": i + 1, "text": text, "chars": len(text.strip()), "ocr": False, "ocrSeconds": None, "error": None}
            if tables:
                try:
                    found = [t for t in p.extract_tables() if t and clean_table(t)]
                    rec["tables"] = [{"index": k + 1, "rows": len(clean_table(t)), "cols": len(clean_table(t)[0]),
                                      **({"csv": table_csv(t)} if "csv" in tables else {}),
                                      **({"markdown": table_md(t)} if "markdown" in tables else {})} for k, t in enumerate(found)]
                except Exception:
                    rec["tables"] = []
            if deadline is not None and time.monotonic() > deadline:
                rec["error"] = "time budget exceeded; page skipped"
                rec["text"] = ""
                pages.append(rec)
                break
            need = ocr_mode == "always" or (ocr_mode == "auto" and rec["chars"] < min_chars)
            if need and max_ocr_pages is not None and ocr_done >= max_ocr_pages:
                need = False
                rec["error"] = f"OCR page cap ({max_ocr_pages}) reached; text layer only"
            if need:
                ocr_done += 1
                try:
                    if pdf is None:
                        pdf = pdfium.PdfDocument(data, password=password)
                    t, secs = ocr_page(pdf, i, ocr_lang)
                    rec.update(text=t, chars=len(t.strip()), ocr=True, ocrSeconds=round(secs, 2), textLayerChars=len(text.strip()))
                except Exception as e:
                    rec["error"] = f"OCR failed: {type(e).__name__}: {e}"[:200]
            pages.append(rec)
    if pdf is not None:
        pdf.close()
    return {"pageCount": n, "pagesProcessed": todo, "truncated": todo < n, "encrypted": encrypted,
            "metadata": metadata(reader), "pages": pages}
