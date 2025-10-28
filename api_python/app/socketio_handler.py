import socketio
from fastapi import FastAPI
from app.modules.v1.transcription.service import transcribe_video
from app.modules.v1.sentiment.router import analyze_sentiment
from app.modules.v1.analysis.schemas import VideoAnalysis, AnalysisStep
from app.modules.v1.auth.service import decode_token
from app.core.database import db
from datetime import datetime
import asyncio
import logging

# Create Socket.IO server with ASGI support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=True,
    ping_timeout=120,  # Zwiększamy timeout do 120 sekund
    ping_interval=25   # Ping co 25 sekund
)

# Create Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio)

logger = logging.getLogger(__name__)


async def emit_step(sid: str, analysis_id: str, step: str, status: str, message: str):
    """Emit progress step to specific client"""
    logger.info(f"📤 Emitting step to {sid}: {step} - {status} - {message}")
    
    step_data = AnalysisStep(
        step=step,
        status=status,
        message=message,
        timestamp=datetime.utcnow()
    )
    # Convert to dict and handle datetime serialization
    step_dict = step_data.model_dump() if hasattr(step_data, 'model_dump') else step_data.dict()
    if 'timestamp' in step_dict and isinstance(step_dict['timestamp'], datetime):
        step_dict['timestamp'] = step_dict['timestamp'].isoformat()
    
    await sio.emit('analysis_step', {
        'analysis_id': analysis_id,
        'step': step_dict
    }, room=sid)
    logger.info(f"✅ Step emitted successfully")


async def process_video_analysis(sid: str, url: str, user_id: str, model: str = "whisperpy-base"):
    """Process video analysis with real-time updates via Socket.IO"""
    analysis_id = None
    result = None
    
    try:
        # Create analysis record with user_id
        analysis = VideoAnalysis(
            url=url,
            status="processing",
            steps=[],
            user_id=user_id
        )
        
        result = await db.analyses.insert_one(
            analysis.model_dump(exclude={'id'}) if hasattr(analysis, 'model_dump') 
            else analysis.dict(exclude={'id'})
        )
        analysis_id = str(result.inserted_id)
        
        logger.info(f"Starting analysis {analysis_id} for {url}")
        
        # Step 1: Download and transcribe (combined step with progress)
        await emit_step(sid, analysis_id, "download", "in_progress", "Pobieranie wideo z YouTube...")
        
        # Długa operacja - transkrypcja
        logger.info("Starting transcription - this may take a while")
        await emit_step(sid, analysis_id, "transcription", "in_progress", "Transkrypcja audio w toku... To może potrwać kilka minut.")
        
        transcription_result = await transcribe_video(url, model_name=model)
        logger.info("Transcription completed")
        
        transcription_id = str(transcription_result.id)
        transcription_text = transcription_result.transcription
        
        await emit_step(sid, analysis_id, "transcription", "completed", "Transkrypcja zakończona")
        
        # Step 2: Sentiment analysis
        await emit_step(sid, analysis_id, "sentiment", "in_progress", "Analiza sentymentu...")
        
        sentiment_result = await analyze_sentiment(transcription_id)
        
        await emit_step(sid, analysis_id, "sentiment", "completed", "Analiza sentymentu zakończona")
        
        # Update analysis with results
        await db.analyses.update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "status": "completed",
                    "title": transcription_result.title,
                    "transcription": transcription_text,
                    "sentiment": sentiment_result,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Emit completion
        await sio.emit('analysis_complete', {
            'analysis_id': analysis_id,
            'title': transcription_result.title,
            'transcription': transcription_text,
            'sentiment': sentiment_result
        }, room=sid)
        
        logger.info(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in analysis {analysis_id}: {str(e)}")
        if analysis_id and result:
            await db.analyses.update_one(
                {"_id": result.inserted_id},
                {"$set": {"status": "error"}}
            )
            await emit_step(sid, analysis_id, "error", "error", f"Błąd: {str(e)}")
        await sio.emit('analysis_error', {
            'analysis_id': analysis_id,
            'error': str(e)
        }, room=sid)


@sio.event
async def connect(sid, environ, auth=None):
    """Handle client connection with optional authentication"""
    logger.info(f"Client connected: {sid}")
    if auth:
        logger.info(f"Auth data received: {auth}")
    await sio.emit('connected', {'message': 'Connected to analysis server'}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def start_analysis(sid, data):
    """Handle analysis request from client"""
    logger.info(f"Analysis request from {sid}: {data}")
    url = data.get('url')
    model = data.get('model', 'whisperpy-base')
    token = data.get('token')
    
    if not url:
        await sio.emit('analysis_error', {'error': 'URL is required'}, room=sid)
        return
    
    if not token:
        await sio.emit('analysis_error', {'error': 'Authentication token is required'}, room=sid)
        return
    
    # Decode token to get user_id
    payload = decode_token(token)
    if not payload:
        await sio.emit('analysis_error', {'error': 'Invalid or expired token'}, room=sid)
        return
    
    user_id = payload.get('sub')
    if not user_id:
        await sio.emit('analysis_error', {'error': 'Invalid token payload'}, room=sid)
        return
    
    # Start processing in background with user_id
    asyncio.create_task(process_video_analysis(sid, url, user_id, model))


@sio.event
async def get_analyses(sid, data):
    """Get list of user's analyses"""
    logger.info(f"Get analyses request from {sid}")
    
    try:
        token = data.get('token')
        
        if not token:
            await sio.emit('error', {'message': 'Authentication token is required'}, room=sid)
            return
        
        # Decode token to get user_id
        payload = decode_token(token)
        if not payload:
            await sio.emit('error', {'message': 'Invalid or expired token'}, room=sid)
            return
        
        user_id = payload.get('sub')
        if not user_id:
            await sio.emit('error', {'message': 'Invalid token payload'}, room=sid)
            return
        
        # Filter analyses by user_id
        analyses = await db.analyses.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
        
        # Convert ObjectId and datetime to string
        for analysis in analyses:
            analysis['id'] = str(analysis['_id'])
            del analysis['_id']
            
            # Convert all datetime fields to ISO format strings
            for key, value in analysis.items():
                if isinstance(value, datetime):
                    analysis[key] = value.isoformat()
        
        await sio.emit('analyses_list', {'analyses': analyses}, room=sid)
    except Exception as e:
        logger.error(f"Error fetching analyses: {str(e)}")
        await sio.emit('error', {'message': str(e)}, room=sid)


def mount_socketio(app: FastAPI):
    """Mount Socket.IO to FastAPI app"""
    app.mount('/socket.io', socket_app)
    return sio
