"""ERA AI API — AI microservice for ProjeX Suite (port 8100)."""

from fastapi import FastAPI

app = FastAPI(title="ERA AI API", version="0.1.0")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "era-ai-api"}
