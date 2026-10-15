import json
from app.main import app
open("openapi.json", "w").write(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n")
