import whisper
import srt
from datetime import timedelta


def transcribe(audio_path):
    model=whisper.load_model("base")
    result=model.transcribe(audio_path)
    return result


def convert_to_srt(transcription_result):
    # Whisper puts detailed timing in 'segments', a list of dicts.
    # Each segment has 'start' (sec), 'end' (sec), and 'text'.
    segments = transcription_result['segments']
    subtitles = []
    for i, seg in enumerate(segments):
        subtitle = srt.Subtitle(
            index=i+1,
            start=timedelta(seconds=seg['start']),
            end=timedelta(seconds=seg['end']),
            content=seg['text'].strip()
        )

        subtitles.append(subtitle)

    return srt.compose(subtitles)