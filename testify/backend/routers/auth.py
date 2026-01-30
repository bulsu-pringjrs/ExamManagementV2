import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import jwt
from datetime import datetime, timedelta
import os

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.auth import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "testify-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Hardcoded credentials for demo (in production, use database)
DEMO_USERS = {
    "admin@testify.local": {
        "id": "1",
        "email": "admin@testify.local",
        "password": "admin123",  # Plain text for demo only
        "role": "super_admin",
        "full_name": "Super Administrator"
    },
    "teacher1@testify.local": {
        "id": "2",
        "email": "teacher1@testify.local",
        "password": "teacher123",
        "role": "teacher",
        "full_name": "John Smith"
    },
    "teacher2@testify.local": {
        "id": "3",
        "email": "teacher2@testify.local",
        "password": "teacher123",
        "role": "teacher",
        "full_name": "Sarah Johnson"
    },
    "student1@testify.local": {
        "id": "4",
        "email": "student1@testify.local",
        "password": "student123",
        "role": "student",
        "full_name": "Alice Brown"
    },
    "student2@testify.local": {
        "id": "5",
        "email": "student2@testify.local",
        "password": "student123",
        "role": "student",
        "full_name": "Bob Wilson"
    },
    "student3@testify.local": {
        "id": "6",
        "email": "student3@testify.local",
        "password": "student123",
        "role": "student",
        "full_name": "Carol Davis"
    }
}

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str
    full_name: str

@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """Login endpoint - validates credentials and returns JWT token"""
    try:
        # Check if user exists in demo users
        if data.email not in DEMO_USERS:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = DEMO_USERS[data.email]
        
        # Validate password (plain text comparison for demo)
        if data.password != user["password"]:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create JWT token
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"],
            "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        }
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "full_name": user["full_name"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/logout")
async def logout():
    """Logout endpoint - client should remove token from storage"""
    return {"message": "Logged out successfully"}

@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current user information from JWT token"""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header.split(" ")[1]
        
        # Decode JWT token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "full_name": payload.get("full_name")
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")

@router.post("/users", response_model=dict)
async def create_user(data: CreateUserRequest, request: Request):
    """Create new user (Super Admin only)"""
    try:
        # Verify super admin role
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can create users")
        
        # Check if user already exists
        if data.email in DEMO_USERS:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user ID
        new_id = str(len(DEMO_USERS) + 1)
        
        # Add user to demo users
        DEMO_USERS[data.email] = {
            "id": new_id,
            "email": data.email,
            "password": data.password,
            "role": data.role,
            "full_name": data.full_name
        }
        
        return {
            "id": new_id,
            "email": data.email,
            "role": data.role,
            "full_name": data.full_name,
            "message": "User created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@router.get("/users")
async def list_users(request: Request):
    """List all users (Super Admin only)"""
    try:
        # Verify super admin role
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("role") != "super_admin":
            raise HTTPException(status_code=403, detail="Only super admin can list users")
        
        # Return all users without passwords
        users_list = [
            {
                "id": user["id"],
                "email": user["email"],
                "role": user["role"],
                "full_name": user["full_name"]
            }
            for user in DEMO_USERS.values()
        ]
        
        return {"users": users_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")