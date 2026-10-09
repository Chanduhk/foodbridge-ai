from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """Check health of the API server and database connection."""
    db_status = "connected"
    error_msg = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "error"
        error_msg = str(e)

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        database=db_status,
        details={
            "debug": settings.DEBUG,
            "error": error_msg
        }
    )
