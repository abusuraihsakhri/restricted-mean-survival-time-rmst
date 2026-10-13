"""
FastAPI REST API Server for Restricted Mean Survival Time Rmst.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from rmst_calc import calculate_metrics
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Restricted Mean Survival Time Rmst API",
    description="Unadjusted Kaplan-Meier RMST analysis and legacy audit demonstration",
    version="3.1.0",
)


class ChatRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "restricted-mean-survival-time-rmst", "version": "3.1.0"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}


class SurvivalObservation(BaseModel):
    time: float
    event: int
    group: str = "All"


class RmstRequest(BaseModel):
    tau: float
    observations: List[SurvivalObservation] = Field(min_length=1, max_length=100000)


@app.post("/api/rmst")
def api_rmst(request: RmstRequest):
    """Statistical analysis; no patient identifiers or records are stored."""
    try:
        return calculate_metrics([row.model_dump() for row in request.observations], request.tau)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
