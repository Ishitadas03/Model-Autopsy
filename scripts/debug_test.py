import sys
sys.path.insert(0, ".")
import asyncio
import traceback
from httpx import ASGITransport, AsyncClient
from backend.app.main import app

async def main():
    print("Testing /api/experiments/e003 directly with AsyncClient...")
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            print("Sending GET /api/experiments/e003...")
            resp = await asyncio.wait_for(ac.get("/api/experiments/e003"), timeout=5.0)
            print("Status:", resp.status_code)
            print("Body keys:", list(resp.json().keys()) if resp.status_code == 200 else resp.text[:200])
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
