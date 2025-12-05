import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.modules.v1.sentiment.service import analyze
from fastapi.testclient import TestClient
from app.main import app
from bson import ObjectId
from groq import APIError 
import json

client = TestClient(app)

@pytest.mark.asyncio
async def test_analyze_invalid_id():
    result = await analyze("invalid-object-id")
    assert result == []

@pytest.mark.asyncio
async def test_analyze_transcription_db_error(mock_db):
    """Pokrycie błędu przy fetchowaniu transkrypcji"""
    with patch("app.modules.v1.sentiment.service.db", mock_db):
        mock_db.transcriptions.find_one.side_effect = Exception("DB Fail")
        result = await analyze(str(ObjectId()))
        assert result == []

@pytest.mark.asyncio
async def test_analyze_transcription_key_error(mock_db):
    """Pokrycie błędu przy dostępie do klucza"""
    with patch("app.modules.v1.sentiment.service.db", mock_db):
        
        mock_db.transcriptions.find_one.return_value = {"other": "field"}
        mock_db.sentiment_analysis.find_one.return_value = None
        
        result = await analyze(str(ObjectId()))
        assert result == []

@pytest.mark.asyncio
async def test_analyze_api_error(mock_db):
    """Pokrycie groq.APIError"""
    oid = str(ObjectId())
    with patch("app.modules.v1.sentiment.service.db", mock_db), \
         patch("app.modules.v1.sentiment.service.Groq") as MockGroq:
        
        mock_db.transcriptions.find_one.return_value = {"transcription": "Text"}
        mock_db.sentiment_analysis.find_one.return_value = None
        
        error_mock = APIError(message="API Error", request=MagicMock(), body=None)
        
        MockGroq.return_value.chat.completions.create.side_effect = error_mock
        
        result = await analyze(oid)
        assert result is None

@pytest.mark.asyncio
async def test_analyze_json_error(mock_db):
    """Pokrycie json.JSONDecodeError"""
    oid = str(ObjectId())
    with patch("app.modules.v1.sentiment.service.db", mock_db), \
         patch("app.modules.v1.sentiment.service.Groq") as MockGroq:
        
        mock_db.transcriptions.find_one.return_value = {"transcription": "Text"}
        mock_db.sentiment_analysis.find_one.return_value = None
        
        mock_chat = MockGroq.return_value.chat.completions.create.return_value
        mock_chat.choices[0].message.content = "Not Valid JSON {"
        
        result = await analyze(oid)
        assert result is None

@pytest.mark.asyncio
async def test_analyze_generic_exception(mock_db):
    """Pokrycie ogólnego Exception"""
    oid = str(ObjectId())
    with patch("app.modules.v1.sentiment.service.db", mock_db), \
         patch("app.modules.v1.sentiment.service.Groq") as MockGroq:
        
        mock_db.transcriptions.find_one.return_value = {"transcription": "Text"}
        mock_db.sentiment_analysis.find_one.return_value = None

        MockGroq.return_value.chat.completions.create.side_effect = RuntimeError("Something bad")
        
        result = await analyze(oid)
        assert result is None

@pytest.mark.asyncio
async def test_analyze_success(mock_db):
    oid = str(ObjectId())
    mock_json = {"overall_summary": "S", "results": {}}
    
    with patch("app.modules.v1.sentiment.service.db", mock_db), \
         patch("app.modules.v1.sentiment.service.Groq") as MockGroq:
        mock_db.transcriptions.find_one.return_value = {"transcription": "Text"}
        mock_db.sentiment_analysis.find_one.return_value = None
        
        mock_chat = MockGroq.return_value.chat.completions.create.return_value
        mock_chat.choices[0].message.content = json.dumps(mock_json)
        
        result = await analyze(oid)
        assert result["overall_summary"] == "S"

@pytest.mark.asyncio
async def test_analyze_save_db_error(mock_db):
    """Pokrycie błędu zapisu do bazy (save_results_to_db)"""
    oid = str(ObjectId())
    mock_json = {"overall_summary": "S", "results": {}}
    
    with patch("app.modules.v1.sentiment.service.db", mock_db), \
         patch("app.modules.v1.sentiment.service.Groq") as MockGroq:
        mock_db.transcriptions.find_one.return_value = {"transcription": "Text"}
        mock_db.sentiment_analysis.find_one.return_value = None
        
        mock_chat = MockGroq.return_value.chat.completions.create.return_value
        mock_chat.choices[0].message.content = json.dumps(mock_json)
        
        mock_db.sentiment_analysis.insert_one.side_effect = Exception("DB Insert Fail")
        
        result = await analyze(oid)

        assert result["overall_summary"] == "S"

def test_sentiment_endpoint():
    with patch("app.modules.v1.sentiment.router.analyze", new_callable=AsyncMock) as mock_an:
        mock_an.return_value = {"ok": 1}
        response = client.post("/api/v1/sentiment/analyze/123")
        assert response.status_code == 200