"""
User Service
Manages user authentication with configurable storage

This replaces hardcoded credentials with a proper user management system.
Uses file-based storage by default but can be replaced with database storage.
"""
import json
import os
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
USERS_FILE = DATA_DIR / "users.json"


class UserService:
    """
    User management service.

    Features:
    1. Secure password hashing (SHA-256 with salt)
    2. File-based storage (easily replaceable with DB)
    3. User CRUD operations
    4. Role-based access support
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize user storage"""
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load or create users file
        if USERS_FILE.exists():
            self._load_users()
        else:
            self._create_default_users()

        logger.info(f"UserService initialized with {len(self.users)} users")

    def _load_users(self):
        """Load users from file"""
        try:
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                self.users = data.get('users', {})
                self.salt = data.get('salt', secrets.token_hex(16))
        except Exception as e:
            logger.error(f"Error loading users: {e}")
            self._create_default_users()

    def _save_users(self):
        """Save users to file"""
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump({
                    'users': self.users,
                    'salt': self.salt,
                    'updated_at': datetime.utcnow().isoformat()
                }, f, indent=2)
            logger.info("Users saved to file")
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def _create_default_users(self):
        """Create default users for initial setup"""
        self.salt = secrets.token_hex(16)
        self.users = {}

        # Create default admin and capexplan users
        # In production, these should be configured via environment variables
        default_users = [
            {
                'username': 'capexplan',
                'password': os.getenv('CAPEXPLAN_PASSWORD', 'secure_password_123'),
                'role': 'service',
                'description': 'Capexplan integration service account'
            },
            {
                'username': 'admin',
                'password': os.getenv('ADMIN_PASSWORD', 'admin_password_456'),
                'role': 'admin',
                'description': 'System administrator'
            }
        ]

        for user_data in default_users:
            self.create_user(
                username=user_data['username'],
                password=user_data['password'],
                role=user_data['role'],
                description=user_data.get('description', '')
            )

        self._save_users()
        logger.info("Default users created")

    def _hash_password(self, password: str) -> str:
        """Hash password with salt using SHA-256"""
        salted = f"{self.salt}{password}"
        return hashlib.sha256(salted.encode()).hexdigest()

    def create_user(
        self,
        username: str,
        password: str,
        role: str = 'user',
        description: str = ''
    ) -> Dict[str, Any]:
        """
        Create a new user.

        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            role: User role (admin, service, user)
            description: Optional description

        Returns:
            User record (without password)
        """
        if username in self.users:
            raise ValueError(f"User {username} already exists")

        user = {
            'username': username,
            'password_hash': self._hash_password(password),
            'role': role,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'last_login': None,
            'active': True
        }

        self.users[username] = user
        self._save_users()

        logger.info(f"User {username} created with role {role}")

        # Return user without password hash
        return self._safe_user(user)

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.

        Args:
            username: Username
            password: Plain text password

        Returns:
            User record if authenticated, None otherwise
        """
        user = self.users.get(username)

        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return None

        if not user.get('active', True):
            logger.warning(f"Authentication failed: user {username} is inactive")
            return None

        password_hash = self._hash_password(password)
        if user['password_hash'] != password_hash:
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None

        # Update last login
        user['last_login'] = datetime.utcnow().isoformat()
        self._save_users()

        logger.info(f"User {username} authenticated successfully")
        return self._safe_user(user)

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (without password)"""
        user = self.users.get(username)
        return self._safe_user(user) if user else None

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without passwords)"""
        return [self._safe_user(u) for u in self.users.values()]

    def update_password(self, username: str, new_password: str) -> bool:
        """Update user password"""
        if username not in self.users:
            return False

        self.users[username]['password_hash'] = self._hash_password(new_password)
        self._save_users()
        logger.info(f"Password updated for user {username}")
        return True

    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user (soft delete)"""
        if username not in self.users:
            return False

        self.users[username]['active'] = False
        self._save_users()
        logger.info(f"User {username} deactivated")
        return True

    def activate_user(self, username: str) -> bool:
        """Reactivate a user"""
        if username not in self.users:
            return False

        self.users[username]['active'] = True
        self._save_users()
        logger.info(f"User {username} activated")
        return True

    def _safe_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Return user without sensitive fields"""
        if not user:
            return None
        return {
            'username': user['username'],
            'role': user['role'],
            'description': user.get('description', ''),
            'created_at': user.get('created_at'),
            'last_login': user.get('last_login'),
            'active': user.get('active', True)
        }


# Singleton instance
user_service = UserService()
