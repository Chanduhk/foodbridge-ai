from app.schemas.health import HealthResponse
from app.schemas.user import (
    UserRegister,
    UserLogin,
    Token,
    TokenData,
    UserResponse,
    UserListResponse,
)
from app.schemas.donation import (
    DonationCreate,
    DonationUpdate,
    DonationResponse,
    DonationListResponse,
    EligibilityResult,
    EligibilityCheck,
)
from app.schemas.recipient import (
    RecipientProfileCreate,
    RecipientProfileUpdate,
    RecipientProfileResponse,
    RecipientDemandCreate,
    RecipientDemandUpdate,
    RecipientDemandResponse,
    MatchResult,
    MatchListResponse,
)
from app.schemas.allocation import (
    AllocationCreate,
    AllocationResponse,
)
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryUpdate,
    DeliveryResponse,
    LogisticsRecommendation
)
from app.schemas.ml import (
    DemandForecastRequest,
    DemandForecastResponse,
    AnalyticsResponse
)

__all__ = [
    "HealthResponse",
    "UserRegister",
    "UserLogin",
    "Token",
    "TokenData",
    "UserResponse",
    "UserListResponse",
    "DonationCreate",
    "DonationUpdate",
    "DonationResponse",
    "DonationListResponse",
    "EligibilityResult",
    "EligibilityCheck",
    "RecipientProfileCreate",
    "RecipientProfileUpdate",
    "RecipientProfileResponse",
    "RecipientDemandCreate",
    "RecipientDemandUpdate",
    "RecipientDemandResponse",
    "MatchResult",
    "MatchListResponse",
    "AllocationCreate",
    "AllocationResponse",
    "DeliveryCreate",
    "DeliveryUpdate",
    "DeliveryResponse",
    "LogisticsRecommendation",
    "DemandForecastRequest",
    "DemandForecastResponse",
    "AnalyticsResponse",
]
