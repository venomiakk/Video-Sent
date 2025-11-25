import datetime
from typing import Any
from fastapi.concurrency import run_in_threadpool
from app.utils.helpers import hash_url
from app.core.database import db
from .schemas import Transcription
from app.modules.v1.downloader.downloader import download_audio
from deepgram import (
    DeepgramClient,
)
from app.core.deepgram_secret import DEEPGRAM_SECRET
import logging
from pathlib import Path
import json

async def transcribe_video(url: str, model_name: str = "deepgram-nova-2") -> Any:
    '''
    Download and transcribe video from URL provided.\n
    Uses Deepgram's API for transcription.
    '''

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
    
    base, path, title = download_audio(url, filename_hash)
    deepgram_model_name = model_name[len("deepgram-"):] if model_name.startswith("deepgram-") else model_name

    try:
        deepgram = DeepgramClient(api_key=DEEPGRAM_SECRET)
        
        with open(path, 'rb') as audio_file:
            response = deepgram.listen.v1.media.transcribe_file(
                request=audio_file.read(),
                model=deepgram_model_name,
                smart_format=True,
                language="pl",
            )
            logging.info(f"Deepgram response: {response}")
    except Exception as e:
        logging.error(f"Deepgram transcription error: {e}")
        raise e
    
    transcription_text = response.results.channels[0].alternatives[0].transcript.strip()
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
    {"$setOnInsert": new_doc},      # if not found, insert this
    upsert=True                 # perform upsert if not found
)
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
