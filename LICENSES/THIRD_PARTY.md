# Third-party components and licenses (checked 2026-10-15 from installed package metadata / project pages)

All runtime dependencies permit commercial use. No AGPL/GPL code is linked or shipped by this Actor.

| Component | Version tested | License | Use |
|---|---|---|---|
| pypdf | 6.20.1 | BSD-3-Clause | open, decrypt, metadata |
| pdfplumber | 0.11.10 | MIT | text + table extraction |
| pdfminer.six | 20260107 | MIT | text layout engine (pdfplumber dependency) |
| pypdfium2 | 5.14.0 | BSD-3-Clause / Apache-2.0 (bundles PDFium, BSD-3-Clause) | render pages to images for OCR |
| pytesseract | 0.3.13 | Apache-2.0 | Python wrapper for Tesseract |
| Tesseract OCR (Debian `tesseract-ocr`) | 5.5.0 | Apache-2.0 | OCR engine (installed in Docker image) |
| tessdata language files | Debian packages | Apache-2.0 | OCR models |
| Pillow | 12.3.0 | MIT-CMU (HPND) | images |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | AES-encrypted PDFs (pypdf) |
| httpx | – | BSD-3-Clause | downloads |
| apify SDK | – | Apache-2.0 | Actor runtime |

Deliberately **not** used:
- PyMuPDF / MuPDF — AGPL-3.0 (or commercial licence from Artifex).
- pdf2image — MIT itself, but requires Poppler (GPL-2.0/3.0) binaries; we render with pypdfium2 instead.
- Dev/test only (not in the image): reportlab (BSD) to generate sample PDFs, pytest (MIT).

Note: the base image `apify/actor-python` is a Debian system that may contain GPL system packages (e.g. coreutils); those are separate programs, not linked into this Actor's code.

## Additional components in the HTTP API (pdf-text)

| Component | License | Use |
|---|---|---|
| FastAPI | MIT | web framework |
| Starlette / Pydantic | BSD-3 / MIT | FastAPI deps |
| Uvicorn | BSD-3 | ASGI server |
| python-multipart | Apache-2.0 | upload parsing |
| httpx | BSD-3 | URL download |

`app/vendor/` is copied from `/workspace/earn/apify/pdf-to-text/src` (same author, v0.2) with an added OCR page cap and time budget.
