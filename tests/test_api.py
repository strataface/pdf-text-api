import json, pathlib, shutil, pytest
from conftest import sample
from app import settings, fetch
from app.main import app

def up(client, name, **form):
    return client.post("/v1/extract/upload", files={"file": (name, sample(name), "application/pdf")}, data=form)

def test_health(client):
    r = client.get("/health"); assert r.status_code == 200 and "chi_sim" in r.json()["ocrLanguages"]

def test_text_pdf_tables_csv(client):
    j = up(client, "text_table.pdf", tableFormat="csv").json()
    assert "Quarterly Report 2026" in j["text"] and j["ocrPages"] == 0
    assert j["tableCount"] == 1 and j["tables"][0]["csv"].startswith("Region,Q2,Q3\nNorth,120,135")
    assert "markdown" not in j["tables"][0] and "tables" not in j["pages"][0]

def test_both_formats(client):
    t = up(client, "text_table.pdf", tableFormat="both").json()["tables"][0]
    assert "csv" in t and t["markdown"].startswith("|")

def test_no_tables_key_by_default(client):
    assert "tables" not in up(client, "text_table.pdf").json()

@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract missing")
def test_scanned_ocr(client):
    j = up(client, "scanned.pdf").json()
    assert j["ocrPages"] == 1 and len(j["text"].strip()) > 20

@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract missing")
def test_chinese_ocr(client):
    j = up(client, "scanned_chi_sim.pdf", ocrLanguages="chi_sim+eng").json()
    assert "发票号码" in j["text"]

def test_ocr_never(client):
    j = up(client, "scanned.pdf", ocr="never").json()
    assert j["ocrPages"] == 0

def test_ocr_cap(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_OCR_PAGES", 0)
    j = up(client, "scanned.pdf").json()
    assert j["ocrPages"] == 0 and "OCR page cap" in j["pages"][0]["error"]

def test_bad_language(client):
    r = up(client, "text_table.pdf", ocrLanguages="eng+xx")
    assert r.status_code == 422 and "xx" in r.json()["detail"]

def test_not_pdf(client):
    assert up(client, "not_a_pdf.pdf").status_code == 415

def test_encrypted(client):
    r = up(client, "encrypted.pdf"); assert r.status_code == 401
    r = up(client, "encrypted.pdf", password="wrong-pw"); assert r.status_code == 401 and "wrong-pw" not in r.text
    assert up(client, "encrypted.pdf", password="secret").status_code == 200

def test_too_large(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_BYTES", 100)
    assert up(client, "text_table.pdf").status_code == 413

def test_max_pages_validation(client):
    assert up(client, "text_table.pdf", maxPages=str(settings.MAX_PAGES + 1)).status_code == 422

@pytest.mark.parametrize("url", ["http://127.0.0.1/a.pdf", "http://localhost/a.pdf", "http://10.0.0.5/x.pdf",
                                 "http://169.254.169.254/latest/meta-data", "http://[::1]/a.pdf",
                                 "http://192.168.1.1/a.pdf", "http://[::ffff:127.0.0.1]/a.pdf"])
def test_ssrf_blocked(client, url):
    r = client.post("/v1/extract", json={"url": url})
    assert r.status_code == 403, r.text

@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com/a.pdf", "http://u:p@example.com/a.pdf",
                                 "http://example.com:22/a.pdf"])
def test_bad_urls(client, url):
    assert client.post("/v1/extract", json={"url": url}).status_code in (400, 422)

def test_redirect_to_private_blocked(client, monkeypatch):
    import httpx
    def handler(req):
        return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
    real = httpx.AsyncClient
    monkeypatch.setattr(fetch.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    async def ok(url):
        if "127.0.0.1" in url: raise fetch.FetchError("private", 403)
        return url
    monkeypatch.setattr(fetch, "check_url", ok)
    r = client.post("/v1/extract", json={"url": "https://example.com/a.pdf"})
    assert r.status_code == 403

def test_url_mode_mocked(client, monkeypatch):
    import httpx
    body = sample("text_table.pdf")
    real = httpx.AsyncClient
    monkeypatch.setattr(fetch.httpx, "AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=body)), **kw))
    async def ok(url): return url
    monkeypatch.setattr(fetch, "check_url", ok)
    j = client.post("/v1/extract", json={"url": "https://example.com/a.pdf", "tableFormat": "csv"}).json()
    assert j["source"]["type"] == "url" and j["tableCount"] == 1

def test_ip_is_public():
    assert fetch.ip_is_public("8.8.8.8") and not fetch.ip_is_public("198.18.0.1") and not fetch.ip_is_public("100.64.0.1")

def test_proxy_secret(client, monkeypatch):
    monkeypatch.setenv("RAPIDAPI_PROXY_SECRET", "s3")
    assert up(client, "text_table.pdf").status_code == 403
    assert client.get("/health").status_code == 200 and client.get("/openapi.json").status_code == 200
    r = client.post("/v1/extract/upload", files={"file": ("a.pdf", sample("text_table.pdf"))}, headers={"X-RapidAPI-Proxy-Secret": "s3"})
    assert r.status_code == 200

def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_PER_MIN", 2)
    codes = [client.post("/v1/extract", json={"url": "file:///x"}).status_code for _ in range(3)]
    assert codes[-1] == 429 and client.get("/health").status_code == 200

def test_openapi_file_in_sync(client):
    f = pathlib.Path(__file__).parent.parent / "openapi.json"
    assert json.loads(f.read_text()) == client.get("/openapi.json").json()

def test_no_disk_writes(client, tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    up(client, "scanned.pdf"); up(client, "text_table.pdf", tableFormat="csv")
    assert list(tmp_path.iterdir()) == []

def test_license_note():
    t = (pathlib.Path(__file__).parent.parent / "LICENSES/THIRD_PARTY.md").read_text()
    assert "AGPL" in t and "FastAPI" in t
