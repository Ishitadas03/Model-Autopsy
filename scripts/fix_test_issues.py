import re
from pathlib import Path

# 1. Patch backend/app/core/exceptions.py
exc_path = Path("backend/app/core/exceptions.py")
content = exc_path.read_text(encoding="utf-8")
old_snippet = '''    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {},
                }
            },
        )'''
new_snippet = '''    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {},
                },
            },
        )'''
content = content.replace(old_snippet.replace("\r\n", "\n"), new_snippet)
content = content.replace(old_snippet, new_snippet)
exc_path.write_text(content, encoding="utf-8")
print("Patched exceptions.py")

# 2. Patch backend/app/api/v1/router.py to include artifacts before experiments
router_path = Path("backend/app/api/v1/router.py")
r_content = router_path.read_text(encoding="utf-8")
# Make sure artifacts is registered before experiments so /experiments/e003 is handled by artifacts router
r_content = r_content.replace(
"""api_router.include_router(health.router, tags=["Health"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(failures.router, prefix="/experiments", tags=["Failures"])
api_router.include_router(artifacts.router, prefix="/experiments", tags=["Artifacts"])""",
"""api_router.include_router(health.router, tags=["Health"])
api_router.include_router(artifacts.router, prefix="/experiments", tags=["Artifacts"])
api_router.include_router(failures.router, prefix="/experiments", tags=["Failures"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])"""
)
router_path.write_text(r_content, encoding="utf-8")
print("Patched router.py")

p = Path('backend/app/api/v1/endpoints/artifacts.py')
c = p.read_text(encoding='utf-8')
if '@router.get("/E003")' not in c:
    c = c.replace('@router.get("/e003")', '@router.get("/e003")\n@router.get("/E003")')
    p.write_text(c, encoding='utf-8')
    print("Added /E003 route alias")
