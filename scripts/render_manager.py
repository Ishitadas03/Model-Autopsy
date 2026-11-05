"""Render API helper to manage Render services and environment variables."""
import json
import urllib.error
import urllib.request
from pathlib import Path
import yaml

CONFIG_PATH = Path(r"C:\Users\ishit\.render\cli.yaml")
SERVICE_ID = "srv-dbm8pql9fdbs73c652u0"


def get_token():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("api", {}).get("key")


def set_env_vars(env_dict):
    token = get_token()
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
        "MAX_CONCURRENT_EXPERIMENTS": "1",
        "EXPERIMENT_TIMEOUT_SECONDS": "1800",
        "CORS_ORIGINS": json.dumps(["https://model-autopsy-rose.vercel.app", "https://model-autopsy.vercel.app"]),
        "CORS_ORIGIN_REGEX": r"^https://.*\.vercel\.app$",
    }
    set_env_vars(env_vars)

