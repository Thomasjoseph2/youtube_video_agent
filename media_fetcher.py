import os
import requests
import random
import time
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

class MediaFetcher:
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        self.pixabay_key = os.getenv("PIXABAY_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")

        if not self.pexels_key:
            print("⚠️ PEXELS_API_KEY missing. Pexels disabled.")
            
        self.headers = {"Authorization": self.pexels_key} if self.pexels_key else {}
        
        # Vision Model for Verification
        if self.google_key:
            # User requested gemini-2.5-flash
            self.vision_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                temperature=0,
                safety_settings={
                    "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                    "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                    "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                    "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                }
            )
        else:
            print("⚠️ GOOGLE_API_KEY missing. Visual verification disabled.")
            self.vision_model = None

    def download_media(self, search_terms: List[str], target_dir: str, max_items: int = 1) -> List[str]:
        """
        Smart download: Searches Pexels (Videos+Images), VERIFIES content with Gemini, then downloads.
        """
        downloaded_files = []
        os.makedirs(target_dir, exist_ok=True)
        
        for term in search_terms:
            print(f"   🔍 Searching for: '{term}'")
            
            # 1. Gather Candidates (Videos + Images)
            candidates = []
            
            # Pexels Videos
            candidates.extend(self._search_pexels_videos(term))
            
            # Pexels Images (Fallback/Mix)
            candidates.extend(self._search_pexels_images(term))
            
            # Pixabay Videos (Fallback)
            if len(candidates) < 5 and self.pixabay_key:
                 candidates.extend(self._search_pixabay_candidates(term))
            
            # 2. Verify and Download
            found_match = False
            for cand in candidates:
                # Determine extension based on type
                ext = ".mp4" if cand['type'] == 'video' else ".jpg"
                filename = f"{term[:10].replace(' ', '_')}_{cand['id']}{ext}"
                
                # Check if file already exists locally to skip verification if possible
                filepath = os.path.join(target_dir, filename)
                if os.path.exists(filepath):
                    downloaded_files.append(filepath)
                    found_match = True
                    break

                # Verification
                if self.vision_model:
                    print(f"      👁️ Verifying candidate {cand['id']} ({cand['type']})...")
                    if self._verify_content(cand['image'], term):
                        print("      ✅ Match confirmed!")
                        filepath = self._download_file(cand['download_url'], filename, target_dir)
                        if filepath:
                            downloaded_files.append(filepath)
                            found_match = True
                            break
                    else:
                        print("      ❌ Rejected (irrelevant content).")
                else:
                    # No verification
                    filepath = self._download_file(cand['download_url'], filename, target_dir)
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
        Uses Gemini Vision to verify content. 
        Fail-Open on Rate Limit / Safety Blocks.
        """
        try:
            # Construct a prompt for the vision model
            prompt = f"""Look at this image. 
            Does it accurately depict: "{query}"?
            Strict Rules: Answer ONLY 'YES' or 'NO'."""
            
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
            # Handle Quota Exceeded (429) gracefully to prevent crash
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"      ⚠️ Quota Exceeded for Verification. Defaulting to MATCH.")
                return True # Fail Open: Assume it matches so we don't break the user flow
            
            print(f"      Verify Error: {e}")
            return True # Fail Open

    def _search_pexels_videos(self, query: str) -> List[dict]:
        """Returns list of {id, type='video', download_url, image}"""
        if not self.pexels_key: return []
        results = []
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation=portrait"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                for v in data.get('videos', []):
                    files = sorted(v['video_files'], key=lambda x: x['width'] * x['height'], reverse=True)
                    if files:
                        results.append({
                            'id': v['id'],
                            'type': 'video',
                            'download_url': files[0]['link'],
                            'image': v['image'] 
                        })
        except Exception: pass
        return results

    def _search_pexels_images(self, query: str) -> List[dict]:
        """Returns list of {id, type='image', download_url, image}"""
        if not self.pexels_key: return []
        results = []
        url = f"https://api.pexels.com/v1/search?query={query}&per_page=10&orientation=portrait"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                for photo in data.get('photos', []):
                    img_url = photo['src']['large']
                    results.append({
                        'id': photo['id'],
                        'type': 'image',
                        'download_url': img_url,
                        'image': img_url 
                    })
        except Exception: pass
        return results

    def _search_pixabay_candidates(self, query: str) -> List[dict]:
        """Returns list of {id, type='video', download_url, image}"""
        if not self.pixabay_key: return []
        results = []
        url = f"https://pixabay.com/api/videos/?key={self.pixabay_key}&q={query}&per_page=15&orientation=vertical"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for v in data.get('hits', []):
                     if 'large' in v.get('videos', {}):
                         vid_url = v['videos']['large']['url']
                         pic_id = v.get('picture_id')
                         thumb = f"https://i.vimeocdn.com/video/{pic_id}_295x166.jpg"
                         results.append({
                            'id': v['id'],
                            'type': 'video',
                            'download_url': vid_url,
                            'image': thumb
                        })
        except Exception: pass
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
