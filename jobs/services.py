import assemblyai as aai

from .appsettings import get_assemblyai_api_key

ASSEMBLYAI_API_KEY_PLACEHOLDERS = frozenset({"", "your_assemblyai_api_key_here"})


def assemblyai_configured() -> bool:
    key = get_assemblyai_api_key()
    return bool(key) and key not in ASSEMBLYAI_API_KEY_PLACEHOLDERS


def _make_aai_config(
    *,
    speaker_labels: bool = False,
    webhook_url: str = "",
    webhook_auth_token: str = "",
    language_code: str = "",
) -> aai.TranscriptionConfig:
    # language_detection and language_code are mutually exclusive in AssemblyAI
    use_auto_detect = not language_code
    return aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.best,
        language_detection=use_auto_detect,
        language_code=language_code if language_code else None,
        speaker_labels=speaker_labels,
        webhook_url=webhook_url or None,
        webhook_auth_header_name="Authorization" if webhook_auth_token else None,
        webhook_auth_header_value=f"Bearer {webhook_auth_token}" if webhook_auth_token else None,
    )


def _parse_transcript_result(
    transcript: aai.Transcript,
    speaker_labels: bool = False,
) -> tuple[str, float, list[dict], str]:
    if transcript.status == aai.TranscriptStatus.error:
        raise RuntimeError(transcript.error)
    if not transcript.text:
        raise RuntimeError("No transcript text returned by AssemblyAI.")

    duration = float(transcript.audio_duration or 0.0)
    sentences: list[dict] = []
    try:
        if speaker_labels and transcript.utterances:
            for u in transcript.utterances:
                sentences.append({"text": u.text, "start": u.start, "end": u.end, "speaker": u.speaker})
        else:
            for s in (transcript.sentences or []):
                sentences.append({"text": s.text, "start": s.start, "end": s.end, "speaker": None})
    except Exception:
        pass

    return transcript.text, duration, sentences, ""


def transcribe_file(
    file_path: str,
    *,
    speaker_labels: bool = False,
    language_code: str = "",
) -> tuple[str, float, list[dict], str]:
    """Synchronous transcription. Blocks until AssemblyAI returns."""
    if not assemblyai_configured():
        raise RuntimeError(
            "AssemblyAI API key is missing. Add one on the Settings page — get a key at "
            "https://www.assemblyai.com/dashboard."
        )

    aai.settings.api_key = get_assemblyai_api_key()
    config = _make_aai_config(
        speaker_labels=speaker_labels,
        language_code=language_code,
    )
    transcript = aai.Transcriber().transcribe(file_path, config=config)
    return _parse_transcript_result(transcript, speaker_labels=speaker_labels)


def submit_file_async(
    file_path: str,
    *,
    speaker_labels: bool = False,
    webhook_url: str = "",
    webhook_auth_token: str = "",
    language_code: str = "",
) -> str:
    """Submit file for async transcription. Returns AssemblyAI transcript_id immediately."""
    if not assemblyai_configured():
        raise RuntimeError("AssemblyAI API key is not configured.")

    aai.settings.api_key = get_assemblyai_api_key()
    config = _make_aai_config(
        speaker_labels=speaker_labels,
        webhook_url=webhook_url,
        webhook_auth_token=webhook_auth_token,
        language_code=language_code,
    )
    transcript = aai.Transcriber().submit(file_path, config)
    return transcript.id


def fetch_transcript_by_id(
    transcript_id: str,
    *,
    speaker_labels: bool = False,
) -> tuple[str, float, list[dict], str]:
    """Fetch a completed transcript from AssemblyAI by ID."""
    aai.settings.api_key = get_assemblyai_api_key()
    transcript = aai.Transcript.get_by_id(transcript_id)
    return _parse_transcript_result(transcript, speaker_labels=speaker_labels)
