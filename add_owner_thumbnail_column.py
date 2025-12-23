"""
Add thumbnail_url column to owners table

Run this script to add the thumbnail_url column to the owners table:
python add_owner_thumbnail_column.py
"""
from app.db.base import SessionLocal
from sqlalchemy import text

def add_thumbnail_column():
    """Add thumbnail_url column to owners table"""
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='owners' AND column_name='thumbnail_url'
        """))

        if result.fetchone():
            print("✓ Column 'thumbnail_url' already exists in owners table")
            return

        # Add the column
        db.execute(text("""
            ALTER TABLE owners
            ADD COLUMN thumbnail_url VARCHAR(500)
        """))
        db.commit()
        print("✓ Successfully added 'thumbnail_url' column to owners table")

    except Exception as e:
        db.rollback()
        print(f"✗ Error adding column: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding thumbnail_url column to owners table...")
    add_thumbnail_column()
    print("Done!")
