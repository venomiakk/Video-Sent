import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from app.core.exceptions import AppException

client = TestClient(app)

def test_lifespan(mock_db):
    """Testuje startup i shutdown (lifespan)"""
    with patch("app.main.init_indexes", new_callable=AsyncMock) as mock_init:

        with TestClient(app) as c:
            response = c.get("/")
            assert response.status_code == 200
        
        mock_init.assert_called_once()

@pytest.mark.asyncio
async def test_process_v1_legacy():
    mock_trans = MagicMock()
    mock_trans.id = "123"
    mock_trans.link_hash = "hash123"
    mock_trans.url = "http://youtube.com"
    mock_trans.title = "Test"
    mock_trans.transcription = "text"
    mock_trans.model = "deepgram-nova-2"
    mock_trans.created_at = datetime.now()
    
    with patch("app.main.transcribe_video", new_callable=AsyncMock) as mock_tr, \
         patch("app.main.analyze_sentiment", new_callable=AsyncMock) as mock_an:
        
        mock_tr.return_value = mock_trans
        mock_an.return_value = {"res": "ults"}
        
        response = client.post("/api/v1/process", json={"url": "http://yt.com"})
        assert response.status_code == 200

def test_app_exception_handler():
    @app.get("/test_exception")
    def trigger_error():
        raise AppException("Custom Error", status_code=418, detail={"foo": "bar"})

    c = TestClient(app)
    response = c.get("/test_exception")
    
    assert response.status_code == 418
    data = response.json()
    assert data["detail"] == "Custom Error"
    assert data["meta"] == {"foo": "bar"}