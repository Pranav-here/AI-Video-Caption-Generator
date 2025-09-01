# burn_captions.py

import os
import argparse
import subprocess
from shutil import which


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    ffmpeg_path: str | None = None,
    font: str | None = None,
    font_size: int | None = None,
    outline: int | None = 2,
    shadow: int | None = 0,
    crf: int = 20,
    preset: str = "medium",
) -> None:
    """
    Overlay SRT subtitles using ffmpeg's subtitles filter.
    Notes for Windows:
      Use forward slashes in the filter path to avoid escaping issues.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    if not os.path.isfile(srt_path):
        raise FileNotFoundError(f"SRT not found: {srt_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    ffmpeg = ffmpeg_path or which("ffmpeg") or "ffmpeg"
    # Filter expects a POSIX-like path. Convert backslashes to forward slashes.
    srt_for_filter = os.path.abspath(srt_path).replace("\\", "/")

    style_bits = []
    if font:
        style_bits.append(f"FontName={font}")
    if font_size:
        style_bits.append(f"FontSize={font_size}")
    if outline is not None:
        style_bits.append(f"Outline={outline}")
    if shadow is not None:
        style_bits.append(f"Shadow={shadow}")
    style_clause = ""
    if style_bits:
        style_clause = f":force_style='{','.join(style_bits)}'"

    filter_arg = f"subtitles={srt_for_filter}{style_clause}"

    cmd = [
        ffmpeg,
        "-y",  # overwrite
        "-i", os.path.abspath(video_path),
        "-vf", filter_arg,
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "copy",  # keep original audio
        os.path.abspath(output_path),
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Captioned video: {os.path.abspath(output_path)}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("video", help="Path to input video")
    p.add_argument("srt", help="Path to SRT file")
    p.add_argument("out", help="Path to output video")
    p.add_argument("--ffmpeg", default=None, help="Path to ffmpeg.exe if not on PATH")
    p.add_argument("--font", default=None, help="ASS font name, e.g., Arial")
    p.add_argument("--fontsize", type=int, default=None, help="Font size")
    p.add_argument("--outline", type=int, default=2, help="Outline thickness")
    p.add_argument("--shadow", type=int, default=0, help="Shadow size")
    p.add_argument("--crf", type=int, default=20, help="x264 CRF (lower is higher quality)")
    p.add_argument("--preset", default="medium", help="x264 preset (ultrafast to placebo)")
    args = p.parse_args()

    burn_subtitles(
        video_path=args.video,
        srt_path=args.srt,
        output_path=args.out,
        ffmpeg_path=args.ffmpeg,
        font=args.font,
        font_size=args.fontsize,
        outline=args.outline,
        shadow=args.shadow,
        crf=args.crf,
        preset=args.preset,
    )


if __name__ == "__main__":
    main()
