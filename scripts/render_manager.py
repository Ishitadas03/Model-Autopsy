"""Render API helper to manage Render services and environment variables."""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import yaml

SERVICE_ID = os.environ.get("RENDER_SERVICE_ID", "srv-dbm8pql9fdbs73c652u0")


def get_token():
    token = os.environ.get("RENDER_API_KEY")
    if token:
        return token
    config_path = Path.home() / ".render" / "cli.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("api", {}).get("key")
    return None


def set_env_vars(env_dict):
    token = get_token()
    if not token:
        print("Error: Render API token not found via RENDER_API_KEY or ~/.render/cli.yaml")
        return
    payload = [{"key": k, "value": v} for k, v in env_dict.items()]
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("Status:", resp.status)
            res = json.loads(resp.read().decode())
            print(f"Successfully configured {len(res)} environment variables on Render!")
            for item in res:
                # Safe printing of keys without exposing sensitive values
                k = item.get("envVar", {}).get("key")
                print(f" - {k}: set")
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code, e.read().decode())


if __name__ == "__main__":
    env_vars = {
        "PYTHON_VERSION": "3.11.9",
        "APP_NAME": "Model Autopsy API",
        "APP_VERSION": "0.1.0",
        "DEBUG": "false",
        "LOG_LEVEL": "INFO",
    }
    set_env_vars(env_vars)
