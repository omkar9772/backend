"""
Create device_tokens table in Neon DB
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def create_device_tokens_table():
    """Create device_tokens table in the database"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        sys.exit(1)

    try:
        # Connect to database
        print(f"🔌 Connecting to Neon DB...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'create_device_tokens_table.sql')
        with open(sql_file, 'r') as f:
            sql = f.read()

        # Execute SQL
        print(f"📝 Creating device_tokens table...")
        cursor.execute(sql)
        conn.commit()

        # Verify table was created
        cursor.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'device_tokens'
            ORDER BY ordinal_position;
        """)

        columns = cursor.fetchall()

        if columns:
            print(f"\n✅ device_tokens table created successfully!")
            print(f"\n📋 Table structure:")
            for table, column, dtype in columns:
                print(f"   - {column}: {dtype}")
        else:
            print(f"⚠️ Table may already exist")

        # Check indexes
        cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'device_tokens';
        """)

        indexes = cursor.fetchall()
        if indexes:
            print(f"\n🔍 Indexes created:")
            for idx in indexes:
                print(f"   - {idx[0]}")

        cursor.close()
        conn.close()

        print(f"\n✅ Database setup complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_device_tokens_table()
