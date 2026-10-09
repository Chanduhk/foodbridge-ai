import math
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.allocation import Allocation, AllocationStatus
from app.models.donation import Donation
from app.models.recipient import RecipientProfile
from app.models.user import User, UserRole
from app.schemas.delivery import LogisticsRecommendation

class LogisticsCoordinationAgent:
    """
    Logistics Coordination Agent.
    A decision-support component that evaluates logistics feasibility 
    and recommends suitable pickup arrangements.
    DOES NOT bypass backend authorization or state validation.
    """

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate geographic (straight-line) distance between two points in km."""
        if None in (lat1, lon1, lat2, lon2):
            return 10.0 # fallback
        R = 6371
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def evaluate_feasibility(self, db: Session, allocation: Allocation) -> LogisticsRecommendation:
        """
        Evaluate and recommend a logistics plan for an accepted allocation.
        """
        donation = allocation.donation
        recipient_user = allocation.recipient.user

        # 1. Geographic distance
        dist_km = self.haversine_distance(
            donation.latitude, donation.longitude,
            recipient_user.latitude, recipient_user.longitude
        )

        # 2. Estimate duration (assume 30km/h average urban straight line equivalent speed)
        estimated_duration_min = int((dist_km / 30.0) * 60) + 15 # 15 mins for pickup/dropoff buffer

        # 3. Find available active volunteers (simplified recommendation logic)
        volunteers = db.query(User).filter(
            User.role == UserRole.VOLUNTEER,
            User.is_active == True
        ).all()

        recommended_volunteers = []
        for v in volunteers:
            # We could factor in volunteer location here if they had one consistently
            # For MVP, we recommend all active volunteers, sorted by some heuristic if we had it.
            recommended_volunteers.append(v.id)

        notes = f"Estimated geographic distance: {dist_km:.1f}km. Required vehicle: {'Yes' if donation.requires_vehicle else 'No'}."
        if donation.storage_type.value != "ambient":
            notes += " Requires temperature control."

        return LogisticsRecommendation(
            allocation_id=allocation.id,
            recommended_volunteer_ids=recommended_volunteers,
            distance_km=round(dist_km, 2),
            estimated_duration_min=estimated_duration_min,
            recommendation_notes=notes
        )

logistics_agent = LogisticsCoordinationAgent()
