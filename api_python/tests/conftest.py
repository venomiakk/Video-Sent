import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Mock environment variables before importing app modules
import os
os.environ["SECRET_KEY"] = "test-secret"
os.environ["GROQ_SECRET"] = "test-groq"
os.environ["DEEPGRAM_SECRET"] = "test-deepgram"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db():
    """Mockuje całą bazę danych MongoDB."""
    db = MagicMock()
    # Setup collection mocks
    db.users = AsyncMock()
    db.transcriptions = AsyncMock()
    db.sentiment_analysis = AsyncMock()
    db.analyses = AsyncMock()
    return db

@pytest.fixture
def override_db(mock_db):
    """Nadpisuje bazę danych w aplikacji."""
    from app.core.database import db
    # Patching attributes dynamically
    with list(mock_db.users.side_effect), list(mock_db.transcriptions.side_effect): 
         pass # Just a placeholder context logic if needed, usually patch is better
    return mock_db