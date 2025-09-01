import os
import uvicorn
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
import jwt
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Initialize FastAPI app
app = FastAPI(
    title="Lunch Pay Generic API",
    description="A generic FastAPI + MongoDB REST API with authentication",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB client
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

# Security
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id" and isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_doc(value)
            elif isinstance(value, list):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(user_id: str = Depends(verify_token)):
    """Get current user from database"""
    users_collection = db["users"]
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return serialize_doc(user)

def convert_query_value(value: str):
    """Convert query parameter string to appropriate type"""
    # Convert boolean strings
    if value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    
    # Try to convert to int
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try to convert to float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value

# Authentication Endpoints

@app.post("/auth/register")
async def register(request: Request):
    """Register endpoint"""
    try:
        body = await request.json()
        name = body.get("name")
        email = body.get("email")
        password = body.get("password")
        
        if not name or not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name, email and password required"
            )
        
        users_collection = db["users"]
        
        # Check if user already exists
        existing_user = users_collection.find_one({
            "$or": [{"name": name}, {"email": email}]
        })
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this name or email already exists"
            )
        
        # Create new user
        new_user = {
            "name": name,
            "email": email,
            "password": password,  # Plain text as per guidelines
            "role": "user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None,
            "is_active": True,
            "email_verified": False
        }
        
        result = users_collection.insert_one(new_user)
        
        # Fetch the created user
        created_user = users_collection.find_one({"_id": result.inserted_id})
        user_data = serialize_doc(created_user)
        user_data.pop("password", None)  # Remove password from response
        
        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "user": {
                    "id": user_data["_id"],
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "role": user_data.get("role", "user"),
                    "created_at": user_data.get("created_at"),
                    "is_active": user_data.get("is_active"),
                    "email_verified": user_data.get("email_verified")
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/login")
async def login(request: Request, response: Response):
    """Login endpoint"""
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password required"
            )
        
        users_collection = db["users"]
        user = users_collection.find_one({"email": email})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # For now, check password in plain text as per guidelines
        if user["password"] != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Update last login
        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["_id"])}, 
            expires_delta=access_token_expires
        )
        refresh_token = create_access_token(
            data={"sub": str(user["_id"]), "type": "refresh"}, 
            expires_delta=timedelta(days=7)
        )
        
        # Set HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        user_data = serialize_doc(user)
        user_data.pop("password", None)  # Remove password from response
        
        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "user": {
                    "id": user_data["_id"],
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "role": user_data.get("role", "user")
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout endpoint"""
    return {
        "success": True,
        "message": "Logout successful"
    }

@app.get("/auth/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    user_data = current_user.copy()
    user_data.pop("password", None)  # Remove password from response
    
    return {
        "success": True,
        "message": "Profile retrieved successfully",
        "data": {
            "user": {
                "id": user_data["_id"],
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "role": user_data.get("role", "user"),
                "created_at": user_data.get("created_at"),
                "updated_at": user_data.get("updated_at"),
                "last_login": user_data.get("last_login")
            }
        }
    }

@app.get("/auth/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validate token"""
    return {
        "success": True,
        "message": "Token is valid",
        "data": {
            "valid": True,
            "user_id": current_user["_id"],
            "expires_at": (datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
            "token_type": "access_token"
        }
    }

# Dynamic CRUD Endpoints

@app.get("/{entity}")
async def get_all_documents(entity: str):
    """Get all documents from a collection"""
    try:
        collection = db[entity]
        documents = list(collection.find())
        return serialize_doc(documents)
    except Exception as e:
        logger.error(f"Error fetching documents from {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching documents"
        )

@app.get("/{entity}/id/{item_id}")
async def get_document_by_id(entity: str, item_id: str):
    """Get a single document by ID"""
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ObjectId format"
            )
        
        collection = db[entity]
        document = collection.find_one({"_id": ObjectId(item_id)})
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return serialize_doc(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {item_id} from {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching document"
        )

@app.post("/{entity}")
async def save_new_document(entity: str, request: Request):
    """Save a new document"""
    try:
        document = await request.json()
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()
        
        collection = db[entity]
        result = collection.insert_one(document)
        
        # Fetch the inserted document
        saved_document = collection.find_one({"_id": result.inserted_id})
        return serialize_doc(saved_document)
        
    except Exception as e:
        logger.error(f"Error saving document to {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving document"
        )

@app.put("/{entity}/{item_id}")
async def update_document(entity: str, item_id: str, request: Request):
    """Update an existing document"""
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ObjectId format"
            )
        
        update_data = await request.json()
        update_data["updated_at"] = datetime.utcnow()
        
        collection = db[entity]
        result = collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Fetch the updated document
        updated_document = collection.find_one({"_id": ObjectId(item_id)})
        return serialize_doc(updated_document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {item_id} in {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating document"
        )

@app.delete("/{entity}/{item_id}")
async def delete_document(entity: str, item_id: str):
    """Delete a document by ID"""
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ObjectId format"
            )
        
        collection = db[entity]
        
        # Fetch the document before deletion
        document = collection.find_one({"_id": ObjectId(item_id)})
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        result = collection.delete_one({"_id": ObjectId(item_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "deleted_document": serialize_doc(document)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {item_id} from {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting document"
        )

@app.get("/{entity}/filter")
async def get_filtered_documents(entity: str, request: Request):
    """Get documents with dynamic filtering"""
    try:
        query_params = dict(request.query_params)
        
        # Convert query parameters to appropriate types
        filters = {}
        for key, value in query_params.items():
            # Don't convert _id to ObjectId to avoid Invalid ObjectId errors
            if key != "_id":
                filters[key] = convert_query_value(value)
            else:
                filters[key] = value
        
        collection = db[entity]
        documents = list(collection.find(filters))
        return serialize_doc(documents)
        
    except Exception as e:
        logger.error(f"Error filtering documents from {entity}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error filtering documents"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lunch Pay Generic API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "profile": "GET /auth/profile",
                "validate": "GET /auth/validate"
            },
            "crud": {
                "get_all": "GET /{entity}",
                "get_by_id": "GET /{entity}/id/{item_id}",
                "save_new": "POST /{entity}",
                "update": "PUT /{entity}/{item_id}",
                "delete": "DELETE /{entity}/{item_id}",
                "filter": "GET /{entity}/filter"
            }
        }
    }

# Startup logic for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
