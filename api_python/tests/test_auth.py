import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.modules.v1.auth import service as auth_service
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
import jwt

if not hasattr(jwt, 'JWTError'):
    if hasattr(jwt, 'PyJWTError'):
        jwt.JWTError = jwt.PyJWTError
    else:
        jwt.JWTError = Exception

client = TestClient(app)


def test_verify_password_bytes():
    """Testuje weryfikację hasła, gdy hash jest bajtami (pokrycie linii else)"""
    pwd = "secret"
    hashed_str = auth_service.get_password_hash(pwd)
    hashed_bytes = hashed_str.encode('utf-8')

    assert auth_service.verify_password(pwd, hashed_bytes) is True

def test_password_hashing():
    pwd = "secret"
    hashed = auth_service.get_password_hash(pwd)
    assert hashed != pwd
    assert auth_service.verify_password(pwd, hashed) is True
    assert auth_service.verify_password("wrong", hashed) is False

def test_token_creation_and_decoding():
    data = {"sub": "test@example.com"}
    token = auth_service.create_access_token(data)
    decoded = auth_service.decode_token(token)
    assert decoded["sub"] == "test@example.com"

def test_token_expiration_logic():
    """Testuje wygasły token (pokrycie ExpiredSignatureError)"""
    data = {"sub": "test@example.com"}

    token = auth_service.create_access_token(data, expires_delta=timedelta(days=-1))
    
    assert auth_service.decode_token(token) is None

def test_token_invalid_signature():
    """Testuje niepoprawny token (pokrycie JWTError/InvalidToken)"""
    assert auth_service.decode_token("invalid.token.structure") is None

@pytest.mark.asyncio
async def test_create_user_success(mock_db):
    with patch("app.modules.v1.auth.service.db", mock_db):
        mock_db.users.find_one.side_effect = [None, {"_id": "123", "email": "new@test.com"}] 
        mock_db.users.insert_one.return_value.inserted_id = "123"
        
        user = await auth_service.create_user("new@test.com", "pass")
        assert user["email"] == "new@test.com"
        mock_db.users.insert_one.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_exists(mock_db):
    with patch("app.modules.v1.auth.service.db", mock_db):
        mock_db.users.find_one.return_value = {"email": "exists@test.com"}
        user = await auth_service.create_user("exists@test.com", "pass")
        assert user is None

@pytest.mark.asyncio
async def test_authenticate_user(mock_db):
    hashed = auth_service.get_password_hash("pass")
    mock_user = {"email": "test@test.com", "password": hashed}
    
    with patch("app.modules.v1.auth.service.db", mock_db):
        mock_db.users.find_one.return_value = mock_user
        
        # Success
        auth = await auth_service.authenticate_user("test@test.com", "pass")
        assert auth == mock_user
        
        # Wrong password
        auth_fail = await auth_service.authenticate_user("test@test.com", "wrong")
        assert auth_fail is False
        
        # User not found
        mock_db.users.find_one.return_value = None
        auth_none = await auth_service.authenticate_user("404@test.com", "pass")
        assert auth_none is False

# --- API Router Tests ---

@pytest.mark.asyncio
async def test_register_endpoint():
    with patch("app.modules.v1.auth.router.create_user", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = {"_id": "123", "email": "test@test.com", "created_at": datetime.now()}
        
        response = client.post("/api/v1/auth/register", json={"email": "test@test.com", "password": "password123"})
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_register_existing_user():
    with patch("app.modules.v1.auth.router.create_user", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = None
        
        response = client.post("/api/v1/auth/register", json={"email": "exists@test.com", "password": "password123"})
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_endpoint():
    with patch("app.modules.v1.auth.router.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = {"_id": "123", "email": "test@test.com", "created_at": datetime.now()}
        
        response = client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "pass"})
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_failure():
    with patch("app.modules.v1.auth.router.authenticate_user", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = False
        response = client.post("/api/v1/auth/login", json={"email": "test@test.com", "password": "pass"})
        assert response.status_code == 401

def test_auth_test_endpoint():
    response = client.get("/api/v1/auth/test")
    assert response.status_code == 200