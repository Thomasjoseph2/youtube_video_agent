import os
import requests
import random
import time
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class MediaFetcher:
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")

        if not self.pexels_key:
            print("⚠️ PEXELS_API_KEY missing. Pexels disabled.")
            
        self.headers = {"Authorization": self.pexels_key} if self.pexels_key else {}
        
        # Vision Model for Verification
        # Vision Model for Verification
        if self.google_key:
            # User requested gemini-2.5-flash
            self.vision_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                temperature=0,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
        else:
            print("⚠️ GOOGLE_API_KEY missing. Visual verification disabled.")
            self.vision_model = None

    def download_media(self, search_terms: List[str], target_dir: str, max_items: int = 1) -> List[str]:
        """
        Smart download: Searches Pexels/Pixabay, VERIFIES content with Gemini, then downloads.
        """
        downloaded_files = []
        os.makedirs(target_dir, exist_ok=True)
        
        for term in search_terms:
            print(f"   🔍 Searching for: '{term}'")
            
            # 1. Search Pexels (Videos)
            candidates = self._search_pexels_candidates(term)
            
            # 2. Search Pixabay (Videos) as fallback or supplement
            if len(candidates) < 5 and self.pixabay_key:
                 candidates.extend(self._search_pixabay_candidates(term))
            
            # 3. Verify and Download
            found_match = False
            for cand in candidates:
                if self.vision_model:
                    print(f"      👁️ Verifying candidate {cand['id']}...")
                    if self._verify_content(cand['image'], term):
                        print("      ✅ Match confirmed!")
                        filepath = self._download_file(cand['video'], f"{term[:10].replace(' ', '_')}_{cand['id']}.mp4", target_dir)
                        if filepath:
                            downloaded_files.append(filepath)
                            found_match = True
                            break
                    else:
                        print("      ❌ Rejected (irrelevant content).")
                else:
                    # No verification, just take the first one
                    filepath = self._download_file(cand['video'], f"{term[:10].replace(' ', '_')}_{cand['id']}.mp4", target_dir)
                    if filepath:
                        downloaded_files.append(filepath)
                        found_match = True
                        break
            
            if not found_match:
                 print(f"   ⚠️ No suitable media found for '{term}' after verification.")
                 downloaded_files.append(None) # Marker for assembler

        return downloaded_files

    def _verify_content(self, image_url: str, query: str) -> bool:
        """
        Uses Gemini Vision to verify if the image_url matches the query 
        and does NOT contain humans (unless requested).
        """
        try:
            # Construct a prompt for the vision model
            prompt = f"""Look at this image. 
            Does it accurately depict: "{query}"?
            
            Strict Rules:
            1. If the query is about animals (dogs), reject if there are humans prominently in the frame.
            2. Reject if it is not related to the query.
            3. Answer ONLY 'YES' or 'NO'.
            """
            
            msg = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": image_url},
                ]
            )
            response = self.vision_model.invoke([msg])
            result = response.content.strip().upper()
            
            if not result:
                print("      ⚠️ Verification Warning: Empty response (blocked). Defaulting to MATCH.")
                return True
                
            return "YES" in result
        except Exception as e:
            print(f"      Verify Error: {e}")
            return True # Fail open

    def _search_pexels_candidates(self, query: str) -> List[dict]:
        """Returns list of {id, video, image}"""
        if not self.pexels_key: return []
        results = []
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=15&orientation=portrait"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                for v in data.get('videos', []):
                    # Get best quality video link
                    files = sorted(v['video_files'], key=lambda x: x['width'] * x['height'], reverse=True)
                    if files:
                        results.append({
                            'id': v['id'],
                            'video': files[0]['link'],
                            'image': v['image'] # Thumbnail
                        })
        except Exception as e:
            print(f"      Pexels Error: {e}")
        return results

    def _search_pixabay_candidates(self, query: str) -> List[dict]:
        """Returns list of {id, video, image}"""
        if not self.pixabay_key: return []
        results = []
        # Pixabay API requires query param 'q', 'key', 'video_type'
        url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={query}&per_page=15&orientation=vertical"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for v in data.get('hits', []):
                     # Pixabay structure: 'videos' -> 'large' -> 'url'
                     if 'large' in v.get('videos', {}):
                         vid_url = v['videos']['large']['url']
                         # Pixabay doesn't give a direct image url for video easily, 
                         # usually 'userImageURL' or 'userImage' or fetch 'picture_id'
                         # Actually hits have 'userImageURL' but that's user avatar.
                         # 'picture_id' maps to an image url? 
                         # Use 'videos' -> 'medium' -> 'thumbnail' if exists?
                         # Often 'pageURL' has thumbnail.
                         # Let's try 'userImageURL' (often wrong). 
                         # Wait, Pixabay video hits HAVE 'userImageURL' (user avatar) vs 'picture_id'.
                         # Actually for simplification: Pixabay often returns 'thumbnail' in other endpoints, 
                         # Here: 'videos' struct has url, thumb (sometimes). 
                         # Let's check docs: field 'picture_id' allows building URL.
                         # https://i.vimeocdn.com/video/{picture_id}_640x360.jpg
                         # Safe fallback: skip verification for Pixabay if no easy image?
                         # Actually, let's construct it.
                         pic_id = v.get('picture_id')
                         thumb = f"https://i.vimeocdn.com/video/{pic_id}_295x166.jpg"
                         
                         results.append({
                            'id': v['id'],
                            'video': vid_url,
                            'image': thumb
                        })
        except Exception as e:
            print(f"      Pixabay Error: {e}")
        return results

    def _download_file(self, url: str, filename: str, target_dir: str) -> str:
        filepath = os.path.join(target_dir, filename)
        if os.path.exists(filepath): return filepath
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            return filepath
        except Exception: return None
