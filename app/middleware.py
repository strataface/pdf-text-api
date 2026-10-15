"""RapidAPI proxy-secret gate (no-op when RAPIDAPI_PROXY_SECRET unset) + simple per-client rate limit."""
import hmac, os, time
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from . import settings

EXEMPT = {"/health", "/docs", "/openapi.json", "/redoc"}


def _exempt(request):
    return (request.url.path.rstrip("/") or "/") in EXEMPT


class ProxySecretMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        secret = os.environ.get("RAPIDAPI_PROXY_SECRET") or ""
        if secret and not _exempt(request):
            got = request.headers.get("x-rapidapi-proxy-secret", "")
            if not hmac.compare_digest(got.encode(), secret.encode()):
                return JSONResponse(status_code=403, content={"error": "forbidden",
                                    "detail": "invalid or missing X-RapidAPI-Proxy-Secret"})
        return await call_next(request)


def client_key(request):
    user = request.headers.get("x-rapidapi-user")
    if user and os.environ.get("RAPIDAPI_PROXY_SECRET"):   # only trusted behind the verified proxy
        return "rapid:" + user
    if settings.TRUST_PROXY:
        xff = request.headers.get("x-forwarded-for", "")
        if xff:
            return "ip:" + xff.split(",")[0].strip()
    return "ip:" + (request.client.host if request.client else "?")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding 60 s window, in-memory (per instance). Good enough for a single free-tier instance."""
    def __init__(self, app):
        super().__init__(app)
        self.hits = defaultdict(deque)

    async def dispatch(self, request, call_next):
        limit = settings.RATE_PER_MIN
        if limit <= 0 or _exempt(request):
            return await call_next(request)
        now = time.monotonic()
        q = self.hits[client_key(request)]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= limit:
            retry = int(60 - (now - q[0])) + 1
            return JSONResponse(status_code=429, headers={"Retry-After": str(retry)},
                                content={"error": "rate_limited", "detail": f"max {limit} requests per minute"})
        q.append(now)
        if len(self.hits) > 10000:   # bound memory
            for k in [k for k, v in self.hits.items() if not v or now - v[-1] > 60]:
                del self.hits[k]
        return await call_next(request)
