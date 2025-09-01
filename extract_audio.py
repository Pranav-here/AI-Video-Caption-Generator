# extract_audio.py

import os
import argparse
from moviepy.editor import VideoFileClip


def extract_audio(video_path: str, output_audio_path: str) -> None:
    """
    Pull audio from a video and write a 16 kHz mono WAV.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

    # Use context manager so resources get closed properly
    with VideoFileClip(video_path) as clip:
        if clip.audio is None:
            print("No audio track found in the video.")
            return
        # 16 kHz mono PCM WAV plays nicest with Whisper
        clip.audio.write_audiofile(
            output_audio_path,
            fps=16000,
            nbytes=2,
            codec="pcm_s16le",
            ffmpeg_params=["-ac", "1"],
            verbose=False,
            logger=None,
        )
    print(f"Audio extracted: {os.path.abspath(output_audio_path)}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video", help="Path to input video")
    p.add_argument("audio_out", help="Path to output WAV (e.g., audio/sample_audio.wav)")
    args = p.parse_args()
    extract_audio(args.video, args.audio_out)


if __name__ == "__main__":
    main()
