import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from app.socketio_handler import (
    emit_step, 
    process_video_analysis, 
    start_analysis, 
    get_analyses,
    connect,
    disconnect
)
from datetime import datetime

@pytest.mark.asyncio
async def test_emit_step():
    mock_sio = AsyncMock()
    with patch("app.socketio_handler.sio", mock_sio):
        await emit_step("sid1", "aid1", "step1", "status", "msg")
        mock_sio.emit.assert_called_with(
            'analysis_step', 
            {'analysis_id': 'aid1', 'step': {'step': 'step1', 'status': 'status', 'message': 'msg', 'timestamp': ANY}}, 
            room='sid1'
        )

@pytest.mark.asyncio
async def test_process_video_analysis_success(mock_db):
    mock_sio = AsyncMock()
    
    mock_transcription = MagicMock()
    mock_transcription.id = "tid1"
    mock_transcription.transcription = "text"
    mock_transcription.title = "title"
    
    mock_sentiment = {"overall_summary": "good", "results": {}}
    
    with patch("app.socketio_handler.sio", mock_sio), \
         patch("app.socketio_handler.db", mock_db), \
         patch("app.socketio_handler.transcribe_video", new_callable=AsyncMock) as mock_tr, \
         patch("app.socketio_handler.analyze", new_callable=AsyncMock) as mock_an:
        
        mock_db.analyses.insert_one.return_value.inserted_id = "aid1"
        mock_tr.return_value = mock_transcription
        mock_an.return_value = mock_sentiment
        
        await process_video_analysis("sid1", "http://url", "uid1")
        
        assert mock_tr.called
        assert mock_an.called
        assert mock_db.analyses.update_one.call_count > 0
        mock_sio.emit.assert_any_call('analysis_complete', ANY, room='sid1')

@pytest.mark.asyncio
async def test_process_video_analysis_whisper_mapping(mock_db):
    """Testuje czy model 'whisper' jest mapowany na 'deepgram-nova-2'"""
    mock_sio = AsyncMock()
    mock_transcription = MagicMock()
    mock_transcription.id = "tid1"
    mock_transcription.transcription = "text"
    mock_transcription.title = "title"

    with patch("app.socketio_handler.sio", mock_sio), \
         patch("app.socketio_handler.db", mock_db), \
         patch("app.socketio_handler.transcribe_video", new_callable=AsyncMock) as mock_tr, \
         patch("app.socketio_handler.analyze", new_callable=AsyncMock) as mock_an:
        
        mock_db.analyses.insert_one.return_value.inserted_id = "aid1"
        mock_tr.return_value = mock_transcription
        mock_an.return_value = {"msg": "ok"}
        
        await process_video_analysis("sid1", "http://url", "uid1", model="whisper-large")
        
        mock_tr.assert_called_with("http://url", model_name="deepgram-nova-2")

@pytest.mark.asyncio
async def test_process_video_analysis_error(mock_db):
    mock_sio = AsyncMock()
    with patch("app.socketio_handler.sio", mock_sio), \
         patch("app.socketio_handler.db", mock_db), \
         patch("app.socketio_handler.transcribe_video", side_effect=Exception("Fail")):
        
        mock_db.analyses.insert_one.return_value.inserted_id = "aid1"
        
        await process_video_analysis("sid1", "http://url", "uid1")
        
        mock_sio.emit.assert_any_call('analysis_error', ANY, room='sid1')
        mock_db.analyses.update_one.assert_called_with(
            {"_id": "aid1"}, 
            {"$set": {"status": "error"}}
        )

@pytest.mark.asyncio
async def test_socket_handlers():
    mock_sio = AsyncMock()
    with patch("app.socketio_handler.sio", mock_sio):
        await connect("sid1", {}, auth={"token": "t"})
        mock_sio.emit.assert_called_with('connected', ANY, room='sid1')
        
        await disconnect("sid1") 
        
        await start_analysis("sid1", {})
        mock_sio.emit.assert_called_with('analysis_error', {'error': 'URL is required'}, room='sid1')
        
        await start_analysis("sid1", {"url": "u"})
        mock_sio.emit.assert_called_with('analysis_error', {'error': 'Authentication token is required'}, room='sid1')
        
        with patch("app.socketio_handler.decode_token", return_value=None):
            await start_analysis("sid1", {"url": "u", "token": "bad"})
            mock_sio.emit.assert_called_with('analysis_error', {'error': 'Invalid or expired token'}, room='sid1')
        
        with patch("app.socketio_handler.decode_token", return_value={"sub": None}):
             await start_analysis("sid1", {"url": "u", "token": "badpayload"})
             mock_sio.emit.assert_called_with('analysis_error', {'error': 'Invalid token payload'}, room='sid1')

        with patch("app.socketio_handler.decode_token", return_value={"sub": "uid1"}), \
             patch("app.socketio_handler.asyncio.create_task") as mock_task:
            await start_analysis("sid1", {"url": "u", "token": "good", "model": "whisper"})
            mock_task.assert_called()

@pytest.mark.asyncio
async def test_get_analyses(mock_db):
    mock_sio = AsyncMock()
    with patch("app.socketio_handler.sio", mock_sio), \
         patch("app.socketio_handler.db", mock_db):

        mock_db.analyses.find = MagicMock() 
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = [{"_id": "aid1", "created_at": datetime.now()}]
        
        mock_db.analyses.find.return_value.sort.return_value = mock_cursor

        await get_analyses("sid1", {})
        mock_sio.emit.assert_called_with('error', {'message': 'Authentication token is required'}, room='sid1')
        
        with patch("app.socketio_handler.decode_token", return_value=None):
             await get_analyses("sid1", {"token": "bad"})
             mock_sio.emit.assert_called_with('error', {'message': 'Invalid or expired token'}, room='sid1')

        with patch("app.socketio_handler.decode_token", return_value={"sub": "uid1"}):
            await get_analyses("sid1", {"token": "good"})

            mock_sio.emit.assert_called_with('analyses_list', ANY, room='sid1')
            
        with patch("app.socketio_handler.decode_token", side_effect=Exception("Boom")):
            await get_analyses("sid1", {"token": "crash"})
            mock_sio.emit.assert_called_with('error', {'message': 'Boom'}, room='sid1')