import datetime
import app.modules.v1.downloader.downloader as downloader
from pathlib import Path
from starlette.concurrency import run_in_threadpool
from .utils import hash_url
from typing import Any, Dict
from app.core.database import db
from .schemas import Transcription

# Load Whisper models lazily to avoid heavy work at import time (fixes uvicorn reload issues)
_models: Dict[str, Any] = {}


def get_model(name: str = "base") -> Any:
    """Return a cached whisper model, loading it on first use."""
    if name in _models:
        return _models[name]

    # Import inside function to avoid importing whisper at module import time
    import whisper

    _models[name] = whisper.load_model(name)
    return _models[name]


async def transcribe_video(url: str, model_name: str = "base", **whisper_opts) -> Transcription:
    """Download audio from `url` and transcribe it using Whisper.
    Returns a Transcription object.
    """
    filename_hash = hash_url(str(url))

    doc = await db.transcriptions.find_one(
        {
            "link_hash": filename_hash,
            "model": model_name
        })

    if doc:
        if "transcription" in doc:
            return doc

    base, path, title = downloader.download_audio(url, filename_hash)

    model = get_model(model_name)
    # whisper expects a path-like or filename string
    result = model.transcribe(str(path), **whisper_opts)
    transcription_text = result.get("text", "").strip() if isinstance(result, dict) else ""

    # use timezone-aware UTC datetime for storage and include a human-friendly ISO string
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    new_doc = {
        "link_hash": filename_hash,
        "url": str(url),
        "title": title,
        "transcription": transcription_text,
        "model": model_name,
        "created_at": now,
    }
    await db.transcriptions.update_one(
    {"link_hash": filename_hash, "model": model_name},       # ← filtr (który dokument chcemy zaktualizować)
    {"$setOnInsert": new_doc},      # ← co wstawić, jeśli dokument nie istnieje
    upsert=True                 # ← jeśli nie ma dokumentu, wstaw nowy
)

    # Attempt to remove the audio file asynchronously so we don't block the event loop.
    # We ignore errors here (e.g. file already removed or locked) but you can add logging.
    try:
        await run_in_threadpool(lambda: Path(path).unlink(missing_ok=True))
    except Exception:
        pass

    return new_doc
