import json
import os
from datetime import datetime
from typing import Dict, List

class LibraryManager:
    def __init__(self, library_path: str = "data/library.json"):
        self.library_path = library_path
        # Ensure file exists
        if not os.path.exists(self.library_path):
            os.makedirs(os.path.dirname(self.library_path), exist_ok=True)
            with open(self.library_path, 'w') as f:
                json.dump([], f)

    def add_entry(self, video_data: Dict):
        """
        Adds a video entry to the library.
        video_data should have: id, prompt, local_path, cloudinary_url, timestamp
        """
        entries = self.get_all_videos()
        entries.append(video_data)
        
        with open(self.library_path, 'w') as f:
            json.dump(entries, f, indent=2)
            
    def get_all_videos(self) -> List[Dict]:
        """Returns all videos (newest first logic can be applied in frontend)"""
        try:
            with open(self.library_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
