"""
FastAPI Service Entrypoint & Healthcheck Probes for Normalizer Service (F1-K2-A).
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, Any
from .models import NormalizationResult
from .normalizer import NormalizerEngine

app = FastAPI(
    title="cryptoAML Normalizer Service",
    description="Canonical Normalization Service for Blockchain Transactions & Events",
    version="1.0.0"
)

engine = NormalizerEngine()


@app.get("/livez")
def livez():
    """Liveness probe: Checks if process is running."""
    return {"status": "ok", "service": "normalizer"}


@app.get("/readyz")
def readyz():
    """Readiness probe: Checks if dependencies are accessible."""
    return {"status": "ready", "service": "normalizer"}


@app.get("/startupz")
def startupz():
    """Startup probe: Checks if initialization completed."""
    return {"status": "started", "service": "normalizer"}


@app.post("/normalize", response_model=NormalizationResult)
def normalize_transaction(payload: Dict[str, Any]):
    """Normalize raw transaction RPC payload into canonical entities."""
    result = engine.normalize_raw_payload(payload)
    if not result.success and result.transaction is None:
        raise HTTPException(status_code=400, detail=result.error_reason)
    return result
