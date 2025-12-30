import asyncio
import edge_tts
import os
import json

class AudioGenerator:
    def __init__(self):
        self.voice = "en-US-ChristopherNeural"
        self.rate = "+15%" # Slightly faster for Shorts

    async def _generate_with_subs(self, text: str, output_file: str):
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        subtitles = []
        
        with open(output_file, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # chunk layout: {type, offset, duration, text}
                    # offset and duration are in 100ns units (ticks)
                    # 1s = 10,000,000 ticks
                    start = chunk["offset"] / 1e7
                    duration = chunk["duration"] / 1e7
                    subtitles.append({
                        "start": start,
                        "end": start + duration,
                        "word": chunk["text"]
                    })
        return subtitles

    def generate_narrative(self, text: str, output_file: str = "narration.mp3"):
        """
        Generates audio AND word-level subtitles.
        Returns: (audio_path, subtitles_json_path)
        """
        print(f"   🎙️ Generating audio (Voice: {self.voice})...")
        try:
            subs_file = output_file.replace(".mp3", ".json")
            subtitles = asyncio.run(self._generate_with_subs(text, output_file))
            
            with open(subs_file, "w") as f:
                json.dump(subtitles, f)
                
            return os.path.abspath(output_file), os.path.abspath(subs_file)
        except Exception as e:
            print(f"   ❌ Error generating audio: {e}")
            raise
