"""Update Render service build and start commands safely."""
import json
import urllib.request
import urllib.error
from pathlib import Path
import yaml

CONFIG_PATH = Path(r"C:\Users\ishit\.render\cli.yaml")
SERVICE_ID = "srv-dbm8pql9fdbs73c652u0"

def update_service():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    token = cfg.get("api", {}).get("key")

    payload = {
        "serviceDetails": {
            "envSpecificDetails": {
                "buildCommand": "pip install --upgrade pip setuptools wheel && pip install -r backend/requirements-prod.txt",
                "startCommand": "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
            }
        }
    }

    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SERVICE_ID}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="PATCH"
    )

    with urllib.request.urlopen(req) as resp:
        print("Updated status:", resp.status)
        svc = json.loads(resp.read().decode())
        details = svc.get("serviceDetails", {}).get("envSpecificDetails", {})
        print("Build Command:", details.get("buildCommand"))
        print("Start Command:", details.get("startCommand"))

if __name__ == "__main__":
    update_service()

