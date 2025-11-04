import datetime
import app.modules.v1.downloader.downloader as downloader
from pathlib import Path
from starlette.concurrency import run_in_threadpool
from app.utils.helpers import hash_url
from typing import Any, Dict
from app.core.database import db
from .schemas import Transcription

_models: Dict[str, Any] = {}


def get_model(name: str = "base") -> Any:
    """Return a cached whisper model, loading it on first use."""
    if name in _models:
        return _models[name]

    import whisper

    _models[name] = whisper.load_model(name)
    return _models[name]


async def transcribe_video(url: str, model_name: str = "whisperpy-base", **whisper_opts) -> Transcription:
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
            doc["_id"] = str(doc["_id"])
            return Transcription(**doc)

    base, path, title = downloader.download_audio(url, filename_hash)
    whisper_model_name = model_name[len("whisperpy-"):] if model_name.startswith("whisperpy-") else model_name
    model = get_model(whisper_model_name)
    result = model.transcribe(str(path), **whisper_opts)
    transcription_text = result.get("text", "").strip() if isinstance(result, dict) else ""

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
    {"link_hash": filename_hash, "model": model_name},       # filtr
    {"$setOnInsert": new_doc},      # if not found, insert new_doc
    upsert=True                 # perform upsert if not found
)

    # Attempt to remove the audio file asynchronously 
    try:
        await run_in_threadpool(lambda: Path(path).unlink(missing_ok=True))
    except Exception:
        pass
    
    inserted_doc = await db.transcriptions.find_one(
        {
            "link_hash": filename_hash,
            "model": model_name
        }
    )
    inserted_doc["_id"] = str(inserted_doc["_id"])
    return Transcription(**inserted_doc)
