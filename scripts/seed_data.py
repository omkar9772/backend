"""
Seed script to populate database with sample data for testing
"""
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.db.base import SessionLocal, engine, Base
from app.models import (
    District, Taluka, Tahsil, Village,
    Owner, Bull, Race, RaceResult,
    AdminUser
)
from app.core.security import get_password_hash


def create_admin_user(db: Session):
    """Create initial admin user"""
    print("Creating admin user...")

    admin = AdminUser(
        username="admin",
        email="admin@naadbailgada.com",
        password_hash=get_password_hash("admin123"),
        full_name="System Administrator",
        role="super_admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    print(f"✅ Created admin user: {admin.username}")


def create_regions(db: Session):
    """Create sample regional hierarchy for Maharashtra"""
    print("\nCreating regional hierarchy...")

    # District: Kolhapur
    kolhapur = District(name="Kolhapur", state="Maharashtra")
    db.add(kolhapur)
    db.commit()
    db.refresh(kolhapur)
    print(f"✅ Created district: {kolhapur.name}")

    # Taluka: Karveer
    karveer = Taluka(name="Karveer", district_id=kolhapur.id)
    db.add(karveer)
    db.commit()
    db.refresh(karveer)
    print(f"✅ Created taluka: {karveer.name}")

    # Tahsil: Shirol
    shirol_tahsil = Tahsil(name="Shirol", taluka_id=karveer.id)
    db.add(shirol_tahsil)
    db.commit()
    db.refresh(shirol_tahsil)
    print(f"✅ Created tahsil: {shirol_tahsil.name}")

    # Villages
    villages_data = [
        {"name": "Shirol", "pincode": "416103"},
        {"name": "Kurundvad", "pincode": "416106"},
        {"name": "Halkarni", "pincode": "416109"},
    ]

    villages = []
    for village_data in villages_data:
        village = Village(
            name=village_data["name"],
            tahsil_id=shirol_tahsil.id,
            pincode=village_data["pincode"]
        )
        db.add(village)
        villages.append(village)

    db.commit()
    for village in villages:
        db.refresh(village)
        print(f"✅ Created village: {village.name}")

    return villages


def create_owners_and_bulls(db: Session, villages):
    """Create sample owners and bulls"""
    print("\nCreating owners and bulls...")

    owners_data = [
        {"name": "Ramesh Patil", "phone": "+91-9876543210", "village_idx": 0},
        {"name": "Suresh Jadhav", "phone": "+91-9876543211", "village_idx": 0},
        {"name": "Mahesh Shinde", "phone": "+91-9876543212", "village_idx": 1},
        {"name": "Ganesh Desai", "phone": "+91-9876543213", "village_idx": 1},
        {"name": "Rajesh More", "phone": "+91-9876543214", "village_idx": 2},
    ]

    owners = []
    for owner_data in owners_data:
        owner = Owner(
            full_name=owner_data["name"],
            phone_number=owner_data["phone"],
            village_id=villages[owner_data["village_idx"]].id,
            address=f"Main Street, {villages[owner_data['village_idx']].name}",
            is_active=True
        )
        db.add(owner)
        owners.append(owner)

    db.commit()
    for owner in owners:
        db.refresh(owner)
        print(f"✅ Created owner: {owner.full_name}")

    # Bulls
    bulls_data = [
        {"name": "Vajra", "owner_idx": 0, "village_idx": 0, "year": 2020, "breed": "Khillar", "color": "Black"},
        {"name": "Nandi", "owner_idx": 0, "village_idx": 0, "year": 2019, "breed": "Khillar", "color": "Brown"},
        {"name": "Shiva", "owner_idx": 1, "village_idx": 0, "year": 2021, "breed": "Khillar", "color": "White"},
        {"name": "Mahesh", "owner_idx": 2, "village_idx": 1, "year": 2020, "breed": "Khillar", "color": "Black"},
        {"name": "Ganpat", "owner_idx": 3, "village_idx": 1, "year": 2022, "breed": "Khillar", "color": "Brown"},
        {"name": "Sambhaji", "owner_idx": 4, "village_idx": 2, "year": 2019, "breed": "Khillar", "color": "White"},
        {"name": "Shivaji", "owner_idx": 4, "village_idx": 2, "year": 2021, "breed": "Khillar", "color": "Black"},
    ]

    bulls = []
    for idx, bull_data in enumerate(bulls_data):
        bull = Bull(
            name=bull_data["name"],
            owner_id=owners[bull_data["owner_idx"]].id,
            village_id=villages[bull_data["village_idx"]].id,
            birth_year=bull_data["year"],
            breed=bull_data["breed"],
            color=bull_data["color"],
            description=f"Champion bull from {villages[bull_data['village_idx']].name}",
            registration_number=f"BUL-2024-{idx+1:03d}",
            is_active=True
        )
        db.add(bull)
        bulls.append(bull)

    db.commit()
    for bull in bulls:
        db.refresh(bull)
        print(f"✅ Created bull: {bull.name} (Owner: {bull.owner.full_name})")

    return bulls


def create_races_and_results(db: Session, villages, bulls):
    """Create sample races and results"""
    print("\nCreating races and results...")

    # Race 1: Shirol Annual Race (November 2024)
    race1 = Race(
        name="Shirol Annual Championship 2024",
        race_date=date(2024, 11, 15),
        village_id=villages[0].id,
        track_length_meters=200,
        description="Annual championship race in Shirol",
        status="completed",
        total_participants=4,
        created_by="admin"
    )
    db.add(race1)
    db.commit()
    db.refresh(race1)
    print(f"✅ Created race: {race1.name}")

    # Results for race 1
    results_race1 = [
        {"bull_idx": 0, "position": 1, "time": 18500},  # Vajra wins
        {"bull_idx": 2, "position": 2, "time": 19200},  # Shiva
        {"bull_idx": 1, "position": 3, "time": 19800},  # Nandi
    ]

    for result_data in results_race1:
        result = RaceResult(
            race_id=race1.id,
            bull_id=bulls[result_data["bull_idx"]].id,
            position=result_data["position"],
            time_milliseconds=result_data["time"],
            is_disqualified=False
        )
        db.add(result)

    db.commit()
    print(f"✅ Added results for {race1.name}")

    # Race 2: Kurundvad Race (November 2024)
    race2 = Race(
        name="Kurundvad Diwali Race 2024",
        race_date=date(2024, 11, 20),
        village_id=villages[1].id,
        track_length_meters=200,
        description="Diwali special race",
        status="completed",
        total_participants=3,
        created_by="admin"
    )
    db.add(race2)
    db.commit()
    db.refresh(race2)
    print(f"✅ Created race: {race2.name}")

    # Results for race 2
    results_race2 = [
        {"bull_idx": 3, "position": 1, "time": 18800},  # Mahesh wins
        {"bull_idx": 4, "position": 2, "time": 19500},  # Ganpat
    ]

    for result_data in results_race2:
        result = RaceResult(
            race_id=race2.id,
            bull_id=bulls[result_data["bull_idx"]].id,
            position=result_data["position"],
            time_milliseconds=result_data["time"],
            is_disqualified=False
        )
        db.add(result)

    db.commit()
    print(f"✅ Added results for {race2.name}")

    # Race 3: Upcoming race
    race3 = Race(
        name="Halkarni New Year Race 2025",
        race_date=date(2025, 1, 1),
        village_id=villages[2].id,
        track_length_meters=200,
        description="New Year championship",
        status="scheduled",
        total_participants=0,
        created_by="admin"
    )
    db.add(race3)
    db.commit()
    db.refresh(race3)
    print(f"✅ Created race: {race3.name}")


def seed_database():
    """Main function to seed the database"""
    print("=" * 60)
    print("NAAD BAILGADA - Database Seed Script")
    print("=" * 60)

    # Create database session
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_admin = db.query(AdminUser).first()
        if existing_admin:
            print("\n⚠️  Database already contains data!")
            response = input("Do you want to clear and reseed? (yes/no): ")
            if response.lower() != "yes":
                print("Aborting seed operation.")
                return

            print("\nClearing existing data...")
            # Delete in reverse order of foreign key dependencies
            db.query(RaceResult).delete()
            db.query(Race).delete()
            db.query(Bull).delete()
            db.query(Owner).delete()
            db.query(Village).delete()
            db.query(Tahsil).delete()
            db.query(Taluka).delete()
            db.query(District).delete()
            db.query(AdminUser).delete()
            db.commit()
            print("✅ Cleared existing data")

        # Seed data
        create_admin_user(db)
        villages = create_regions(db)
        bulls = create_owners_and_bulls(db, villages)
        create_races_and_results(db, villages, bulls)

        print("\n" + "=" * 60)
        print("✅ Database seeded successfully!")
        print("=" * 60)
        print("\n📋 Summary:")
        print(f"   - Admin user: admin / admin123")
        print(f"   - Districts: {db.query(District).count()}")
        print(f"   - Talukas: {db.query(Taluka).count()}")
        print(f"   - Tahsils: {db.query(Tahsil).count()}")
        print(f"   - Villages: {db.query(Village).count()}")
        print(f"   - Owners: {db.query(Owner).count()}")
        print(f"   - Bulls: {db.query(Bull).count()}")
        print(f"   - Races: {db.query(Race).count()}")
        print(f"   - Race Results: {db.query(RaceResult).count()}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
