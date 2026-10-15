# Deploy options (researched 2026-10-15, nothing signed up / deployed)

| Host | Card? | Free RAM/CPU | Sleep | Deploy without pushing to GitHub? | Source |
|---|---|---|---|---|---|
| **Koyeb** | Only if their automatic "is human" check fails (then card + $29 pre-auth hold, released) | 512 MB / 0.1 vCPU, 1 free service, fra or was | scale-to-zero after 1 h idle | **Yes**: `koyeb deploy .` uploads the directory as an archive (≤50 MB) and builds the Dockerfile | koyeb.com/docs/reference/instances, /docs/faqs/pricing, /blog/sustaining-free-compute-in-a-hostile-environment, /docs/build-and-deploy/deploy-project-directory |
| **Render** | No (docs: "No payment is required") | 512 MB / 0.1 CPU, 750 h/month | spins down after 15 min, ~1 min cold start | No: needs a Git repo (public URL, or private repo via GitHub connect) or a registry image | render.com/docs/free, /docs/your-first-deploy, /docs/deploying-an-image |
| Railway | No for trial; limited trial unless GitHub verified | trial $5 once / 30 days, then $1/month credit | – | CLI `railway up` uploads | docs.railway.com/reference/pricing/free-trial |
| Fly.io | Trial no card, but only 2 h machine time or 7 days; then card | – | – | `fly deploy` (CLI) | fly.io/docs/about/pricing |
| Cloud Run | Billing account with card required (free trial signup asks for a payment method) | free tier 360k GB-s | scale to zero | gcloud source deploy | cloud.google.com/free/docs/free-cloud-features |
| HF Spaces (Docker) | **Docker Spaces now need a PRO plan** | (CPU Basic 2 vCPU / 16 GB) | sleeps when unused | git/hub upload | huggingface.co/docs/hub/spaces-overview |
| Zeabur | Free plan only manages your own servers (no hosted compute); Dev $5/mo after 14-day trial | – | – | – | zeabur.com/pricing |

SMS verification is not mentioned in any of these official pages (unverified either way).

## Recommended: Koyeb archive deploy (fallback: Render)
Browser steps (sail/parent):
1. app.koyeb.com/auth/signup → email `<OWNER_EMAIL>` + password (or GitHub/Google). Confirm email.
   If a card is demanded → stop (blocker; go to Render).
2. Dashboard → Settings → API → create token; give it to the box as env `KOYEB_TOKEN` (never committed).
Box steps (agent, after approval to deploy):
3. Install koyeb CLI (`curl -fsSL https://raw.githubusercontent.com/koyeb/koyeb-cli/master/install.sh | sh`).
4. `RAPIDAPI_PROXY_SECRET=... scripts/deploy_koyeb.sh` (verify flags with `koyeb deploy --help` first) →
   URL `https://<app>-<org>.koyeb.app`; curl smoke /health + text + scanned.

Fallback Render: sign up (email or GitHub) → New Web Service → needs a repo: either make this a GitHub repo
(Sailgagag is authenticated in gh on the box — **creating/pushing a repo is a push, needs approval**; private repo works
when GitHub is connected to Render) → plan Free → env RAPIDAPI_PROXY_SECRET → `render.yaml` included.
