"""Limits sized for free hosting tiers (512 MB RAM, shared CPU). All overridable by env."""
import os

def _i(name, default):
    return int(os.environ.get(name, default))

VERSION = "0.1.0"
MAX_BYTES = _i("PDFTEXT_MAX_MB", 10) * 1024 * 1024
MAX_PAGES = _i("PDFTEXT_MAX_PAGES", 20)
MAX_OCR_PAGES = _i("PDFTEXT_MAX_OCR_PAGES", 5)
TIME_BUDGET_S = _i("PDFTEXT_TIME_BUDGET_S", 60)      # extraction budget per request
DOWNLOAD_TIMEOUT_S = _i("PDFTEXT_DOWNLOAD_TIMEOUT_S", 20)
MAX_REDIRECTS = 3
CONCURRENCY = _i("PDFTEXT_CONCURRENCY", 2)            # parallel extractions (memory guard)
RATE_PER_MIN = _i("PDFTEXT_RATE_PER_MIN", 20)         # per client; 0 disables
TRUST_PROXY = os.environ.get("PDFTEXT_TRUST_PROXY", "0") == "1"   # use first X-Forwarded-For hop
# Extra CIDRs allowed despite being non-public (testing only, e.g. a sandbox with fake DNS).
ALLOW_CIDRS = [c for c in os.environ.get("PDFTEXT_ALLOW_CIDRS", "").split(",") if c.strip()]
USER_AGENT = f"pdf-text-api/{VERSION}"
