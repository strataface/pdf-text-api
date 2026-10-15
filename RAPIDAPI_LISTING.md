# RapidAPI Listing Copy — PDF Text & Tables (DRAFT, not published)

**Listing name (exact):** `PDF Text & Tables` (no "API"; RapidAPI appends it)  
**Logo to upload:** `/workspace/design/rapidapi-pdf-text/logo-500.png`

## Short description (≤ 100 chars — this one is 96)
Extract PDF text and CSV tables, OCR in 8 languages incl. Chinese & Japanese. No file retention.

## Long description
**PDF Text & Tables** turns PDFs into clean text and ready-to-use CSV (or Markdown) tables in one call.
Send a public PDF URL or upload the file directly.

- **Text layer first, OCR when needed**: `ocr=auto` OCRs only pages without a usable text layer
  (`always` / `never` also available). Per-page output says which pages were OCRed and how long it took.
- **8 OCR languages bundled**: English, German, French, Spanish, Italian, Portuguese, Simplified Chinese, Japanese.
  Combine with `+`, main language first (e.g. `chi_sim+eng`). Unknown codes are rejected with a clear 422.
- **Tables as CSV and/or Markdown**, with page number, rows and columns per table.
- **Password-protected PDFs** supported (password is never logged or echoed).
- **Metadata** (title, author, producer, dates), page count, and a `truncated` flag when the page limit applies.
- **No file retention**: PDFs are processed in memory and discarded when the response is sent (details below).

Good for invoice/receipt pipelines, RAG and search indexing, document intake forms, and pulling tables out of reports.

What it is not: no layout reconstruction, no handwriting recognition, no form-field (AcroForm) export; OCR quality
depends on scan quality (Tesseract engine). Large or long documents are refused or truncated (see limits).

## Endpoints
| Method & path | Description | Body |
|---|---|---|
| `POST /v1/extract` | Extract from a public PDF URL | JSON `{url, ocr, ocrLanguages, tableFormat, password, maxPages}` |
| `POST /v1/extract/upload` | Extract from an uploaded file | multipart `file` + same fields as form fields |
| `GET /health` | Service status and bundled OCR languages | — |

Parameters: `ocr` = `auto` (default) \| `always` \| `never`; `ocrLanguages` default `eng`; `tableFormat` = `none` (default) \|
`csv` \| `markdown` \| `both`; `maxPages` 1–20 (default 20).

### Example responses
Real responses captured from a local run of this exact code on 2026-10-15 (Asia/Shanghai); full files in `docs/smoke/`.
Strings longer than 200 chars are cut here with "…". Shown against the local server; on RapidAPI the host is the RapidAPI gateway.

**Upload a text PDF, tables as CSV**
```bash
curl -X POST "$BASE/v1/extract/upload" -F file=@text_table.pdf -F tableFormat=csv
```
```json
{
 "source": {
  "type": "upload",
  "filename": "text_table.pdf",
  "bytes": 2377
 },
 "pageCount": 2,
 "pagesProcessed": 2,
 "truncated": false,
 "encrypted": false,
 "metadata": {
  "title": "Sample Invoice",
  "author": "pdf-to-text tests",
  "subject": "(unspecified)",
  "creator": "(unspecified)",
  "producer": "ReportLab PDF Library - (opensource)",
  "creationdate": "D:20261015202940+08'00'",
  "moddate": "D:20261015202940+08'00'"
 },
 "ocrPages": 0,
 "text": "Quarterly Report 2026\nRevenue grew in every region during the third quarter.\nRegion Q2 Q3\nNorth 120 135\nSouth 98 110\n\nSecond page: notes and conclusions.",
 "pages": [
  {
   "page": 1,
   "text": "Quarterly Report 2026\nRevenue grew in every region during the third quarter.\nRegion Q2 Q3\nNorth 120 135\nSouth 98 110",
   "chars": 116,
   "ocr": false,
   "ocrSeconds": null,
   "error": null
  },
  {
   "page": 2,
   "text": "Second page: notes and conclusions.",
   "chars": 35,
   "ocr": false,
   "ocrSeconds": null,
   "error": null
  }
 ],
 "tables": [
  {
   "page": 1,
   "index": 1,
   "rows": 3,
   "cols": 3,
   "csv": "Region,Q2,Q3\nNorth,120,135\nSouth,98,110\n"
  }
 ],
 "tableCount": 1,
 "limits": {
  "maxPages": 20,
  "maxOcrPages": 5,
  "maxMB": 10
 },
 "seconds": 0.01
}
```

