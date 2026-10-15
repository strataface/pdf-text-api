import pathlib, pytest
from fastapi.testclient import TestClient
SAMPLES = pathlib.Path(__file__).parent / "samples"

@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("RAPIDAPI_PROXY_SECRET", raising=False)
    from app import main, settings
    monkeypatch.setattr(settings, "RATE_PER_MIN", 1000)
    return TestClient(main.app)

def sample(name):
    return (SAMPLES / name).read_bytes()
