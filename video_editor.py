from moviepy import VideoFileClip, ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip, vfx
import os
import json

class VideoAssembler:
    def __init__(self):
        self.target_resolution = (1080, 1920) # Vertical 9:16
        # Using absolute path to ensure MoviePy/ImageMagick finds it
        self.font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" 
        self.font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

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
                    original_clip = ImageClip(media_path).with_duration(duration)
                    # Smart Crop Logic
                    w, h = original_clip.size
                    if w/h > 1080/1920:
                        visual_clip = original_clip.with_effects([vfx.Resize(height=1920)])
                        visual_clip = visual_clip.with_effects([vfx.Crop(width=1080, height=1920, x_center=visual_clip.w/2)])
                    else:
                        visual_clip = original_clip.with_effects([vfx.Resize(width=1080)])
                        visual_clip = visual_clip.with_effects([vfx.Crop(width=1080, height=1920, y_center=visual_clip.h/2)])
                        
                elif media_path.endswith(('.mp4', '.mov')):
                    original_clip = VideoFileClip(media_path)
                    if original_clip.duration < duration:
                        original_clip = original_clip.with_effects([vfx.Loop(duration=duration)])
                    else:
                        original_clip = original_clip.subclipped(0, duration)
                    
                    # Smart Crop Logic
                    w, h = original_clip.size
                    if w/h > 1080/1920:
                        visual_clip = original_clip.with_effects([vfx.Resize(height=1920)])
                        visual_clip = visual_clip.with_effects([vfx.Crop(width=1080, height=1920, x_center=visual_clip.w/2)])
                    else:
                         visual_clip = original_clip.with_effects([vfx.Resize(width=1080)])
                         visual_clip = visual_clip.with_effects([vfx.Crop(width=1080, height=1920, y_center=visual_clip.h/2)])
            else:
                 visual_clip = ColorClip(size=self.target_resolution, color=(0,0,0), duration=duration)

            visual_clip = visual_clip.with_audio(audio_clip)

            # 3. Dynamic Subtitles (YouTube Shorts Style)
            captions = []
            
            if subs_path and os.path.exists(subs_path):
                try:
                    with open(subs_path, 'r') as f:
                        processed_subs = json.load(f)
                    
                    for sub in processed_subs:
                        word = sub['word']
                        start = sub['start']
                        end = sub['end']
                        duration_sub = end - start
                        
                        if duration_sub < 0.1: duration_sub = 0.1

                        txt_clip = TextClip(
                            text=word.upper(), 
                            font_size=105, 
                            color='yellow', 
                            font=self.font_bold, 
                            stroke_color='black', 
                            stroke_width=5, 
                            size=(1000, None), 
                            method='caption',
                            text_align='center'
                        )
                        txt_clip = txt_clip.with_start(start).with_duration(duration_sub).with_position('center')
                        captions.append(txt_clip)
                        
                except Exception as e:
                    print(f"   ⚠️ Subtitle JSON Error: {e}")

            # 4. Emphasis Text Overlay (from Agent)
            top_overlay = scene.get('text_overlay', "")
            if top_overlay:
                 try:
                    title_clip = TextClip(
                        text=top_overlay.upper(),
                        font_size=90, 
                        color='white', 
                        font=self.font_bold,
                        stroke_color='black',
                        stroke_width=6,
                        size=(self.target_resolution[0] - 100, None),
                        method='caption',
                        text_align='center'
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
