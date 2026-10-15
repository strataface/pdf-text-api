"""Fetch exactly the user-given URL (plus up to 3 redirects), with SSRF guards and a size cap.
Nothing is written to disk; the body is held in memory only."""
import asyncio, ipaddress, socket
from urllib.parse import urlsplit, urljoin
import httpx
from . import settings


class FetchError(Exception):
    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


def _allowed_extra(ip):
    return any(ip in ipaddress.ip_network(c.strip(), strict=False) for c in settings.ALLOW_CIDRS)


def ip_is_public(ip):
    ip = ipaddress.ip_address(ip)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if _allowed_extra(ip):
        return True
    return ip.is_global and not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                                 or ip.is_reserved or ip.is_unspecified)


async def check_url(url):
    try:
        u = urlsplit(url)
    except ValueError:
        raise FetchError("invalid URL")
    if u.scheme not in ("http", "https") or not u.hostname:
        raise FetchError("only absolute http(s) URLs are accepted")
    if u.username or u.password:
        raise FetchError("credentials in URL are not allowed")
    if u.port not in (None, 80, 443, 8080, 8443):
        raise FetchError("port not allowed")
    host = u.hostname
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, u.port or (443 if u.scheme == "https" else 80),
                                                              type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchError("host could not be resolved")
    ips = {i[4][0] for i in infos}
    bad = [ip for ip in ips if not ip_is_public(ip)]
    if not ips or bad:
        raise FetchError("URL resolves to a private, loopback or otherwise non-public address", 403)
    return url


async def fetch_pdf(url):
    async with httpx.AsyncClient(follow_redirects=False, timeout=settings.DOWNLOAD_TIMEOUT_S,
                                 headers={"User-Agent": settings.USER_AGENT, "Accept": "application/pdf,*/*"}) as c:
        for _ in range(settings.MAX_REDIRECTS + 1):
            await check_url(url)
            try:
                async with c.stream("GET", url) as r:
                    if r.status_code in (301, 302, 303, 307, 308) and "location" in r.headers:
                        url = urljoin(url, r.headers["location"])
                        continue
                    if r.status_code != 200:
                        raise FetchError(f"remote server returned HTTP {r.status_code}", 502)
                    cl = r.headers.get("content-length")
                    if cl and cl.isdigit() and int(cl) > settings.MAX_BYTES:
                        raise FetchError(f"file larger than {settings.MAX_BYTES // 2**20} MB limit", 413)
                    buf = bytearray()
                    async for chunk in r.aiter_bytes():
                        buf += chunk
                        if len(buf) > settings.MAX_BYTES:
                            raise FetchError(f"file larger than {settings.MAX_BYTES // 2**20} MB limit", 413)
                    return bytes(buf)
            except httpx.TimeoutException:
                raise FetchError("download timed out", 504)
            except httpx.HTTPError as e:
                raise FetchError(f"download failed: {type(e).__name__}", 502)
        raise FetchError("too many redirects", 502)
