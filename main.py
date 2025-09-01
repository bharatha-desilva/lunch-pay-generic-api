from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
from typing import Dict, Any, Optional
import os
import uvicorn

# MongoDB configuration
MONGODB_URI = "mongodb+srv://nuwanwp:zXi15ByhNUNFEOOD@cluster0.gjas8wj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
MONGODB_DB = "fastapi_mongo_api"

# Initialize FastAPI app
app = FastAPI(
    title="Generic MongoDB API",
    description="Dynamic FastAPI REST API with MongoDB integration",
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

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    if isinstance(doc, dict):
        return {k: serialize_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc

def convert_query_params(params: Dict[str, str]) -> Dict[str, Any]:
    """Convert query parameters to appropriate types"""
    filters = {}
    for key, value in params.items():
        # Don't convert _id to ObjectId to avoid InvalidId errors
        if key == "_id":
            filters[key] = value
        elif value.lower() == "true":
            filters[key] = True
        elif value.lower() == "false":
            filters[key] = False
        else:
            # Try to convert to int
            try:
                filters[key] = int(value)
                continue
            except ValueError:
                pass
            
            # Try to convert to float
            try:
                filters[key] = float(value)
                continue
            except ValueError:
                pass
            
            # Keep as string
            filters[key] = value
    
    return filters

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    """Add CORS headers to all responses"""
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Generic MongoDB API", "version": "1.0.0"}

@app.get("/{entity}")
async def get_all(entity: str):
    """GET_ALL: Fetch all documents from the specified entity/collection"""
    try:
        collection = db[entity]
        documents = list(collection.find())
        return {"data": serialize_doc(documents), "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {str(e)}")

@app.get("/{entity}/id/{item_id}")
async def get_by_id(entity: str, item_id: str):
    """GET_BY_ID: Fetch a single document by its MongoDB ObjectId"""
    try:
        collection = db[entity]
        try:
            document = collection.find_one({"_id": ObjectId(item_id)})
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"data": serialize_doc(document)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document: {str(e)}")

@app.post("/{entity}")
async def save_new(entity: str, request: Request):
    """SAVE_NEW: Save a new JSON object exactly as received in the request body"""
    try:
        collection = db[entity]
        body = await request.json()
        
        # Insert the document as-is
        result = collection.insert_one(body)
        
        # Fetch the inserted document
        inserted_doc = collection.find_one({"_id": result.inserted_id})
        
        return {"data": serialize_doc(inserted_doc), "message": "Document created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving document: {str(e)}")

@app.put("/{entity}/{item_id}")
async def update(entity: str, item_id: str, request: Request):
    """UPDATE: Update an existing document by its ObjectId with JSON fields provided in the request"""
    try:
        collection = db[entity]
        body = await request.json()
        
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        # Update the document
        result = collection.update_one(
            {"_id": object_id},
            {"$set": body}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Fetch the updated document
        updated_doc = collection.find_one({"_id": object_id})
        
        return {"data": serialize_doc(updated_doc), "message": "Document updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating document: {str(e)}")

@app.get("/{entity}/filter")
async def get_filtered(entity: str, request: Request):
    """GET_FILTERED: Fetch documents dynamically filtered by any query parameters"""
    try:
        collection = db[entity]
        query_params = dict(request.query_params)
        
        # Convert query parameters to appropriate types
        filters = convert_query_params(query_params)
        
        # Query the collection
        documents = list(collection.find(filters))
        
        return {"data": serialize_doc(documents), "count": len(documents), "filters": filters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering documents: {str(e)}")

@app.delete("/{entity}/{item_id}")
async def delete_by_id(entity: str, item_id: str):
    """DELETE_BY_ID: Delete document by key"""
    try:
        collection = db[entity]
        
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid ObjectId format")
        
        # Fetch the document before deletion
        document = collection.find_one({"_id": object_id})
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete the document
        result = collection.delete_one({"_id": object_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"data": serialize_doc(document), "message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

# Startup logic for Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