**Upload a scanned Chinese PDF (OCR)**
```bash
curl -X POST "$BASE/v1/extract/upload" -F file=@scanned_chi_sim.pdf -F ocrLanguages=chi_sim+eng
```
```json
{
 "source": {
  "type": "upload",
  "filename": "scanned_chi_sim.pdf",
  "bytes": 36449
 },
 "pageCount": 1,
 "pagesProcessed": 1,
 "truncated": false,
 "encrypted": false,
 "metadata": {
  "title": "scanned_chi_sim",
  "creationdate": "D:20261015122940Z",
  "moddate": "D:20261015122940Z"
 },
 "ocrPages": 1,
 "text": "发票号码 4711\n应付总额 250 欧元\n",
 "pages": [
  {
   "page": 1,
   "text": "发票号码 4711\n应付总额 250 欧元\n",
   "chars": 21,
   "ocr": true,
   "ocrSeconds": 0.38,
   "error": null,
   "textLayerChars": 0
  }
 ],
 "limits": {
  "maxPages": 20,
  "maxOcrPages": 5,
  "maxMB": 10
 },
 "seconds": 0.41
}
```

**From a URL** (IRS Form W-9, first page only)
```bash
curl -X POST "$BASE/v1/extract" -H 'Content-Type: application/json' \
  -d '{"url":"https://www.irs.gov/pub/irs-pdf/fw9.pdf","maxPages":1}'
```
```json
{
 "source": {
  "type": "url",
  "url": "https://www.irs.gov/pub/irs-pdf/fw9.pdf"
 },
 "pageCount": 6,
 "pagesProcessed": 1,
 "truncated": true,
 "encrypted": false,
 "metadata": {
  "title": "Form W-9 (Rev. March 2024)",
  "author": "SE:W:CAR:MP",
  "subject": "Request for Taxpayer Identification Number and Certification",
  "creator": "Designer 6.5",
  "producer": "Designer 6.5",
  "creationdate": "D:20240306081813-05'00'",
  "moddate": "D:20240306081813-05'00'"
 },
 "ocrPages": 0,
 "text": "W-9\nRequest for Taxpayer\nForm Give form to the\n(Rev. March 2024) Identification Number and Certification requester. Do not\nDepartment of the Treasury send to the IRS.\nGo to www.irs.gov/FormW9 for inst…",
 "pages": [
  {
   "page": 1,
   "text": "W-9\nRequest for Taxpayer\nForm Give form to the\n(Rev. March 2024) Identification Number and Certification requester. Do not\nDepartment of the Treasury send to the IRS.\nGo to www.irs.gov/FormW9 for inst…",
   "chars": 5659,
   "ocr": false,
   "ocrSeconds": null,
   "error": null
  }
 ],
 "limits": {
  "maxPages": 20,
  "maxOcrPages": 5,
  "maxMB": 10
 },
 "seconds": 0.15
}
```
(Captured in a sandbox whose DNS is faked, so it ran with the test-only `PDFTEXT_ALLOW_CIDRS` override; in production that variable stays unset.)

**Health**
```json
{
 "status": "ok",
 "version": "0.1.0",
 "ocrLanguages": [
  "eng",
  "deu",
  "fra",
  "spa",
  "ita",
  "por",
  "chi_sim",
  "jpn"
 ]
}
```

**Errors** (`{error, detail}`)
```json
{
 "error": "invalid_ocr_language",
 "detail": "Unsupported OCR language(s): xx. Available: eng, deu, fra, spa, ita, por, chi_sim, jpn"
}
{
 "error": "fetch_failed",
 "detail": "URL resolves to a private, loopback or otherwise non-public address"
}
```
Status codes: 400/403 bad or non-public URL · 401 password required/wrong · 413 too large · 415 not a PDF ·
422 validation / unknown OCR language · 429 rate limited · 502/504 remote download failed or timed out.

## Usage limits (server defaults, env-overridable)
| Limit | Default | Env |
|---|---|---|
| File size | 10 MB | `PDFTEXT_MAX_MB` |
| Pages processed per request | 20 (more → `truncated: true`) | `PDFTEXT_MAX_PAGES` |
| OCR pages per request | 5 (further pages: text layer only, with a per-page note) | `PDFTEXT_MAX_OCR_PAGES` |
| Extraction time budget | ~60 s | `PDFTEXT_TIME_BUDGET_S` |
| URL download timeout | 20 s, max 3 redirects | `PDFTEXT_DOWNLOAD_TIMEOUT_S` |
| Concurrent extractions per instance | 2 | `PDFTEXT_CONCURRENCY` |
| Requests per minute per client | 20 | `PDFTEXT_RATE_PER_MIN` |
Monthly quotas per plan are enforced by RapidAPI plan configuration, not by the server.

