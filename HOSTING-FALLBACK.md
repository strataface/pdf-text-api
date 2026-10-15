# Hosting fallback research (2026-10-16 ~02:30 Asia/Shanghai, read-only, no signup/card)

Context: Render requires a card for this account (API 402, see DEPLOY.md history); HF Docker/Gradio Spaces need PRO;
Koyeb may ask for a card. Needs: Python + Tesseract (apt) + ~300 MB RAM peak, arbitrary outbound HTTPS (URL mode), commercial API use.

## PythonAnywhere free ("Beginner") — not suitable
| Question | Answer (official text) |
|---|---|
| Limits | "Free accounts … support the following features: 100 CPU seconds, 512 MiB of disk space, 1 web app with 1 web worker and 1 month expiry, 2 consoles" — https://help.pythonanywhere.com/pages/FreeAccountsFeatures/ |
| Outbound internet | "one web app at your-username.pythonanywhere.com and two consoles with restricted outbound Internet access" (https://www.pythonanywhere.com/pricing/); "The following sites are allowlisted for free PythonAnywhere accounts. Paid accounts have unrestricted access." (https://www.pythonanywhere.com/whitelist/) → **URL mode would fail for most PDF hosts.** |
| FastAPI/ASGI | "deployment of ASGI … websites on PythonAnywhere is an experimental feature … We have not worked out the long-term pricing for ASGI sites … We're 99.9% certain that there will be a way to host them in a free plan" (https://help.pythonanywhere.com/pages/ASGICommandLine/) → free availability **not verified**. |
| Tesseract | "You don't have root access … so you can't use tools like apt to install packages" (https://help.pythonanywhere.com/pages/InstallingNewModules/). `pytesseract` wrapper is listed in batteries-included; a system `tesseract` binary + language packs: **not verified**. 512 MiB disk is tight for 8 tessdata packs. |
| Expiry | Free web app has "1 month expiry" (must be renewed in the UI). |
| Domain/HTTPS | Free = `username.pythonanywhere.com` only; "All accounts (including free ones) have … free SSL support" (pricing page). Custom domains are paid. |
| Commercial use | Terms (https://www.pythonanywhere.com/terms/) contain no explicit commercial ban found by keyword search; **not verified**. |
| Card | Beginner $0, no card mentioned on pricing page. |

## Other hosts
| Host | Card? | RAM/CPU free | Tesseract / Docker | Deploy | Commercial | Verdict |
|---|---|---|---|---|---|---|
| **Leapcell** Hobby | Official pricing shows "Hobby … $0 per seat / month" with no card step; "no credit card required" is from a third-party video (YouTube xhOALd640tA) → **card: likely no, not officially stated** | "Up to 3 vCPUs per project (3 vCPUs, 4GB RAM)"; serverless ("we only charge when requests come in") — https://leapcell.io/pricing, https://leapcell.io/ | "Python Debian … Includes apt-get for installing more dependencies" (https://docs.leapcell.io/docs/application) → `apt-get install tesseract-ocr …` in build command; no Dockerfile needed | "Import from GitHub Repo OR Submit Link" (homepage) → **needs a GitHub repo = push** | Fair Use "Allowed Use Cases: … APIs + Backends … Tool API Serving … More fair and legal business scenarios" (https://docs.leapcell.io/fair-use/) | **Best fit** (RAM, apt, API use allowed). Hobby quotas (requests, timeout, build minutes) not verified. |
| Back4app Containers | "no credit card required" (https://www.back4app.com/pricing/container-as-a-service) | "0.25 CPU 256 MB RAM 100 GB Transfer" | "Custom Docker containers" (our Dockerfile works as-is) | "Deployment from GitHub" via GitHub App → **push** | not verified | Fallback; 256 MB is tight for chi_sim/jpn OCR (set PDFTEXT_CONCURRENCY=1). Sleep: third-party says 2–5 min cold start (not official). |
| Northflank Sandbox | **Yes**: "all users must add a payment method to start creating resources on Northflank, regardless of plan selection" (https://northflank.com/docs/v1/application/billing/pricing-on-northflank) | 2 free services, always-on | Docker | Git/registry | – | Out (card). |
| Alwaysdata Free | not stated | "Disk space SSD 1 Go … RAM 256 Mo … CPU ¼"; "Free For personal needs" (https://www.alwaysdata.com/en/pricing/) | no root/apt (not verified) | SSH upload | "personal needs" → commercial doubtful | Out. |
| Vercel Hobby | no | Python functions, "Size (uncompressed) 250 MB, or 500 MB for Python" (https://vercel.com/docs/functions/limitations) | no apt; Tesseract binary would have to be bundled | Git/CLI | "the Hobby plan restricts users to non-commercial, personal use only" (https://vercel.com/docs/plans/hobby) | Out (non-commercial). |
| Glitch | – | – | – | – | "On July 8, 2025 Glitch project hosting and user profiles will be shut down" (https://blog.glitch.com/post/changes-are-coming-to-glitch/) | Out (gone). |
| Serv00 | "3 GB for free" (https://serv00.com/) | shared FreeBSD hosting | no Docker; tesseract not verified | SSH | not verified | Out (no Docker, FreeBSD). |
| Zeabur Free | – | free plan only manages your own servers (https://zeabur.com/pricing) | – | – | – | Out. |
| Adaptable.io | site unreachable (curl 000) | – | – | – | – | Not verified / likely gone. |
| Replit | usage-limits doc 404; not researched further | – | – | – | – | Not verified. |
| Deta Space | not researched (service sunset reported earlier; not verified) | | | | | |
SMS verification: none of the official pages above mention it (not verified either way).

## What every no-card option has in common
Leapcell and Back4app both deploy from a GitHub repo, so a repo must be created and pushed (e.g. private repo under
Sailgagag, gh is authenticated on the box) — that push needs explicit approval. Neither offers a CLI/archive upload on free.

**Preferred: Leapcell Hobby (Python Debian runtime + apt tesseract, 4 GB RAM, APIs allowed); sail must act — sign up (email/GitHub) and approve creating+pushing a private GitHub repo for pdf-text.**
