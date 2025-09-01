import subprocess
import os


def burn_subtitles(video_path, srt_relative_path, output_path, ffmpeg_path):
    # Get absolute paths for audio and video
    video_full = os.path.abspath(video_path)
    output_full = os.path.abspath(output_path)

    # Use the relative path for subtitles exactly as it worked in your manual command
    # Make sure the wkdir is project dir
    command = f'"{ffmpeg_path}" -i "{video_full}" -vf "subtitles={srt_relative_path}" "{output_full}"'

    print("Running command: ")
    print(command)

    try:
        subprocess.run(command, shell=True, check=True)
        print(f"Video with burned-in captions generated: {output_full}")
    except subprocess.CalledProcessError as e:
        print(f"Error burning subtitles: {e}")


if __name__=='__main__':
    ffmpeg_path = "C:\\ffmpeg\\ffmpeg-7.1.1-essentials_build\\bin\\ffmpeg.exe"

    # Use relative path for the subtitles 
    video_file = "videos/sample_video.mp4"
    srt_relative_path = "captions/output.srt"
    output_video = "videos/output_video.mp4"

    burn_subtitles(video_file, srt_relative_path, output_video, ffmpeg_path)