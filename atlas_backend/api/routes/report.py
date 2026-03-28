from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from core.session_report import generate_report

router = APIRouter()

@router.post("/report")
def export_report(payload: dict):
    state = payload.get("state", {})
    analytics = payload.get("analytics", {})
    staleness = payload.get("staleness", 0)

    report = generate_report(state, analytics, staleness_seconds=staleness)

    return PlainTextResponse(
        content=report,
        headers={"Content-Disposition": "attachment; filename=atlas_report.md"}
    )