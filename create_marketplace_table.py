"""
Script to create marketplace_listings table if it doesn't exist
Safe to run - won't affect existing data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, inspect
from app.db.base import Base, engine
from app.models.marketplace import MarketplaceListing

def create_marketplace_table():
    """Create marketplace_listings table if it doesn't exist"""
    print("=" * 60)
    print("Creating Marketplace Table (if not exists)")
    print("=" * 60)

    # Check if table exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    print(f"\nExisting tables in database: {', '.join(existing_tables)}")

    if "marketplace_listings" in existing_tables:
        print("\n✓ marketplace_listings table already exists!")
        print("  No action needed.")
    else:
        print("\n⚠ marketplace_listings table does NOT exist!")
        print("  Creating table now...")

        # Create only the marketplace table
        MarketplaceListing.__table__.create(bind=engine, checkfirst=True)

        print("\n✓ marketplace_listings table created successfully!")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        create_marketplace_table()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
