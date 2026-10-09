from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.recipient import RecipientProfile, RecipientDemand, OrgType, DemandStatus
from app.models.donation import Donation, DonorType, StorageType, DonationStatus
from app.models.allocation import Allocation, AllocationStatus
from app.models.delivery import Delivery, DeliveryStatus
from app.models.notification import Notification, NotificationChannel
from app.models.audit import AuditLog


def test_user_creation_and_roles(db_session: Session):
    """Test user model creation with various roles and verification flags."""
    donor = User(
        email="donor@example.org",
        hashed_password="hashed_pw_test",
        full_name="Alice Chef",
        role=UserRole.DONOR,
        phone="+1234567890",
        latitude=40.7128,
        longitude=-74.0060,
        address="123 Bakery Lane"
    )
    db_session.add(donor)
    db_session.commit()

    retrieved = db_session.query(User).filter_by(email="donor@example.org").first()
    assert retrieved is not None
    assert retrieved.role == UserRole.DONOR
    assert retrieved.is_active is True
    assert retrieved.is_verified is False
    assert retrieved.full_name == "Alice Chef"


def test_recipient_profile_and_demand_relationship(db_session: Session):
    """Test RecipientProfile and RecipientDemand relation with demand tracking."""
    user = User(
        email="shelter@example.org",
        hashed_password="hashed_pw_test",
        full_name="Community Shelter Admin",
        role=UserRole.RECIPIENT,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    profile = RecipientProfile(
        user_id=user.id,
        organization_name="Downtown Community Shelter",
        organization_type=OrgType.SHELTER,
        license_number="LIC-12345",
        is_verified=True,
        capacity_kg=250.0,
        current_occupancy_kg=50.0,
        food_categories_accepted=["prepared", "bakery", "dairy"],
        operating_hours="08:00 - 20:00"
    )
    db_session.add(profile)
    db_session.commit()

    # Create demand record for this recipient
    demand = RecipientDemand(
        recipient_id=profile.id,
        food_category="prepared",
        quantity_requested=40.0,
        unit="kg",
        priority=2,
        needed_by=datetime.now(timezone.utc) + timedelta(hours=6),
        status=DemandStatus.OPEN,
        dietary_requirements="Nut-free"
    )
    db_session.add(demand)
    db_session.commit()

    retrieved_profile = db_session.query(RecipientProfile).filter_by(id=profile.id).first()
    assert retrieved_profile is not None
    assert len(retrieved_profile.demands) == 1
    assert retrieved_profile.demands[0].quantity_requested == 40.0
    assert retrieved_profile.demands[0].status == DemandStatus.OPEN


def test_donation_with_donor_type_and_allocation(db_session: Session):
    """Test Donation creation with specific donor_type and partial Allocation."""
    # Create donor user
    donor = User(
        email="restaurant@example.org",
        hashed_password="hashed_pw_test",
        full_name="Chef Mario",
        role=UserRole.DONOR
    )
    # Create recipient user
    recipient_user = User(
        email="foodbank@example.org",
        hashed_password="hashed_pw_test",
        full_name="Metro Food Bank",
        role=UserRole.RECIPIENT,
        is_verified=True
    )
    db_session.add_all([donor, recipient_user])
    db_session.commit()

    recipient_prof = RecipientProfile(
        user_id=recipient_user.id,
        organization_name="Metro Food Bank Org",
        organization_type=OrgType.FOOD_BANK,
        is_verified=True,
        capacity_kg=1000.0,
        food_categories_accepted=["prepared", "packaged"]
    )
    db_session.add(recipient_prof)
    db_session.commit()

    # Create donation with donor_type = RESTAURANT
    donation = Donation(
        donor_id=donor.id,
        donor_type=DonorType.RESTAURANT,
        food_type="prepared",
        description="50 boxes of cooked vegetable pasta",
        quantity_kg=50.0,
        allocated_kg=25.0,
        prepared_at=datetime.now(timezone.utc) - timedelta(hours=2),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=10),
        storage_type=StorageType.AMBIENT,
        requires_vehicle=True,
        latitude=40.7306,
        longitude=-73.9352,
        pickup_address="45 Broadway St",
        status=DonationStatus.ELIGIBLE,
        eligibility_result={"eligible": True, "checks": [{"rule": "expiry", "passed": True}]}
    )
    db_session.add(donation)
    db_session.commit()

    # Create allocation of 25kg
    allocation = Allocation(
        donation_id=donation.id,
        recipient_id=recipient_prof.id,
        quantity_kg=25.0,
        match_score=0.92,
        score_explanation={"distance_score": 0.95, "capacity_score": 0.90},
        status=AllocationStatus.PROPOSED
    )
    db_session.add(allocation)
    db_session.commit()

    retrieved_donation = db_session.query(Donation).filter_by(id=donation.id).first()
    assert retrieved_donation is not None
    assert retrieved_donation.donor_type == DonorType.RESTAURANT
    assert retrieved_donation.quantity_kg == 50.0
    assert len(retrieved_donation.allocations) == 1
    assert retrieved_donation.allocations[0].quantity_kg == 25.0
    assert retrieved_donation.allocations[0].match_score == 0.92


