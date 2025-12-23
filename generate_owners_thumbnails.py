"""
Generate thumbnails for existing owner images

Run this script after adding the thumbnail_url column:
python generate_owners_thumbnails.py
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.core.config import settings
from app.models.owner import Owner
from app.utils.image_utils import ImageProcessor
from app.services.storage import storage_service

# Create database session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def generate_thumbnails_for_owners():
    """Generate thumbnails for all owners that have photos but no thumbnails"""

    # Get all owners with images but no thumbnails
    owners = db.query(Owner).filter(
        Owner.photo_url.isnot(None),
        Owner.thumbnail_url.is_(None)
    ).all()

    if not owners:
        print("✅ No owners need thumbnail generation!")
        return

    print(f"📸 Found {len(owners)} owners that need thumbnails\n")

    processor = ImageProcessor()

    if not storage_service.client:
        print("❌ Storage client not initialized")
        return

    bucket = storage_service.client.bucket(storage_service.bucket_name)

    success_count = 0
    error_count = 0

    for i, owner in enumerate(owners, 1):
        try:
            print(f"[{i}/{len(owners)}] Processing: {owner.full_name}")

            # Download original image
            original_blob = bucket.blob(owner.photo_url)

            # Check if blob exists
            if not original_blob.exists():
                print(f"  ⚠️  Original image not found: {owner.photo_url}")
                error_count += 1
                continue

            # Reload to get metadata
            original_blob.reload()

            # Download image bytes
            image_bytes = original_blob.download_as_bytes()
            original_size = len(image_bytes)

            # Generate thumbnail
            thumbnail_bytes = processor.create_thumbnail(image_bytes)
            thumbnail_size = len(thumbnail_bytes)

            # Calculate savings
            savings_pct = ((original_size - thumbnail_size) / original_size) * 100

            # Upload thumbnail with naming convention: {original_name}_thumb.jpg
            path = Path(owner.photo_url)
            thumbnail_blob_name = f"{path.parent}/{path.stem}_thumb{path.suffix}"

            thumbnail_blob = bucket.blob(thumbnail_blob_name)
            thumbnail_blob.upload_from_string(
                thumbnail_bytes,
                content_type="image/jpeg"
            )

            # Update database
            owner.thumbnail_url = thumbnail_blob_name
            db.commit()

            print(f"  ✅ Generated thumbnail: {original_size//1024}KB → {thumbnail_size//1024}KB ({savings_pct:.0f}% smaller)")
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            error_count += 1
            db.rollback()
            continue

    print(f"\n{'='*60}")
    print(f"✅ Successfully generated {success_count} thumbnails")
    if error_count > 0:
        print(f"❌ Failed to generate {error_count} thumbnails")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        generate_thumbnails_for_owners()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
    finally:
        db.close()
