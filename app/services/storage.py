"""
Google Cloud Storage Service
"""
import os
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from google.cloud import storage
from google.auth import compute_engine
from app.core.config import settings
import uuid
from datetime import timedelta
from app.utils.image_utils import process_bull_image_upload

class StorageService:
    def __init__(self):
        self.bucket_name = settings.GCP_BUCKET_NAME
        self.client = None
        self.signing_credentials = None

        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                self.client = storage.Client.from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)
                # Service account JSON has signing credentials
                self.signing_credentials = self.client._credentials
            except Exception as e:
                print(f"Failed to initialize GCP Storage client: {e}")
                # Re-raise so we know why it failed immediately
                raise e
        else:
            # Use default credentials (for Cloud Run)
            try:
                self.client = storage.Client()
                # For Cloud Run, use compute engine credentials for signing
                # This uses IAM signBlob API which works with service accounts
                try:
                    self.signing_credentials = compute_engine.IDTokenCredentials(
                        request=None,
                        target_audience="",
                        use_metadata_identity_endpoint=True
                    )
                except:
                    # If that fails, signing will use IAM API automatically
                    self.signing_credentials = None
            except Exception as e:
                print(f"Failed to initialize GCP Storage client (default creds): {e}")

    async def upload_file(self, file: UploadFile, folder: str = "marketplace") -> str:
        """
        Upload file to GCP Bucket
        Returns the blob name (storage path)
        """
        if not self.client:
            raise Exception("GCP Storage client not initialized. Check credentials.")
            
        if not self.bucket_name:
            raise Exception("GCP_BUCKET_NAME not set in configuration")

        bucket = self.client.bucket(self.bucket_name)
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{folder}/{uuid.uuid4()}{file_ext}"
        
        blob = bucket.blob(unique_filename)
        
        # Read file content
        contents = await file.read()
        
        # Upload
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
        # Return path (blob name) for DB storage
        return unique_filename

    async def upload_bull_image(self, file: UploadFile, folder: str = "race_bulls") -> Tuple[str, str]:
        """
        Upload bull image with thumbnail generation
        Returns (photo_url, thumbnail_url) tuple

        This optimizes loading performance:
        - Thumbnail: ~30-50 KB (for list views)
        - Original: ~100-200 KB (for detail views)
        """
        if not self.client:
            raise Exception("GCP Storage client not initialized. Check credentials.")

        if not self.bucket_name:
            raise Exception("GCP_BUCKET_NAME not set in configuration")

        bucket = self.client.bucket(self.bucket_name)

        # Read original file
        contents = await file.read()

        # Generate both optimized original and thumbnail
        optimized_original, thumbnail, original_filename, thumbnail_filename = process_bull_image_upload(
            contents,
            file.filename
        )

        # Generate unique filenames
        file_ext = Path(file.filename).suffix.lower()
        base_uuid = str(uuid.uuid4())

        # Upload original
        original_blob_name = f"{folder}/{base_uuid}{file_ext}"
        original_blob = bucket.blob(original_blob_name)
        original_blob.upload_from_string(
            optimized_original,
            content_type="image/jpeg"
        )

        # Upload thumbnail
        thumbnail_blob_name = f"{folder}/{base_uuid}_thumb{file_ext}"
        thumbnail_blob = bucket.blob(thumbnail_blob_name)
        thumbnail_blob.upload_from_string(
            thumbnail,
            content_type="image/jpeg"
        )

        print(f"✓ Uploaded bull image: original={original_blob_name}, thumbnail={thumbnail_blob_name}")

        return original_blob_name, thumbnail_blob_name

    async def upload_owner_image(self, file: UploadFile, folder: str = "owners") -> Tuple[str, str]:
        """
        Upload owner image with thumbnail generation
        Returns (photo_url, thumbnail_url) tuple

        This optimizes loading performance:
        - Thumbnail: ~30-50 KB (for list views)
        - Original: ~100-200 KB (for detail views)
        """
        if not self.client:
            raise Exception("GCP Storage client not initialized. Check credentials.")

        if not self.bucket_name:
            raise Exception("GCP_BUCKET_NAME not set in configuration")

        bucket = self.client.bucket(self.bucket_name)

        # Read original file
        contents = await file.read()

        # Generate both optimized original and thumbnail (reuse bull image processing)
        optimized_original, thumbnail, original_filename, thumbnail_filename = process_bull_image_upload(
            contents,
            file.filename
        )

        # Generate unique filenames
        file_ext = Path(file.filename).suffix.lower()
        base_uuid = str(uuid.uuid4())

        # Upload original
        original_blob_name = f"{folder}/{base_uuid}{file_ext}"
        original_blob = bucket.blob(original_blob_name)
        original_blob.upload_from_string(
            optimized_original,
            content_type="image/jpeg"
        )

        # Upload thumbnail
        thumbnail_blob_name = f"{folder}/{base_uuid}_thumb{file_ext}"
        thumbnail_blob = bucket.blob(thumbnail_blob_name)
        thumbnail_blob.upload_from_string(
            thumbnail,
            content_type="image/jpeg"
        )

        print(f"✓ Uploaded owner image: original={original_blob_name}, thumbnail={thumbnail_blob_name}")

        return original_blob_name, thumbnail_blob_name

    def generate_signed_url(self, blob_name: str, expiration: int = 3600) -> str:
        """
        Generate a signed URL for a blob

        Args:
            blob_name: The blob path in GCS
            expiration: Expiration time in seconds (default: 3600 = 1 hour)
        """
        if not self.client or not self.bucket_name or not blob_name:
            return ""

        # Handle case where old full URLs might still be in DB
        prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
        if blob_name.startswith(prefix):
            blob_name = blob_name[len(prefix):]

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)

        try:
            # Generate signed URL - works with both service account JSON and Cloud Run ADC
            # When using ADC in Cloud Run, this will use IAM signBlob API automatically
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(seconds=expiration),
                method="GET"
            )
            return url
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            print(f"Blob: {blob_name}, Bucket: {self.bucket_name}")
            import traceback
            traceback.print_exc()
            # Fallback to public URL format
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    def delete_file(self, file_path: str):
        """Delete file from bucket"""
        if not self.client or not self.bucket_name:
            return

        # Handle full URL if present
        prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
        if file_path.startswith(prefix):
            blob_name = file_path[len(prefix):]
        else:
            blob_name = file_path

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        try:
            blob.delete()
        except Exception as e:
            print(f"Error deleting file {blob_name}: {e}")

storage_service = StorageService()
