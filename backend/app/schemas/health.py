from typing import Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    project: str
    environment: str
    database: str
    details: Dict[str, Any]
