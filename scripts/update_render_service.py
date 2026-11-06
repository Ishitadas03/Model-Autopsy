"""Update Render service build and start commands safely."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import yaml

SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "srv-dbm8pql9fdbs73c652u0")


def update_service():
    token = os.environ.get("RENDER_API_KEY")
    if not token:
        config_path = Path.home() / ".render" / "cli.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            token = cfg.get("api", {}).get("key")

    if not token:
        print("Error: Render API token not found via RENDER_API_KEY or ~/.render/cli.yaml")
        return

    payload = {
        "serviceDetails": {
            "envSpecificDetails": {
                "buildCommand": "pip install --upgrade pip setuptools wheel && pip install -r backend/requirements-prod.txt",
                "startCommand": "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT",
            }
        }
    }

    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SERVICE_ID}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print("Updated status:", resp.status)
            svc = json.loads(resp.read().decode())
            details = svc.get("serviceDetails", {}).get("envSpecificDetails", {})
            print("Build Command:", details.get("buildCommand"))
            print("Start Command:", details.get("startCommand"))
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode())


if __name__ == "__main__":
    update_service()
