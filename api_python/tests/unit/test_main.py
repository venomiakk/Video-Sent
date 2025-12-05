import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from app.core.exceptions import AppException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
         patch("app.main.analyze", new_callable=AsyncMock) as mock_an:
        
        mock_tr.return_value = mock_trans
        mock_an.return_value = {"res": "ults"}
        
        response = client.post("/api/v1/process", json={"url": "http://yt.com"})
        assert response.status_code == 200

# --- Testy Handlerów Wyjątków ---

def test_app_exception_handler():
    @app.get("/test_app_exc")
    def trigger_app_error():
        raise AppException("Custom Error", status_code=418, detail={"foo": "bar"})

    c = TestClient(app)
    response = c.get("/test_app_exc")
    
    assert response.status_code == 418
    data = response.json()
    assert data["detail"] == "Custom Error"
    assert data["meta"] == {"foo": "bar"}

def test_http_exception_handler():
    @app.get("/test_http_exc")
    def trigger_http_error():
        raise StarletteHTTPException(status_code=403, detail="Forbidden Access")

    c = TestClient(app)
    response = c.get("/test_http_exc")
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden Access"

def test_global_exception_handler():
    @app.get("/test_global_exc")
    def trigger_global_error():
        raise ValueError("Unexpected Crash")

    c = TestClient(app, raise_server_exceptions=False)
    
    response = c.get("/test_global_exc")
    
    assert response.status_code == 500
    data = response.json()
    assert data["detail"] == "Internal Server Error"
    assert "meta" in data

def test_validation_exception_handler():
    from pydantic import BaseModel
    class Item(BaseModel):
        name: str

    @app.post("/test_validation")
    def trigger_validation(item: Item):
        return {"ok": True}

    c = TestClient(app)

    response = c.post("/test_validation", json={})
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"] == "Validation Error"
    assert isinstance(data["meta"]["errors"], list)

    assert data["meta"]["errors"][0]["field"] == "body.name"