def test_delivery_workflow_and_volunteer(db_session: Session):
    """Test Delivery tracking linked to Allocation and volunteer."""
    donor = User(email="d1@ex.org", hashed_password="pw", full_name="Donor 1", role=UserRole.DONOR)
    rec_user = User(email="r1@ex.org", hashed_password="pw", full_name="Rec 1", role=UserRole.RECIPIENT)
    volunteer = User(email="v1@ex.org", hashed_password="pw", full_name="Vol 1", role=UserRole.VOLUNTEER)
    db_session.add_all([donor, rec_user, volunteer])
    db_session.commit()

    rec_prof = RecipientProfile(
        user_id=rec_user.id,
        organization_name="Shelter Org",
        food_categories_accepted=["bakery"]
    )
    db_session.add(rec_prof)
    db_session.commit()

    donation = Donation(
        donor_id=donor.id,
        food_type="bakery",
        description="Fresh bread loaves",
        quantity_kg=15.0,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        latitude=40.71,
        longitude=-74.00,
        pickup_address="10 Baker Ave"
    )
    db_session.add(donation)
    db_session.commit()

    allocation = Allocation(
        donation_id=donation.id,
        recipient_id=rec_prof.id,
        quantity_kg=15.0
    )
    db_session.add(allocation)
    db_session.commit()

    delivery = Delivery(
        allocation_id=allocation.id,
        volunteer_id=volunteer.id,
        status=DeliveryStatus.CLAIMED,
        scheduled_pickup=datetime.now(timezone.utc) + timedelta(hours=1),
        distance_km=3.5,
        estimated_duration_min=15
    )
    db_session.add(delivery)
    db_session.commit()

    retrieved_delivery = db_session.query(Delivery).filter_by(id=delivery.id).first()
    assert retrieved_delivery is not None
    assert retrieved_delivery.status == DeliveryStatus.CLAIMED
    assert retrieved_delivery.volunteer_id == volunteer.id
    assert retrieved_delivery.distance_km == 3.5


def test_notification_and_audit_log(db_session: Session):
    """Test Notification and AuditLog recording."""
    user = User(email="audited@ex.org", hashed_password="pw", full_name="Audited User", role=UserRole.ADMIN)
    db_session.add(user)
    db_session.commit()

    notification = Notification(
        user_id=user.id,
        title="Welcome to FoodBridge",
        message="Your account is active.",
        channel=NotificationChannel.IN_APP
    )
    audit = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="users",
        entity_id=user.id,
        new_values={"email": user.email, "role": user.role.value},
        ip_address="127.0.0.1"
    )
    db_session.add_all([notification, audit])
    db_session.commit()

    retrieved_audit = db_session.query(AuditLog).filter_by(entity_id=user.id).first()
    assert retrieved_audit is not None
    assert retrieved_audit.action == "USER_REGISTERED"
    assert retrieved_audit.new_values["email"] == "audited@ex.org"

    retrieved_notif = db_session.query(Notification).filter_by(user_id=user.id).first()
    assert retrieved_notif is not None
    assert retrieved_notif.is_read is False
