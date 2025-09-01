from moviepy.editor import VideoFileClip
import os


# Step 1: Extract audio from the video and save it somewhere
def extract_audio(video_path, output_audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        if audio:
            audio.write_audiofile(output_audio_path)
            print(f"Audio extracted successfully: {output_audio_path}")
        else:
            print(f"No audio tract found in the video")
    
    except Exception as e:
        print(f"[!] There was an error extracting the audio:  {e}")