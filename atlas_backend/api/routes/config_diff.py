from fastapi import APIRouter
from atlas_backend.core.config_manager import load_config
from atlas_backend.core.config_diff import compute_diff

router = APIRouter()

@router.post("/config/diff")
def diff(payload: dict):
    current = load_config()
    new_data = payload.get("data")

    return compute_diff(current, new_data)