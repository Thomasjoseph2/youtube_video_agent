import os
import shutil
import asyncio
from datetime import datetime
import re
from dotenv import load_dotenv
from agent import VideoDirector
from media_fetcher import MediaFetcher
from audio_generator import AudioGenerator
from video_editor import VideoAssembler

# Load environment variables
load_dotenv()

def slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

def main():
    print("🐶 Welcome to the Dog Video AI Agent! 🎥")
    
    # Check for keys
    if not os.getenv("PEXELS_API_KEY"):
        print("❌ Error: PEXELS_API_KEY not found in .env")
        return
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in .env")
        return

    # 1. Get User Input
    import sys
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
        print(f"\nUsing command line prompt: '{user_prompt}'")
    else:
        user_prompt = input("\nWhat kind of dog video should I make? (e.g., 'Funny pugs eating'): ")
    
    if not user_prompt:
        print("Please enter a prompt!")
        return

    # 2. Setup Workspace (Temp & Results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_slug = slugify(user_prompt[:30])
    session_id = f"{timestamp}_{session_slug}"
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    temp_dir = os.path.join(base_dir, "data", "temp", session_id)
    result_dir = os.path.join(base_dir, "data", "results", session_id)
    
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)
    print(f"\n📂 Session: {session_id}")
    print(f"   Temp: {temp_dir}")
    print(f"   Result: {result_dir}")

    try:
        print(f"\n🎬 Scene 1: Directing... (Analyzing '{user_prompt}')")
        director = VideoDirector()
        script_data = director.generate_script(user_prompt)
        print(f"   📝 Generated search terms: {script_data.get('search_terms')}")
        print(f"   📜 Script: {script_data.get('narrative_script')[:50]}...")

        print("\n🎬 Scene 2: Casting... (Fetching media)")
        fetcher = MediaFetcher()
        # Download to temp dir
        media_files = fetcher.download_media(script_data['search_terms'], target_dir=temp_dir)
        print(f"   ✅ Downloaded {len(media_files)} clips/images.")

        print("\n🎬 Scene 3: Sound... (Recording Audio)")
        audio_gen = AudioGenerator()
        audio_path = os.path.join(temp_dir, "narration.mp3")
        audio_file = audio_gen.generate_narrative(script_data['narrative_script'], output_file=audio_path)
        print(f"   ✅ Audio recorded at {audio_file}")

        print("\n🎬 Scene 4: Editing... (Assembling Video)")
        editor = VideoAssembler()
        final_video_path = os.path.join(result_dir, "final_video.mp4")
        editor.assemble_video(media_files, audio_file, final_video_path)
        
        print(f"\n✨ Success! Video saved to: {final_video_path}")
        
        # Cleanup
        print(f"   🧹 Cleaning up temp files in {temp_dir}...")
        shutil.rmtree(temp_dir)
        print("   ✨ Cleaned up.")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
