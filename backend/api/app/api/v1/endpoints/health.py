from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get(
    "",
    summary="Health check básico",
    description="Verifica que la API esté funcionando"
)
async def health_check():
    """Health check simple sin dependencias externas"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get(
    "/ready",
    summary="Readiness check",
    description="Verifica conectividad con dependencias (DB)"
)
async def readiness_check(db: Annotated[Session, Depends(get_db)]):
    """
    Verifica que todas las dependencias estén disponibles.
    
    Útil para orchestrators (Kubernetes) que necesitan saber
    si la app está lista para recibir tráfico.
    """
    checks = {
        "api": "ok",
        "database": "down"
    }
    
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
    
    if any(v != "ok" for v in checks.values()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=checks
        )
    
    return checks
