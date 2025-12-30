from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip, vfx
import os
import json

class VideoAssembler:
    def __init__(self):
        self.target_resolution = (1080, 1920) # Vertical 9:16
        # Using absolute path to ensure MoviePy/ImageMagick finds it
        self.font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" 

    def assemble_video_from_timeline(self, timeline: list, media_paths: list, audio_data: list, output_path: str):
        """
        Assembles video based on the structured timeline.
        media_paths[i]: path to video/image
        audio_data[i]: tuple (audio_path, subtitles_path)
        """
        final_clips = []
        
        for i, scene in enumerate(timeline):
            media_path = media_paths[i]
            # Unpack audio data
            if isinstance(audio_data[i], tuple):
                audio_path, subs_path = audio_data[i]
            else:
                audio_path = audio_data[i]
                subs_path = None

            # 1. Load Audio
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # 2. Visual Clip
            visual_clip = None
            if media_path and os.path.exists(media_path):
                if media_path.endswith(('.jpg', '.jpeg', '.png')):
                    visual_clip = ImageClip(media_path).with_duration(duration)
                    visual_clip = visual_clip.with_effects([vfx.Resize(new_size=self.target_resolution)]) 
                elif media_path.endswith(('.mp4', '.mov')):
                    visual_clip = VideoFileClip(media_path)
                    if visual_clip.duration < duration:
                        visual_clip = visual_clip.with_effects([vfx.Loop(duration=duration)])
                    else:
                        visual_clip = visual_clip.subclipped(0, duration)
                    visual_clip = visual_clip.with_effects([vfx.Resize(new_size=self.target_resolution)])
            else:
                 visual_clip = ColorClip(size=self.target_resolution, color=(0,0,0), duration=duration)

            visual_clip = visual_clip.with_audio(audio_clip)

            # 3. Scene-Based Subtitles
            # Display the full script text for this scene at the bottom
            captions = []
            
            # Get the script text for this scene
            script_text = scene.get('script', '')
            
            if script_text:
                try:
                    # Create subtitle with the full script text
                    subtitle = TextClip(
                        text=script_text,
                        font_size=60,
                        color='white',
                        font=self.font,
                        stroke_color='black',
                        stroke_width=4,
                        size=(self.target_resolution[0] - 120, None),  # Leave margins
                        method='caption',
                        align='center'
                    )
                    # Position at bottom with safe margin (Y=1500 leaves ~420px from bottom)
                    subtitle = subtitle.with_position(('center', 1500)).with_duration(duration)
                    captions.append(subtitle)
                except Exception as e:
                    print(f"   ⚠️ Subtitle Error: {e}")

            # 4. Fallback / Emphasis Text Overlay (from Agent)
            # If the user requested a specific "Text Overlay" in the prompt, let's show it 
            # as a Title at the top, separate from captions.
            top_overlay = scene.get('text_overlay', "")
            if top_overlay:
                 try:
                    title_clip = TextClip(
                        text=top_overlay,
                        font_size=90, 
                        color='white', 
                        font=self.font,
                        stroke_color='black',
                        stroke_width=4,
                        size=(self.target_resolution[0] - 100, None),
                        method='caption'
                    )
                    title_clip = title_clip.with_position(('center', 200)).with_duration(duration)
                    captions.append(title_clip)
                 except Exception as e:
                    print(f"   ⚠️ Title Error: {e}")

            # Composite everything
            if captions:
                visual_clip = CompositeVideoClip([visual_clip, *captions])

            final_clips.append(visual_clip)

        # Concatenate
        final_video = concatenate_videoclips(final_clips, method="compose")
        final_video.write_videofile(output_path, fps=24)
