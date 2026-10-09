import math
from typing import List, Tuple
from datetime import datetime, timezone

from app.models.donation import Donation, DonationStatus
from app.models.recipient import RecipientProfile, RecipientDemand, DemandStatus
from app.models.user import User
from app.schemas.recipient import MatchResult

class MatchingAgent:
    """
    Intelligent Recipient Matching Agent.
    A rule-based, two-stage explainable decision-support component.
    """
    
    def __init__(self):
        # Initial configurable design parameters
        self.weights = {
            "distance": 0.30,
            "capacity_fit": 0.25,
            "compatibility": 0.20,
            "reliability": 0.15,
            "urgency": 0.10
        }

    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on the earth."""
        if None in (lat1, lon1, lat2, lon2):
            return 10.0 # fallback default distance
            
        R = 6371 # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def match(self, donation: Donation, profiles: List[RecipientProfile], demands: List[RecipientDemand]) -> List[MatchResult]:
        """
        Execute two-stage matching logic.
        Stage 1: Hard constraint filtering
        Stage 2: Explainable weighted ranking
        """
        now = datetime.now(timezone.utc)
        available_kg = donation.quantity_kg - donation.allocated_kg
        
        # --- Pre-computation Stage 1: Donation-Level Constraints ---
        if donation.status != DonationStatus.ELIGIBLE:
            return [] # Donation not eligible
            
        donation_expires_at = donation.expires_at
        if donation_expires_at.tzinfo is None:
            donation_expires_at = donation_expires_at.replace(tzinfo=timezone.utc)
            
        if donation_expires_at <= now:
            return [] # Donation expired
            
        if available_kg <= 0:
            return [] # Fully allocated
            
        feasible_candidates: List[Tuple[RecipientProfile, Optional[RecipientDemand], float]] = []
        
        # Group demands by recipient
        demands_by_recipient = {}
        for d in demands:
            if d.status == DemandStatus.OPEN or d.status == DemandStatus.PARTIALLY_FULFILLED:
                if d.recipient_id not in demands_by_recipient:
                    demands_by_recipient[d.recipient_id] = []
                demands_by_recipient[d.recipient_id].append(d)

        # --- Stage 1: Hard Constraint Filtering ---
        for profile in profiles:
            user = profile.user
            
            # Recipient verification & activity
            if not profile.is_verified:
                continue
            if not user.is_active:
                continue
                
            # Capacity constraints
            available_capacity = profile.capacity_kg - profile.current_occupancy_kg
            if available_capacity <= 0:
                continue
                
            # Food Category compatibility (if profile has strict list)
            if profile.food_categories_accepted:
                # Simple loose matching for this stage
                categories_lower = [c.lower() for c in profile.food_categories_accepted]
                if donation.food_type.lower() not in categories_lower:
                    continue
                    
            # Check demand compatibility if required.
            # We look for the most relevant demand
            recipient_demands = demands_by_recipient.get(profile.id, [])
            best_demand = None
            if recipient_demands:
                # Find demand matching category loosely
                for d in recipient_demands:
                    if d.food_category.lower() in donation.food_type.lower() or donation.food_type.lower() in d.food_category.lower():
                        best_demand = d
                        break
                        
                # If no matching demand and demands exist, skip or proceed with lower score?
                # The prompt says: "recipient demand is not compatible where demand is required"
                # If they have demands but none match, we might skip. But if they have NO demands, we assume they can accept if capacity allows.
                if not best_demand:
                    continue
            
            # Determine max they can take
            max_can_take = available_capacity
            if best_demand:
                demand_remaining = best_demand.quantity_requested
                max_can_take = min(available_capacity, demand_remaining)
                
            if max_can_take <= 0:
                continue
                
            recommended_kg = min(available_kg, max_can_take)
            
            feasible_candidates.append((profile, best_demand, recommended_kg))
            
        # --- Stage 2: Explainable Weighted Ranking ---
        results = []
        
        for profile, demand, rec_kg in feasible_candidates:
            user = profile.user
            
            # 1. Distance (Normalize assuming max reasonable distance is 50km)
            dist_km = self.haversine_distance(donation.latitude, donation.longitude, user.latitude, user.longitude)
            dist_score = max(0.0, (50.0 - dist_km) / 50.0) # 1.0 if 0km, 0.0 if >= 50km
            
            # 2. Capacity Fit
            # How much of the donation can they take?
            cap_score = rec_kg / available_kg
            
            # 3. Compatibility (Food/Dietary)
            # If demand matched, high compatibility.
            comp_score = 1.0 if demand else 0.5
            
            # 4. Historical Reliability
            # No data yet, default to 0.8
            rel_score = 0.80
            
            # 5. Urgency
            urg_score = 0.5
            if demand:
                # Higher priority = higher score (priority 1-5 where 5 is high)
                urg_score = demand.priority / 5.0
                
            final_score = (
                dist_score * self.weights["distance"] +
                cap_score * self.weights["capacity_fit"] +
                comp_score * self.weights["compatibility"] +
                rel_score * self.weights["reliability"] +
                urg_score * self.weights["urgency"]
            )
            
            warnings = []
            if dist_km > 30:
                warnings.append("Recipient is further than 30km away.")
            if rec_kg < available_kg:
                warnings.append(f"Recipient can only accept {rec_kg}kg out of {available_kg}kg available.")
                
            explanation = (
                f"Match score {final_score:.2f} based on distance ({dist_km:.1f}km), "
                f"capacity fit ({rec_kg}kg), and urgency."
            )
            
            results.append(MatchResult(
                recipient_id=profile.id,
                match_score=round(final_score, 4),
                factor_scores={
                    "distance": round(dist_score, 4),
                    "capacity_fit": round(cap_score, 4),
                    "compatibility": round(comp_score, 4),
                    "reliability": round(rel_score, 4),
                    "urgency": round(urg_score, 4)
                },
                recommended_quantity_kg=rec_kg,
                explanation=explanation,
                warnings=warnings
            ))
            
        # Sort descending by match_score
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

matching_agent = MatchingAgent()
