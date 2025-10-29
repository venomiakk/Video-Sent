from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
from app.core.database import db
from bson import ObjectId

# JWT settings
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: Move to config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Convert strings to bytes for bcrypt
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Convert password to bytes and hash it
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string for storage
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def get_user_by_email(email: str):
    """Get user by email"""
    user = await db.users.find_one({"email": email})
    return user


async def create_user(email: str, password: str):
    """Create a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(email)
    if existing_user:
        return None
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # Create user document
    user_doc = {
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }
    
    # Insert into database
    result = await db.users.insert_one(user_doc)
    
    # Get the created user
    user = await db.users.find_one({"_id": result.inserted_id})
    return user


async def authenticate_user(email: str, password: str):
    """Authenticate a user"""
    user = await get_user_by_email(email)
    if not user:
        return False
    if not verify_password(password, user["password"]):
        return False
    return user


def decode_token(token: str):
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
