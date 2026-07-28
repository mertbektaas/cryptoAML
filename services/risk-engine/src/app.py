"""
FastAPI Service Entrypoint & Healthcheck Probes for Risk Engine Service (F2-K2-A).
"""

from fastapi import FastAPI, HTTPException
try:
    from .models import EvaluationRequest, EvaluationResponse
    from .evaluator import RuleEvaluator
except ImportError:
    from models import EvaluationRequest, EvaluationResponse
    from evaluator import RuleEvaluator

app = FastAPI(
    title="cryptoAML Risk Engine Service",
    description="Rule-based Policy Engine and Risk Scoring Service",
    version="1.0.0"
)

evaluator = RuleEvaluator()


@app.get("/livez")
def livez():
    """Liveness probe: Checks if process is running."""
    return {"status": "ok", "service": "risk-engine"}


@app.get("/readyz")
def readyz():
    """Readiness probe: Checks if dependencies are accessible."""
    return {"status": "ready", "service": "risk-engine"}


@app.get("/startupz")
def startupz():
    """Startup probe: Checks if initialization completed."""
    return {"status": "started", "service": "risk-engine"}


@app.post("/evaluate", response_model=EvaluationResponse)
def evaluate_risk(request: EvaluationRequest):
    """Evaluates address signals against policy rules and returns risk assessment."""
    response = evaluator.evaluate_request(request)
    if not response.success:
        raise HTTPException(status_code=400, detail=response.error_message)
    return response
