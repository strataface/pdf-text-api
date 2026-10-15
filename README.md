# PDF Text & Tables API (pdf-text)

Stateless HTTP API that turns PDFs into text and CSV/Markdown tables, with Tesseract OCR for scanned pages.
Backend intended for a RapidAPI listing. **Status: local only — not deployed, not listed.**

## Endpoints
| Method | Path | Body |
|---|---|---|
| GET | `/health` | – (exempt from proxy secret and rate limit) |
| POST | `/v1/extract` | JSON `{url, ocr: auto\|always\|never, ocrLanguages: "eng", tableFormat: none\|csv\|markdown\|both, password?, maxPages?}` |
| POST | `/v1/extract/upload` | multipart: `file` + same fields as form fields |
| GET | `/openapi.json`, `/docs` | OpenAPI 3 (static copy: `openapi.json`, regenerate with `python scripts/export_openapi.py`) |

Response: `text`, `pages[] {page, text, chars, ocr, ocrSeconds, error}`, `tables[] {page, index, rows, cols, csv?, markdown?}`,
`pageCount`, `pagesProcessed`, `truncated`, `ocrPages`, `metadata`, `seconds`.
Errors: `{error, detail}` with 400/403 (bad or private URL), 401 (password), 413 (too large), 415 (not a PDF),
422 (validation, unknown OCR language), 429 (rate limit), 502/504 (remote fetch).

OCR languages: eng, deu, fra, spa, ita, por, chi_sim, jpn — join with `+`, main language first (`chi_sim+eng`).

## Safety & privacy
- **Only the URL you send is fetched** (no crawling); up to 3 redirects, each re-checked.
- **SSRF guard**: http/https only, ports 80/443/8080/8443, no URL credentials; every resolved address must be public
  (blocks loopback, RFC1918, link-local/metadata 169.254.x, CGNAT, IPv4-mapped IPv6, reserved).
  Residual risk: DNS rebinding between the check and the connect is not pinned — acceptable for a stateless free service, noted for review.
- **No disk retention**: PDF bytes stay in memory for the request; the app writes nothing; pytesseract's scratch image is deleted after each page
  (test asserts the temp dir is empty). Uvicorn access log is off; passwords are never echoed in errors.
- Limits (env-overridable): 10 MB (`PDFTEXT_MAX_MB`), 20 pages (`PDFTEXT_MAX_PAGES`), 5 OCR pages (`PDFTEXT_MAX_OCR_PAGES`),
  60 s budget (`PDFTEXT_TIME_BUDGET_S`), 2 concurrent extractions, 20 req/min per client (`PDFTEXT_RATE_PER_MIN`, in-memory, per instance).
- `RAPIDAPI_PROXY_SECRET` set → every route except /health and docs requires a matching `X-RapidAPI-Proxy-Secret` (off when unset).
  Behind that secret the rate limit keys on `X-RapidAPI-User`; set `PDFTEXT_TRUST_PROXY=1` on hosts with a front proxy to key on X-Forwarded-For.

## Run locally
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim ...   # see Dockerfile
.venv/bin/pytest -q
.venv/bin/uvicorn app.main:app --port 8000
curl -F file=@tests/samples/scanned.pdf localhost:8000/v1/extract/upload
```
Sandbox note: this box resolves every hostname to 198.18.0.1 (fake DNS), so URL mode is refused here unless
`PDFTEXT_ALLOW_CIDRS=198.18.0.0/15` is set (testing only; never set it in production).

## Deploy
See `DEPLOY.md`. Docker image honours `$PORT`.

## Licenses
`app/vendor/` is vendored from `apify/pdf-to-text` v0.2. See `LICENSES/THIRD_PARTY.md` — no AGPL/GPL code linked (Tesseract is Apache-2.0).
