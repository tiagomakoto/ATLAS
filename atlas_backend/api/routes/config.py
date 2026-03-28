from fastapi import APIRouter, HTTPException
from core.config_manager import load_config, update_config

# NOTA: o backend não verifica se o diff foi exibido ao operador.
# O frontend DEVE enforçar o fluxo: diff → confirmar → salvar.
# Limitação conhecida e documentada.

router = APIRouter()

@router.post("/config/update")
def update(payload: dict):
    description = payload.get("description", "").strip()
    data = payload.get("data")
    confirm = payload.get("confirm", False)

    if not description:
        raise HTTPException(
            status_code=400,
            detail={"error": "DESCRIPTION_REQUIRED"}
        )

    # 🔴 PROTEÇÃO — exige confirmação explícita
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "CONFIRMATION_REQUIRED",
                "message": "Envie confirm=true para aplicar alteração"
            }
        )

    version = update_config(data, description)

    return {
        "status": "OK",
        "version": version["version_id"]
    }