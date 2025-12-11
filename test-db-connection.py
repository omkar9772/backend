#!/usr/bin/env python3
"""
Test database connection to Neon PostgreSQL
"""

import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    sys.exit(1)

print("🔍 Testing database connection...")
print(f"Database: {DATABASE_URL.split('@')[1].split('/')[0] if '@' in DATABASE_URL else 'Unknown'}")
print("")

try:
    # Create engine
    engine = create_engine(DATABASE_URL, echo=False)

    # Test connection
    with engine.connect() as connection:
        # Test basic query
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]

        print("✅ Database connection successful!")
        print(f"PostgreSQL version: {version.split(',')[0]}")
        print("")

        # Check if tables exist
        result = connection.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]

        if tables:
            print(f"📊 Found {len(tables)} existing tables:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("📋 No tables found (database is empty)")
            print("   Run migrations to create tables: alembic upgrade head")

        print("")
        print("🎉 Database is ready!")

except Exception as e:
    print(f"❌ Database connection failed!")
    print(f"Error: {str(e)}")
    print("")
    print("Troubleshooting:")
    print("1. Check if DATABASE_URL is correct in .env")
    print("2. Verify Neon database is accessible")
    print("3. Check firewall/network settings")
    sys.exit(1)
