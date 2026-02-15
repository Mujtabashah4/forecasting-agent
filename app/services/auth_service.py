"""
Authentication Service
Token-based authentication with IP restrictions
Based on Section 3 of implementation guide
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token string

    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        return None


def check_ip_allowed(client_ip: str) -> bool:
    """
    Check if client IP is in allowed list.

    Args:
        client_ip: Client IP address

    Returns:
        bool: True if IP is allowed, False otherwise
    """
    allowed_ips = settings.allowed_ips_list

    # Check if IP is in allowed list
    if client_ip in allowed_ips:
        return True

    # Check for CIDR ranges (basic implementation)
    # For production, use a proper CIDR library
    for allowed_ip in allowed_ips:
        if '/' in allowed_ip:
            # CIDR range - simplified check
            # In production, use ipaddress module properly
            network = allowed_ip.split('/')[0]
            if client_ip.startswith(network.rsplit('.', 1)[0]):
                return True

    return False


# Import user service for proper user management
from app.services.user_service import user_service


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user with username and password.

    Uses the UserService for proper user management instead of hardcoded credentials.

    Args:
        username: Username
        password: Plain text password

    Returns:
        dict: User data if authenticated, None otherwise
    """
    user = user_service.authenticate(username, password)

    if not user:
        logger.debug(f"Authentication failed for user: {username}")
        return None

    logger.info(f"User authenticated successfully: {username}")
    return user
