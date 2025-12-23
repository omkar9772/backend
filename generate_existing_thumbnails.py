"""
Generate thumbnails for existing bull images
Run this once to create thumbnails for all existing bulls
"""
from app.db.base import get_db
from app.models.bull import Bull
from app.services.storage import storage_service
from app.utils.image_utils import ImageProcessor
from google.cloud import storage
from pathlib import Path
import io


def generate_thumbnails_for_existing_bulls():
    """Generate thumbnails for all bulls that have photo_url but no thumbnail_url"""

    db = next(get_db())

    # Get all bulls with photos but no thumbnails
    bulls = db.query(Bull).filter(
        Bull.photo_url.isnot(None),
        Bull.thumbnail_url.is_(None)
    ).all()

    print(f"Found {len(bulls)} bulls needing thumbnails")

    if len(bulls) == 0:
        print("✓ All bulls already have thumbnails!")
        return

    # Initialize GCS client
    client = storage_service.client
    bucket = client.bucket(storage_service.bucket_name)
    processor = ImageProcessor()

    success_count = 0
    error_count = 0

    for i, bull in enumerate(bulls, 1):
        try:
            print(f"\n[{i}/{len(bulls)}] Processing: {bull.name} (ID: {bull.id})")

            # Download original image from GCS
            print(f"  Photo URL: {bull.photo_url}")
            original_blob = bucket.blob(bull.photo_url)

            # Reload blob metadata to get size
            original_blob.reload()

            if not original_blob.exists():
                print(f"  ⚠️  Original image not found in GCS: {bull.photo_url}")
                error_count += 1
                continue

            original_size_kb = (original_blob.size or 0) / 1024
            print(f"  Downloading original ({original_size_kb:.1f} KB)...")
            image_bytes = original_blob.download_as_bytes()

            # Generate thumbnail
            print(f"  Generating thumbnail...")
            thumbnail_bytes = processor.create_thumbnail(image_bytes)
            thumbnail_kb = len(thumbnail_bytes) / 1024

            # Generate thumbnail filename
            path = Path(bull.photo_url)
            thumbnail_blob_name = f"{path.parent}/{path.stem}_thumb{path.suffix}"

            # Upload thumbnail to GCS
            print(f"  Uploading thumbnail ({thumbnail_kb:.1f} KB)...")
            thumbnail_blob = bucket.blob(thumbnail_blob_name)
            thumbnail_blob.upload_from_string(
                thumbnail_bytes,
                content_type="image/jpeg"
            )

            # Update database
            bull.thumbnail_url = thumbnail_blob_name
            db.commit()

            print(f"  ✓ Success! Original: {original_size_kb:.1f} KB → Thumbnail: {thumbnail_kb:.1f} KB")
            success_count += 1

        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            error_count += 1
            db.rollback()
            continue

    print(f"\n{'='*60}")
    print(f"Thumbnail generation complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(bulls)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    generate_thumbnails_for_existing_bulls()
