"""WA-Hub Gateway — WhatsApp integration microservice for ProjeX Suite (port 8500)."""

from fastapi import FastAPI

app = FastAPI(title="WA-Hub Gateway", version="0.1.0")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "wahub-gateway"}
