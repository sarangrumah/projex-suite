"""AppCatalog API — Documentation pipeline microservice for ProjeX Suite (port 8300)."""

from fastapi import FastAPI

app = FastAPI(title="AppCatalog API", version="0.1.0")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "appcatalog-api"}
