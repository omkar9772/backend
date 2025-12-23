"""
Make bull images publicly accessible in GCS bucket
This is needed so the mobile app can load images without authentication
"""
from app.services.storage import storage_service
from app.db.base import get_db
from app.models.bull import Bull


def make_bull_images_public():
    """Set all bull images to be publicly readable"""

    db = next(get_db())
    client = storage_service.client
    bucket = client.bucket(storage_service.bucket_name)

    # Get all bulls with images
    bulls = db.query(Bull).filter(
        Bull.photo_url.isnot(None)
    ).all()

    print(f"Found {len(bulls)} bulls with images")
    print(f"Bucket: {storage_service.bucket_name}")
    print()

    success_count = 0

    for bull in bulls:
        try:
            # Make original photo public
            if bull.photo_url:
                blob = bucket.blob(bull.photo_url)
                if blob.exists():
                    blob.make_public()
                    print(f"✓ {bull.name}: {bull.photo_url}")
                    success_count += 1

            # Make thumbnail public
            if bull.thumbnail_url:
                blob = bucket.blob(bull.thumbnail_url)
                if blob.exists():
                    blob.make_public()
                    print(f"  ✓ Thumbnail: {bull.thumbnail_url}")
                    success_count += 1

        except Exception as e:
            print(f"✗ Error for {bull.name}: {str(e)}")

    print()
    print(f"{'='*60}")
    print(f"Made {success_count} images publicly accessible!")
    print(f"{'='*60}")
    print()
    print("Images are now accessible at:")
    print(f"https://storage.googleapis.com/{storage_service.bucket_name}/[blob_path]")


if __name__ == "__main__":
    make_bull_images_public()
