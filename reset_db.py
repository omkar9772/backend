"""
Script to reset (drop and recreate) the database
USE WITH CAUTION: This will delete all data!
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.base import Base, engine
from app.models.admin import AdminUser
from app.models.bull import Bull
from app.models.owner import Owner
from app.models.race import Race, RaceResult


def reset_database():
    """Drop all tables and recreate them"""
    print("=" * 50)
    print("DATABASE RESET")
    print("=" * 50)
    print("\nWARNING: This will delete ALL data in the database!")

    confirm = input("\nType 'YES' to confirm: ")
    if confirm != "YES":
        print("Reset cancelled.")
        return

    print("\nDropping materialized views and tables...")
    # Drop materialized views first (they may depend on tables)
    from sqlalchemy import text
    with engine.connect() as connection:
        # Drop all materialized views
        result = connection.execute(text("""
            SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'
        """))
        for row in result:
            matview_name = row[0]
            print(f"  Dropping materialized view: {matview_name}")
            connection.execute(text(f"DROP MATERIALIZED VIEW IF EXISTS {matview_name} CASCADE"))
        connection.commit()

    # Now drop all tables
    Base.metadata.drop_all(bind=engine)
    print("All tables and views dropped successfully!")

    print("\nCreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

    print("\n" + "=" * 50)
    print("Database reset complete!")
    print("=" * 50)
    print("\nYou can now start the application with:")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    reset_database()
