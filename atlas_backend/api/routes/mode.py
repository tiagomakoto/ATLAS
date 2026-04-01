from fastapi import APIRouter, HTTPException
from atlas_backend.core.runtime_mode import set_mode, get_mode
from atlas_backend.core.audit_logger import log_action

router = APIRouter()

@router.get("/mode")
def read_mode():
    return {"mode": get_mode()}

@router.post("/mode")
def update_mode(payload: dict):
    mode = payload.get("mode")

    if not mode:
        raise HTTPException(
            status_code=400,
            detail={"error": "MODE_REQUIRED", "accepted": ["observe", "live"]}
        )

    try:
        result = set_mode(mode)

        log_action(
            action="mode_change",
            payload={"mode": mode},
            response={"status": "OK", "mode": result}
        )

        return {"mode": result}

    except ValueError as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})