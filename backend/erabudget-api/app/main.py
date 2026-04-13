"""ERABudget API — Budget microservice for ProjeX Suite (port 8200)."""

from fastapi import FastAPI

app = FastAPI(title="ERABudget API", version="0.1.0")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "erabudget-api"}