## Suggested plans (draft)
| Plan | Price | Quota | Per 1,000 requests | Your net after RapidAPI 25% |
|---|---|---|---|---|
| Free (BASIC) | $0 | 100 requests / month, hard limit | – | $0 |
| Basic (PRO) | $5 / month | 2,000 requests / month, hard limit | $2.50 | $3.75 |
| Pro (ULTRA) | $15 / month | 10,000 requests / month, hard limit | $1.50 | $11.25 |

Benchmarks (from seo/48, captured 2026-10-15; RapidAPI figures are search-index snapshots, **not verified live**):
- RapidAPI "PDF To Text Converter": $2 / 100, $5 / 500, $7 / 1,000 per month ($7–$20 per 1,000) — not verified live
- RapidAPI "OCR Wizard": free 30 pages; $12.99 / 5,000 ($2.60 per 1,000) — not verified live
- OCR.space (direct, verified): Free 25,000/mo; PRO $30 / 300,000 ($0.10 per 1,000), but 3-page PDF cap on Free/PRO
- pdfRest (direct, verified): $9.99 / 600 ($16.65 per 1,000)
Positioning: cheaper per request than the comparable small RapidAPI listings, more expensive than OCR.space, justified by
CSV tables, 8 bundled languages incl. CJK, 20 pages / 5 OCR pages per call, and no retention. Hard limits (no overage)
avoid surprise bills while the backend runs on a small instance.
Capacity caveat: a free-tier host (0.1 vCPU) will OCR far slower than the local box (0.38 s/page measured locally);
re-measure on the real host before raising quotas.

## Net revenue math (estimates)
- RapidAPI marketplace fee: **25%** ([Payouts and Finance](https://docs.rapidapi.com/docs/payouts-and-finance), see seo/47;
  the same page still shows an older 20% example — budget with 25%). Paid monthly via PayPal only, with about a one-month lag.
- PayPal: withdrawal from a PayPal balance to a **mainland China bank: 35.00 USD per withdrawal** (PayPal China fee page
  https://www.paypal.com/c2/webapps/mpp/paypal-fees and /merchant-fees, fetched 2026-10-15, saved in `docs/evidence/`).
  Withdrawal to a Hong Kong bank: free if ≥ 1,000 HKD and no currency conversion. Currency conversion: 3.5%–4% for USD (same page).
- PayPal fee on **receiving** the RapidAPI payout itself: **not verified** (RapidAPI does not document it; depends on account type/region).

| Scenario (per month) | Gross | After 25% | After one $35 mainland withdrawal |
|---|---|---|---|
| 1 Basic subscriber | $5 | $3.75 | – (accumulate; withdrawing would lose money) |
| 10 Basic | $50 | $37.50 | $2.50 |
| 5 Basic + 2 Pro | $55 | $41.25 | $6.25 |
| 3 Pro | $45 | $33.75 | – (below $35) |
Break-even for one mainland withdrawal: 9.3 Basic-months or 3.1 Pro-months of net revenue → withdraw rarely, in large amounts.
Hosting cost not included (free tier unavailable without a card so far; see DEPLOY.md). Zero subscribers is a realistic outcome; no demand figures are verified.

## Privacy & data handling
- **No file retention by the app**: the PDF (uploaded or downloaded) is held in memory for the request and discarded
  afterwards. The app writes no files; the OCR engine's scratch image per page is deleted immediately (tested: temp dir empty after requests).
- **Nothing stored or logged about content**: no database, no queue, no cache. HTTP access logs are disabled in the server;
  error messages never include the password.
- **URL fetching**: only the URL you send is downloaded (no crawling, max 3 redirects). Private, loopback, link-local
  (cloud metadata), CGNAT and reserved addresses are refused, re-checked on every redirect; only ports 80/443/8080/8443.
- **Honest caveats**: the hosting provider and the RapidAPI gateway sit in front of the app and keep their own request
  logs/metadata (IP, URL path, timing, sizes) under their own policies; we do not control those. Request bodies are not
  logged by the app. Text returned to you is your responsibility to store securely.

## Not done
Not published. Base URL not yet available (hosting blocked on a card requirement). Pricing is a draft for sail's decision.
