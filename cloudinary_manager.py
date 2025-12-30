import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

class CloudinaryManager:
    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET")
        
        if not all([self.cloud_name, self.api_key, self.api_secret]):
            print("⚠️ Cloudinary credentials missing. Videos will be local only.")
            self.enabled = False
        else:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
            self.enabled = True

    def upload_video(self, file_path: str, public_id: str) -> str:
        """
        Uploads a video to Cloudinary and returns the secure URL.
        """
        if not self.enabled:
            return None
            
        print(f"   ☁️ Uploading to Cloudinary (IDs: {public_id})...")
        try:
            response = cloudinary.uploader.upload(
                file_path, 
                resource_type="video", 
                public_id=public_id,
                folder="dog_videos"
            )
            url = response.get("secure_url")
            print(f"   ✅ Uploaded: {url}")
            return url
        except Exception as e:
            print(f"   ❌ Cloudinary Upload Error: {e}")
            return None
