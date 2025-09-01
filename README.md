# AI Video Caption Generator

A minimal Streamlit app that turns a video into a captioned video with hard subtitles. The app:
- Extracts audio from the uploaded video
- Transcribes speech with OpenAI Whisper
- Generates an SRT subtitle file
- Burns the subtitles into the video using ffmpeg
- Lets you preview and download the SRT and the captioned MP4

This runs locally, nothing is sent to remote services by the app itself.

## Requirements
- Python 3.10 or newer
- ffmpeg installed and available on PATH, or provide its path in the UI
- GPU is optional, Whisper will use CPU if CUDA is not available

## Quick start with `uv`
```bash
# Create and activate a local virtual environment
uv init
# Linux or macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Install dependencies
uv add streamlit moviepy openai-whisper srt torch
```

> Note: For Torch, install the build that matches your OS and CUDA support if you want GPU acceleration. CPU-only also works.

## Run
```bash
uv run streamlit run app.py
```

## Usage
1. Upload a video file in the UI
2. Run the pipeline
3. Review the transcript and SRT
4. Download the SRT or the captioned video

## Controls
- Whisper model size (tiny, base, small, medium, large)
- Optional language hint
- Subtitle style (font name, font size, outline, shadow)
- ffmpeg path override, CRF, and x264 preset
