# generate_srt.py

import os
import argparse
from datetime import timedelta
import torch
import whisper
import srt


def _transcribe(audio_path: str, model_name: str = "base", language: str | None = None) -> dict:
    if not torch.cuda.is_available():
        device = "cpu"
        fp16 = False
    else:
        device = "cuda"
        fp16 = True
    model = whisper.load_model(model_name, device=device)
    return model.transcribe(audio_path, language=language, fp16=fp16)


def convert_to_srt(transcription_result: dict) -> str:
    """
    Build SRT text from Whisper segments.
    """
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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("audio", help="Path to WAV")
    p.add_argument("srt_out", help="Path to output SRT (e.g., captions/output.srt)")
    p.add_argument("--model", default="base", help="Whisper model size")
    p.add_argument("--lang", default=None, help="Language hint")
    args = p.parse_args()

    os.makedirs(os.path.dirname(args.srt_out), exist_ok=True)
    result = _transcribe(args.audio, model_name=args.model, language=args.lang)
    srt_text = convert_to_srt(result)

    with open(args.srt_out, "w", encoding="utf-8") as f:
        f.write(srt_text)
    print(f"SRT written: {os.path.abspath(args.srt_out)}")


if __name__ == "__main__":
    main()
