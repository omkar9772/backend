"""
Google Cloud Storage Service
"""
import os
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from google.cloud import storage
from app.core.config import settings
import uuid

class StorageService:
    def __init__(self):
        self.bucket_name = settings.GCP_BUCKET_NAME
        self.client = None
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            try:
                self.client = storage.Client.from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)
            except Exception as e:
                print(f"Failed to initialize GCP Storage client: {e}")
                # Re-raise so we know why it failed immediately
                raise e
        else:
             # Try default credentials or warn
             try:
                 self.client = storage.Client()
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

    def generate_signed_url(self, blob_name: str, expiration: int = 3600) -> str:
        """Generate a signed URL for a blob"""
        if not self.client or not self.bucket_name or not blob_name:
            return ""
            
        # Handle case where old full URLs might still be in DB
        prefix = f"https://storage.googleapis.com/{self.bucket_name}/"
        if blob_name.startswith(prefix):
            blob_name = blob_name[len(prefix):]

        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        
        try:
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="GET"
            )
            return url
        except Exception as e:
            print(f"Error generating signed URL: {e}")
            return blob_name

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
