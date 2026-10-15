# Leapcell deploy recipe (draft — no account, no repo yet)

Docs used (fetched 2026-10-16): https://docs.leapcell.io/service/ (Serverless mode, "Packaging and Deployment"),
https://docs.leapcell.io/docs/application (runtimes), https://docs.leapcell.io/fair-use/ .

## Service form (field names as in the docs' "Configuration Details")
| Field | Value |
|---|---|
| **Runtime** | `Python Debian` — docs: "Python Debian \| Python 3.11.2, pip, apt-get \| Includes apt-get for installing more dependencies" |
| **Build Command** | see below |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log` |
| **Serving Port** | `8080` — docs: "The port your service listens on (default: `8080`). Ensure this matches the port in your Start Command." (Leapcell does not document a `$PORT` variable, hence the `:-8080` default.) |
| **Environment Variables** | see below — docs: "Configure them via the Service > Environment section" |
| Health check `/health` | No health-check field is documented on the pages above → **not verified**; `/health` exists and is cheap if a field appears. |
| Memory | Serverless memory is configurable; docs table: "256 MB \| CPU Cap 14.1%", 128–1769 MB = 1 core. **Pick ≥ 512 MB, preferably 1024 MB** (see memory results). |

Build Command (one line):
```
apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-fra tesseract-ocr-spa tesseract-ocr-ita tesseract-ocr-por tesseract-ocr-chi-sim tesseract-ocr-jpn && pip install -r requirements.txt
```
(The docs' own example runs `apt-get update && apt-get install -y …` in the Build Command. Whether apt runs as root there is implied, not stated.)

Environment Variables:
| Name | Value | Note |
|---|---|---|
| `OMP_THREAD_LIMIT` | `1` | same as Dockerfile; keeps Tesseract to one thread |
| `PDFTEXT_CONCURRENCY` | `1` | ≤1 GB memory |
| `PDFTEXT_MAX_OCR_PAGES` | `3` | lower than default 5 because the CPU share is small (5 OCR pages took 19.5 s at full CPU locally) |
| `PDFTEXT_TIME_BUDGET_S` | `60` | default |
| `PDFTEXT_MAX_MB` / `PDFTEXT_MAX_PAGES` / `PDFTEXT_RATE_PER_MIN` | `10` / `20` / `20` | defaults |
| `PDFTEXT_TRUST_PROXY` | `1` | rate-limit key from X-Forwarded-For behind Leapcell's proxy |
| `RAPIDAPI_PROXY_SECRET` | **unset for now** | set when the RapidAPI listing exists; enables the 403 gate |
| `PDFTEXT_ALLOW_CIDRS` | **never set in production** | test-only SSRF bypass |

Storage note: docs say "Only the `/tmp` directory is writable"; pytesseract's per-page scratch file goes to `/tmp` and is deleted immediately — compatible.
Cold starts: serverless, "we only charge when requests come in"; first request after idle pays Tesseract/Python start (~1 s locally; on Leapcell not measured).

## Differences vs Dockerfile
| | Dockerfile (Back4app/Koyeb/Render) | Leapcell |
|---|---|---|
| Base | python:3.12-slim (Debian) | Python Debian runtime, Python 3.11.2 (docs) |
| Tesseract | same 8 apt packages | same 8 apt packages in Build Command |
| User | non-root uid 1000 | platform-managed |
| Port | `$PORT` default 8000 | Serving Port 8080 (`${PORT:-8080}`) |
| Flags | `--proxy-headers --forwarded-allow-ips='*'` | not needed for app logic (PDFTEXT_TRUST_PROXY reads X-Forwarded-For directly) |
| Concurrency default | 2 | set 1 via env |

## Back4app fallback
Uses the existing `Dockerfile` unchanged (Back4app: "Custom Docker containers", free "0.25 CPU 256 MB RAM", deploy via GitHub App).
Set env `PDFTEXT_CONCURRENCY=1`, `PDFTEXT_MAX_OCR_PAGES=1`, `PORT=8000`. With 256 MB only text PDFs and single-page OCR fit (measurements below);
multi-page OCR risks OOM kills. Leapcell at 1024 MB is the primary path.

## Local smoke mimicking the Leapcell build (2026-10-16)
Fidelity, honestly: **no Docker/chroot.** Clean copy via `git archive HEAD` into /tmp/lc-smoke, fresh venv with **Python 3.11.17** (uv; Leapcell lists 3.11.2),
`pip install -r requirements.txt`; Tesseract from the box's Debian 13 apt packages (tesseract 5.5.0, tessdata 4.1.0) — Leapcell's Debian release
and Tesseract version are not documented, so OCR output/speed may differ. No CPU cap was applied (box CPU is far faster than a 14%-cap instance).
- pytest in the clean venv: **32 passed**
- Start command run as written with PORT=8080; `/health` OK; text PDF → CSV table OK; scanned eng OK; scanned chi_sim+eng → "发票号码 4711 / 应付总额 250 欧元".
- Memory (psutil, process tree = uvicorn + tesseract children, sampled every 10 ms; RSS counts shared libs, so slightly overstated) — `scripts/memprobe.py`:

| Phase | Peak tree RSS | Peak Python RSS | Time |
|---|---|---|---|
| idle after start | 80.7 MB | 80.7 MB | – |
| text PDF + CSV tables | 80.9 MB | 80.9 MB | 0.12 s |
| scanned 1 page, eng | 172.8 MB | 101.6 MB | 0.57 s |
| scanned 1 page, chi_sim+eng | 188.1 MB | 95.3 MB | 0.47 s |
| IRS W-9 (6 p) ocr=always, 5-page cap, eng | 264.1 MB | 181.6 MB | 19.5 s |
| same, jpn+chi_sim+eng | 367.2 MB | 185.8 MB | 28.1 s |
| 2 parallel W-9 chi_sim+eng, concurrency 2 | 554.2 MB | 285.9 MB | 31.2 s |
| 2 parallel, concurrency 1 | 359.0 MB | 212.2 MB | 50.2 s |

**256 MB verdict: not enough for general use.** Text-only and single-page OCR fit (≤ ~190 MB), but multi-page OCR reaches 264 MB (eng) to 367 MB (CJK).
Use ≥ 512 MB with concurrency 1 (≤ ~370 MB measured), 1024 MB for headroom and CPU. On a 14%-CPU-cap instance, 5 OCR pages would exceed the 60 s budget → OCR cap 3 (pages past the budget are returned with an error note, not silently dropped).
