import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.modules.v1.transcription.service import transcribe_video
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime

client = TestClient(app)

@pytest.mark.asyncio
async def test_transcribe_video_cached(mock_db):
    with patch("app.modules.v1.transcription.service.db", mock_db):
        mock_db.transcriptions.find_one.return_value = {
            "_id": "existing_id",
            "transcription": "Cached text",
            "link_hash": "hash",
            "model": "deepgram-nova-2",
            "url": "http://yt.com",
            "title": "Title",
            "created_at": datetime.now()
        }
        
        result = await transcribe_video("http://yt.com")
        assert result.transcription == "Cached text"

@pytest.mark.asyncio
async def test_transcribe_video_new_and_unlink_error(mock_db):
    """Pokrywa sukces transkrypcji + błąd przy usuwaniu pliku (unlink)"""
    with patch("app.modules.v1.transcription.service.db", mock_db), \
         patch("app.modules.v1.transcription.service.download_audio") as mock_dl, \
         patch("app.modules.v1.transcription.service.DeepgramClient") as mock_dg, \
         patch("builtins.open", new_callable=MagicMock), \
         patch("app.modules.v1.transcription.service.Path") as MockPath: 
        
        mock_db.transcriptions.find_one.side_effect = [
            None, 
            {
                "_id": "new_id", 
                "transcription": "New text", 
                "link_hash": "hash", 
                "title": "T", 
                "url": "http://yt.com", 
                "model": "deepgram-nova-2", 
                "created_at": datetime.now()
            } 
        ]
        
        mock_dl.return_value = ("hash", "dummy_path", "Video Title")
        
        mock_response = MagicMock()
        mock_response.results.channels[0].alternatives[0].transcript = " New text "
        mock_dg.return_value.listen.v1.media.transcribe_file.return_value = mock_response
        
        MockPath.return_value.unlink.side_effect = Exception("Unlink Fail")
        
        result = await transcribe_video("http://yt.com")
        assert result.transcription == "New text"

@pytest.mark.asyncio
async def test_transcribe_deepgram_error(mock_db):
    """Pokrywa błąd API Deepgram"""
    with patch("app.modules.v1.transcription.service.download_audio"), \
         patch("app.modules.v1.transcription.service.DeepgramClient") as mock_dg, \
         patch("app.modules.v1.transcription.service.db", mock_db):
        
        mock_db.transcriptions.find_one.return_value = None
        mock_dg.side_effect = Exception("Deepgram Connection Fail")
        
        with pytest.raises(Exception):
            await transcribe_video("http://yt.com")

def test_transcription_endpoint():
    with patch("app.modules.v1.transcription.router.transcribe_video", new_callable=AsyncMock) as mock_svc:
        mock_svc.return_value = {"id": "123", "transcription": "abc"}
        response = client.post("/api/v1/transcribe/process", json={"url": "http://yt.com", "model": "deepgram-nova-2"})
        assert response.status_code == 200