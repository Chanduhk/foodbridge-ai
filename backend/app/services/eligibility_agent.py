from datetime import datetime, timezone
from app.models.donation import Donation, DonationStatus
from app.schemas.donation import EligibilityResult, EligibilityCheck

class EligibilityAgent:
    """
    Food Eligibility and Safety Screening Agent.
    
    IMPORTANT: This is a RULE-BASED DECISION-SUPPORT COMPONENT.
    It does NOT certify food as safe for consumption, nor does it invent
    food-safety time limits, temperature thresholds, or override mandatory
    backend validation rules.
    """

    def __init__(self):
        # In a real app, these could be loaded from settings or database
        self.rules = [
            self._check_quantity_positive,
            self._check_not_expired,
            self._check_description_provided,
            self._check_address_provided,
        ]

    def evaluate(self, donation: Donation) -> EligibilityResult:
        """
        Evaluate the donation against configured project eligibility rules.
        """
        checks = []
        is_rejected = False
        requires_review = False
        
        for rule in self.rules:
            check = rule(donation)
            checks.append(check)
            if not check.passed:
                # If it's a hard failure, we might reject.
                # If it's just uncertain or missing something soft, we might require review.
                # For this implementation, expiration and quantity <= 0 are hard rejections.
                # Missing descriptions/info are review_required.
                if check.rule in ["quantity_positive", "not_expired"]:
                    is_rejected = True
                else:
                    requires_review = True
                    
        if is_rejected:
            status = DonationStatus.REJECTED
            eligible = False
        elif requires_review:
            status = DonationStatus.REVIEW_REQUIRED
            eligible = None
        else:
            status = DonationStatus.ELIGIBLE
            eligible = True
            
        return EligibilityResult(
            eligible=eligible,
            status=status,
            checks=checks,
            requires_human_review=requires_review
        )

    def _check_quantity_positive(self, donation: Donation) -> EligibilityCheck:
        passed = donation.quantity_kg > 0
        return EligibilityCheck(
            rule="quantity_positive",
            passed=passed,
            reason="Quantity must be greater than zero." if not passed else "Quantity is valid."
        )

    def _check_not_expired(self, donation: Donation) -> EligibilityCheck:
        # SQLite drops timezone info, so ensure expires_at is timezone aware
        now = datetime.now(timezone.utc)
        expires_at = donation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        passed = expires_at > now
        return EligibilityCheck(
            rule="not_expired",
            passed=passed,
            reason="The stated deadline has passed." if not passed else "Deadline is in the future."
        )

    def _check_description_provided(self, donation: Donation) -> EligibilityCheck:
        passed = bool(donation.description and len(donation.description.strip()) > 5)
        return EligibilityCheck(
            rule="description_provided",
            passed=passed,
            reason="Description is missing or too short. Needs manual review." if not passed else "Description provided."
        )

    def _check_address_provided(self, donation: Donation) -> EligibilityCheck:
        passed = bool(donation.pickup_address and len(donation.pickup_address.strip()) > 5)
        return EligibilityCheck(
            rule="address_provided",
            passed=passed,
            reason="Pickup address is missing or too short." if not passed else "Pickup address provided."
        )

# Singleton instance for dependency injection if needed
eligibility_agent = EligibilityAgent()
