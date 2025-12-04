import pytest
from app.core.config import settings, Settings
from app.core.database import init_indexes
from app.core.exceptions import AppException, DownloadError
from app.utils.helpers import hash_url
from app.core.sentiment_keywords import ASPECT_KEYWORDS
from unittest.mock import patch, AsyncMock

def test_config():
    assert settings.APP_NAME == "Video Sentiment Analyzer"
    assert settings.VERSION == "0.1.0"
    
def test_sentiment_keywords():
    assert "bateria" in ASPECT_KEYWORDS
    assert "aparat" in ASPECT_KEYWORDS
    assert isinstance(ASPECT_KEYWORDS["cena"], list)

@pytest.mark.asyncio
async def test_init_indexes(mock_db):
    with patch("app.core.database.db", mock_db):
        await init_indexes()
        assert mock_db.transcriptions.create_index.call_count == 2
        mock_db.transcriptions.create_index.assert_any_call("link_hash")

def test_app_exception():
    exc = AppException("Error message", status_code=418, detail={"foo": "bar"})
    assert exc.status_code == 418
    data = exc.to_dict()
    assert data["detail"] == "Error message"
    assert data["meta"] == {"foo": "bar"}

def test_app_exception_defaults():
    exc = AppException("Error")
    assert exc.status_code == 400
    assert "meta" not in exc.to_dict()

def test_download_error():
    exc = DownloadError("Download failed")
    assert exc.status_code == 500
    assert exc.message == "Download failed"

def test_hash_url():
    url = "https://example.com"
    hashed = hash_url(url)
    assert isinstance(hashed, str)
    assert len(hashed) == 64  