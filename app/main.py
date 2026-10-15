"""PDF text/table extraction API (FastAPI). Stateless: PDFs live only in memory for the request."""
import asyncio, base64, time
from typing import Literal, Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from . import settings
from .fetch import fetch_pdf, FetchError
from .middleware import ProxySecretMiddleware, RateLimitMiddleware
from .vendor import extract, langs, config as vconfig

vconfig.OCR_PAGE_TIMEOUT_S = min(vconfig.OCR_PAGE_TIMEOUT_S, 30)

DESCRIPTION = f"""Extract text and tables from PDFs, with optional OCR for scanned pages
(Tesseract; languages: {', '.join(langs.BUNDLED)}).

* Only the URL you send is fetched (no crawling). Private/loopback addresses are refused.
* **No file retention**: the PDF is held in memory for the request only and never written to disk
  or logged; OCR scratch images are removed by the OCR wrapper right after each page.
* Limits: {settings.MAX_BYTES // 2**20} MB, {settings.MAX_PAGES} pages, {settings.MAX_OCR_PAGES} OCR pages,
  ~{settings.TIME_BUDGET_S} s per request, {settings.RATE_PER_MIN} requests/min per client.
"""

app = FastAPI(title="PDF Text & Tables API", version=settings.VERSION, description=DESCRIPTION)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ProxySecretMiddleware)   # added last = runs first
_sem = asyncio.Semaphore(settings.CONCURRENCY)

OcrMode = Literal["auto", "always", "never"]
TableFormat = Literal["none", "csv", "markdown", "both"]


class ExtractRequest(BaseModel):
    url: HttpUrl = Field(..., description="Public http(s) URL of a PDF.")
    ocr: OcrMode = Field("auto", description="auto = OCR only pages without a text layer.")
    ocrLanguages: str = Field("eng", description="Tesseract codes joined by '+', main language first, e.g. chi_sim+eng.")
    tableFormat: TableFormat = "none"
    password: Optional[str] = Field(None, description="Password for encrypted PDFs (not logged).")
    maxPages: int = Field(settings.MAX_PAGES, ge=1, le=settings.MAX_PAGES)


def _err(status, code, detail):
    return JSONResponse(status_code=status, content={"error": code, "detail": detail})


def _formats(tf):
    return {"none": (), "csv": ("csv",), "markdown": ("markdown",), "both": ("csv", "markdown")}[tf]


async def _run(data, *, ocr, ocrLanguages, tableFormat, password, maxPages, source):
    try:
        lang = langs.validate(ocrLanguages)
    except ValueError as e:
        return _err(422, "invalid_ocr_language", str(e))
    if not data.startswith(b"%PDF") and b"%PDF" not in data[:1024]:
        return _err(415, "not_a_pdf", "content does not look like a PDF")
    t0 = time.monotonic()
    deadline = t0 + settings.TIME_BUDGET_S
    async with _sem:
        try:
            res = await asyncio.wait_for(asyncio.to_thread(
                extract.extract_pdf, data, password=password, ocr_mode=ocr, ocr_lang=lang,
                max_pages=min(maxPages, settings.MAX_PAGES), tables=_formats(tableFormat),
                max_ocr_pages=settings.MAX_OCR_PAGES, deadline=deadline), timeout=settings.TIME_BUDGET_S + 35)
        except asyncio.TimeoutError:
            return _err(504, "timeout", "extraction exceeded the time limit")
        except extract.PdfError as e:
            msg = str(e)
            if password:
                msg = msg.replace(password, "***")
            status = 401 if "password" in msg.lower() or "encrypt" in msg.lower() else 422
            return _err(status, "pdf_error", msg[:300])
        finally:
            del data
    pages = res["pages"]
    tables = [{"page": p["page"], **t} for p in pages for t in p.pop("tables", [])]
    return {
        "source": source,
        "pageCount": res["pageCount"], "pagesProcessed": res["pagesProcessed"], "truncated": res["truncated"],
        "encrypted": res["encrypted"], "metadata": res["metadata"],
        "ocrPages": sum(1 for p in pages if p["ocr"]),
        "text": "\n\n".join(p["text"] for p in pages),
        "pages": pages,
        **({"tables": tables, "tableCount": len(tables)} if tableFormat != "none" else {}),
        "limits": {"maxPages": settings.MAX_PAGES, "maxOcrPages": settings.MAX_OCR_PAGES,
                   "maxMB": settings.MAX_BYTES // 2**20},
        "seconds": round(time.monotonic() - t0, 2),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "ocrLanguages": list(langs.BUNDLED)}


@app.post("/v1/extract", summary="Extract text/tables from a PDF URL")
async def extract_url(req: ExtractRequest):
    try:
        data = await fetch_pdf(str(req.url))
    except FetchError as e:
        return _err(e.status, "fetch_failed", str(e))
    return await _run(data, ocr=req.ocr, ocrLanguages=req.ocrLanguages, tableFormat=req.tableFormat,
                      password=req.password, maxPages=req.maxPages, source={"type": "url", "url": str(req.url)})


@app.post("/v1/extract/upload", summary="Extract text/tables from an uploaded PDF (multipart)")
async def extract_upload(file: UploadFile = File(..., description="PDF file"),
                         ocr: OcrMode = Form("auto"), ocrLanguages: str = Form("eng"),
                         tableFormat: TableFormat = Form("none"), password: Optional[str] = Form(None),
                         maxPages: int = Form(settings.MAX_PAGES, ge=1, le=settings.MAX_PAGES)):
    buf = bytearray()
    while chunk := await file.read(1 << 20):
        buf += chunk
        if len(buf) > settings.MAX_BYTES:
            await file.close()
            return _err(413, "too_large", f"file larger than {settings.MAX_BYTES // 2**20} MB limit")
    await file.close()
    return await _run(bytes(buf), ocr=ocr, ocrLanguages=ocrLanguages, tableFormat=tableFormat,
                      password=password, maxPages=maxPages,
                      source={"type": "upload", "filename": (file.filename or "")[:200], "bytes": len(buf)})
