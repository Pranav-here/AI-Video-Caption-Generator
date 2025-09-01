# app.py
# AI Video Caption Generator

import os
import io
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import timedelta
from shutil import which

import streamlit as st
import torch
import whisper
import srt
from moviepy.editor import VideoFileClip


# ---------------- Utilities ----------------

@st.cache_resource(show_spinner=False)
def load_whisper_model(name: str = "base"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(name, device=device)
    return model, device


def extract_audio(video_path: str, out_wav: str) -> None:
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    with VideoFileClip(video_path) as clip:
        if clip.audio is None:
            raise RuntimeError("No audio track found in the video.")
        # 16 kHz mono PCM WAV for Whisper
        clip.audio.write_audiofile(
            out_wav,
            fps=16000,
            nbytes=2,
            codec="pcm_s16le",
            ffmpeg_params=["-ac", "1"],
            verbose=False,
            logger=None,
        )


def transcribe_audio(audio_path: str, model_name: str, language_hint: str | None):
    model, device = load_whisper_model(model_name)
    fp16 = device == "cuda"
    result = model.transcribe(audio_path, language=language_hint or None, fp16=fp16)
    return result


def to_srt_text(transcription_result: dict) -> str:
    segments = transcription_result.get("segments", []) or []
    subs = []
    for i, seg in enumerate(segments, start=1):
        subs.append(
            srt.Subtitle(
                index=i,
                start=timedelta(seconds=float(seg["start"])),
                end=timedelta(seconds=float(seg["end"])),
                content=seg["text"].strip(),
            )
        )
    return srt.compose(subs)


def ffmpeg_bin(custom_path: str | None) -> str:
    if custom_path:
        return custom_path
    return which("ffmpeg") or "ffmpeg"


def build_force_style(font: str | None, font_size: int | None, outline: int | None, shadow: int | None) -> str:
    """
    Build the ASS style string. We quote the whole value for safety.
    """
    parts = []
    if font:
        parts.append(f"FontName={font}")
    if font_size is not None:
        parts.append(f"FontSize={int(font_size)}")
    if outline is not None:
        parts.append(f"Outline={int(outline)}")
    if shadow is not None:
        parts.append(f"Shadow={int(shadow)}")
    if not parts:
        return ""
    return f":force_style='{','.join(parts)}'"


def burn_subtitles(
    video_path: str,
    srt_path: str,
    out_path: str,
    ffmpeg_path: str | None,
    font: str | None,
    font_size: int | None,
    outline: int | None,
    shadow: int | None,
    crf: int,
    preset: str,
) -> tuple[str, str]:
    """
    Hardsub SRT with ffmpeg. To avoid Windows filter parsing issues,
    we set cwd to the SRT directory and pass only the SRT basename in the filter.
    Returns (pretty_cmd_string, full_stderr_log).
    """
    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    srt_dir = str(Path(srt_path).parent)
    srt_file = Path(srt_path).name  # no drive colon
    style = build_force_style(font, font_size, outline, shadow)

    # subtitles filter: best to quote filename and style
    vf = f"subtitles=filename='{srt_file}'{style}"

    cmd = [
        ffmpeg_bin(ffmpeg_path),
        "-y",
        "-i", os.path.abspath(video_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "copy",
        os.path.abspath(out_path),
    ]

    # Run with cwd set to SRT directory so filename is resolved without drive colon
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=srt_dir)
    pretty_cmd = f"(cwd={srt_dir}) " + " ".join(cmd)
    stderr = proc.stderr or ""
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, pretty_cmd, output=proc.stdout, stderr=stderr)
    return pretty_cmd, stderr


def save_uploaded_video(uploaded, suffix: str = ".mp4") -> str:
    tmp_dir = tempfile.mkdtemp(prefix="caption_app_")
    path = os.path.join(tmp_dir, f"in{suffix}")
    with open(path, "wb") as f:
        f.write(uploaded.read())
    return path


