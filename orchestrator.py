import os
import shutil
from datetime import datetime
import re
from typing import Callable, Optional
from dotenv import load_dotenv

from agent import VideoDirector
from media_fetcher import MediaFetcher
from audio_generator import AudioGenerator
from video_editor import VideoAssembler
from cloudinary_manager import CloudinaryManager
from library_manager import LibraryManager

load_dotenv()

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

class VideoOrchestrator:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.temp_base = os.path.join(self.base_dir, "data", "temp")
        self.result_base = os.path.join(self.base_dir, "data", "results")
        
        self.director = VideoDirector()
        self.fetcher = MediaFetcher()
        self.audio_gen = AudioGenerator()
        self.editor = VideoAssembler()
        self.cloudinary = CloudinaryManager()
        self.library = LibraryManager()

    def create_video(self, user_prompt: str, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Orchestrates the creation of a video from a prompt.
        """
        def log(msg):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        # 1. Setup Session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = slugify(user_prompt[:30])
        session_id = f"{timestamp}_{slug}"
        temp_dir = os.path.join(self.temp_base, session_id)
        result_dir = os.path.join(self.result_base, session_id)
        
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)
        
        log(f"🚀 Starting Session: {session_id}")

        try:
            # 2. Agent (Script & Plan)
            log("🧠 Director: Planning script and visuals...")
            script_data = self.director.generate_script(user_prompt)
            timeline = script_data.get('timeline', [])
            
            if not timeline:
                raise ValueError("Agent failed to generate a valid timeline.")

            # 3. Media Fetching
            log(f"🎥 Media: Searching for {len(timeline)} scenes...")
            media_files = []
            search_terms = [scene['visual_query'] for scene in timeline]
            # We fetch individually to map them to scenes
            for i, scene in enumerate(timeline):
                term = scene['visual_query']
                log(f"   Downloading media for: {term}")
                files = self.fetcher.download_media([term], temp_dir, max_items=1)
                if files:
                    media_files.append(files[0])
                else:
                    # Fallback or placeholder? For now, we skip or duplicate previous
                    log(f"   ⚠️ Could not find media for {term}")
                    media_files.append(None) # Handle in editor

            # 4. Audio Generation
            log("🎙️ Audio: Generatng voiceover...")
            full_script = " ".join([scene['script'] for scene in timeline])
            audio_path = os.path.join(temp_dir, "narration.mp3")
            # We generate one full audio file for simplicity in this version, 
            # ideally we'd generate per scene for precise alignment, but let's start simple.
            # WAIT: agent.py generates a list of scenes with duration.
            # To match visuals to audio, we should generate audio PER SCENE or use the estimated duration.
            # MVP Pro approach: Generate FULL audio, but we need to know duration of each segment to cut video.
            # Let's stick to full audio for flow, and try to time visuals to it?
            # Actually, user wants "Fast cuts (every 2-3 seconds)".
            # Let's generate audio per scene and concat? That ensures perfect alignment.
            
            scene_audio_paths = []
            for i, scene in enumerate(timeline):
                 scene_audio_path = os.path.join(temp_dir, f"audio_{i}.mp3")
                 # generate_narrative now returns (audio_path, subs_path)
                 result = self.audio_gen.generate_narrative(scene['script'], scene_audio_path)
                 scene_audio_paths.append(result)
            
            # 5. Video Assembly
            log("✂️ Editor: Assembling execution...")
            final_video_path = os.path.join(result_dir, "final.mp4")
            self.editor.assemble_video_from_timeline(timeline, media_files, scene_audio_paths, final_video_path)

            # 6. Cloudinary
            log("☁️ Cloud: Uploading to Cloudinary...")
            cloud_url = self.cloudinary.upload_video(final_video_path, public_id=session_id)
            
            # 7. Library
            log("📚 Library: Saving record...")
            video_record = {
                "id": session_id,
                "prompt": user_prompt,
                "local_path": final_video_path,
                "cloudinary_url": cloud_url,
                "timestamp": timestamp,
                "timeline": timeline 
            }
            self.library.add_entry(video_record)

            # 8. Cleanup
            log("🧹 Cleanup: Removing temp files...")
            shutil.rmtree(temp_dir)
            
            log("✨ Video Creation Complete!")
            return video_record

        except Exception as e:
            log(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
