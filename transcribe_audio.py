# transcribe_audio.py

import argparse
import torch
import whisper


def transcribe(audio_path: str, model_name: str = "base", language: str | None = None) -> dict:
    """
    Run Whisper on a WAV file and return the raw result dict.
    """
    if not torch.cuda.is_available():
        device = "cpu"
        fp16 = False
    else:
        device = "cuda"
        fp16 = True

    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(audio_path, language=language, fp16=fp16)
    print("\nTranscription:\n", result.get("text", "").strip())
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("audio", help="Path to WAV file")
    p.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    p.add_argument("--lang", default=None, help="Language hint, e.g., 'en', 'te', 'hi'")
    args = p.parse_args()
    transcribe(args.audio, model_name=args.model, language=args.lang)


if __name__ == "__main__":
    main()