def write_text_file(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------- UI ----------------

st.set_page_config(page_title="AI Video Caption Generator", layout="centered")
st.title("AI Video Caption Generator")
st.caption("Made by [pranavkuchibhotla.com](https://pranavkuchibhotla.com)")

with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox(
        "Whisper model",
        ["tiny", "base", "small", "medium", "large"],
        index=1,
        help="Larger models are slower but can be more accurate.",
    )
    language_hint = st.text_input(
        "Language hint (optional)",
        placeholder="en, te, hi, etc.",
        help="Leave blank to auto-detect.",
    )
    st.markdown("---")
    st.subheader("Subtitle style")
    font_name = st.text_input("Font name (optional)", value="")
    font_size = st.number_input("Font size", min_value=10, max_value=96, value=38, step=2)
    outline = st.number_input("Outline thickness", min_value=0, max_value=8, value=2, step=1)
    shadow = st.number_input("Shadow size", min_value=0, max_value=8, value=0, step=1)
    st.markdown("---")
    st.subheader("ffmpeg")
    ffmpeg_path = st.text_input("ffmpeg path (optional)", value="", help="If ffmpeg is not on PATH")
    crf = st.slider("x264 CRF (quality)", 16, 28, 20, help="Lower is higher quality")
    preset = st.selectbox(
        "x264 preset",
        ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow", "placebo"],
        index=5,
    )

st.markdown("Upload a video, then run the pipeline. You will see each step and outputs.")

uploaded = st.file_uploader(
    "Choose a video file",
    type=["mp4", "mov", "mkv", "avi", "mpeg", "mpeg4", "mpg"]
)
run = st.button("Run pipeline", disabled=uploaded is None)

if uploaded:
    st.caption("Input preview")
    uploaded.seek(0)
    st.video(uploaded)

if run and uploaded:
    try:
        # Save uploaded file to a temp dir
        uploaded.seek(0)
        input_suffix = Path(uploaded.name).suffix or ".mp4"
        video_path = save_uploaded_video(uploaded, suffix=input_suffix)
        temp_root = Path(video_path).parent
        audio_path = str(temp_root / "audio.wav")
        srt_path = str(temp_root / "captions.srt")
        out_video_path = str(temp_root / "captioned.mp4")

        # Step 1: Extract audio
        with st.status("Step 1 of 4, extract audio", expanded=True) as s1:
            st.write("Converting to 16 kHz mono WAV")
            t0 = time.time()
            extract_audio(video_path, audio_path)
            st.write(f"Audio written to: `{audio_path}`")
            st.write(f"Elapsed: {time.time() - t0:.1f}s")
            s1.update(label="Step 1 complete, audio extracted", state="complete")

        # Step 2: Transcribe
        with st.status("Step 2 of 4, transcribe", expanded=True) as s2:
            st.write(f"Model: {model_name}")
            t0 = time.time()
            result = transcribe_audio(audio_path, model_name=model_name, language_hint=language_hint.strip() or None)
            full_text = result.get("text", "").strip()
            st.write("Transcript:")
            st.text_area("Text", value=full_text, height=180)
            st.write(f"Elapsed: {time.time() - t0:.1f}s")
            s2.update(label="Step 2 complete, transcription done", state="complete")

        # Step 3: Generate SRT
        with st.status("Step 3 of 4, generate SRT", expanded=True) as s3:
            t0 = time.time()
            srt_text = to_srt_text(result)
            write_text_file(srt_path, srt_text)
            st.write(f"SRT saved to: `{srt_path}`")
            st.code(srt_text[:2000] + ("\n... truncated ..." if len(srt_text) > 2000 else ""), language="srt")
            st.download_button("Download SRT", data=srt_text.encode("utf-8"), file_name="captions.srt", mime="application/x-subrip")
            st.write(f"Elapsed: {time.time() - t0:.1f}s")
            s3.update(label="Step 3 complete, SRT ready", state="complete")

        # Step 4: Burn captions
        with st.status("Step 4 of 4, burn captions", expanded=True) as s4:
            t0 = time.time()
            try:
                cmd_str, stderr_text = burn_subtitles(
                    video_path=video_path,
                    srt_path=srt_path,
                    out_path=out_video_path,
                    ffmpeg_path=ffmpeg_path.strip() or None,
                    font=font_name.strip() or None,
                    font_size=int(font_size) if font_size else None,
                    outline=int(outline) if outline is not None else None,
                    shadow=int(shadow) if shadow is not None else None,
                    crf=int(crf),
                    preset=preset,
                )
                st.write("ffmpeg command:")
                st.code(cmd_str, language="bash")
                if stderr_text.strip():
                    st.write("ffmpeg log (stderr):")
                    st.code(stderr_text[-3000:], language="bash")
            except subprocess.CalledProcessError as e:
                st.error("ffmpeg failed while burning subtitles. See log below.")
                st.write("Command:")
                st.code(e.cmd, language="bash")
                if e.stderr:
                    st.code(e.stderr[-5000:], language="bash")
                raise

            st.write(f"Output video: `{out_video_path}`")
            st.write(f"Elapsed: {time.time() - t0:.1f}s")
            s4.update(label="Step 4 complete, captions burned", state="complete")

        st.success("All steps finished")
        st.subheader("Result preview")
        with open(out_video_path, "rb") as f:
            data = f.read()
        st.video(io.BytesIO(data))
        st.download_button("Download captioned video", data=data, file_name="captioned.mp4", mime="video/mp4")

    except subprocess.CalledProcessError:
        # Already surfaced detailed info above
        st.stop()
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
