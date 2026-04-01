from fastapi import APIRouter
from atlas_backend.core.module_registry import get_all_modules

router = APIRouter()

@router.get("/modules/status")
def modules_status():
    return get_all_modules()