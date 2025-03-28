#!/usr/bin/env python3
"""
API Server for File Organizer AI Agent
Provides REST endpoints for file organization functionality
"""

import os
import sys
import json
import time
import shutil  # Add missing import for shutil
import secrets
import logging
import asyncio
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import wraps, lru_cache

from fastapi import FastAPI, HTTPException, Depends, Header, Query, Body, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import uvicorn

# Import the file organizer
from file_organizer_agent import FileOrganizer, Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("api_server")

# Create FastAPI app
app = FastAPI(
    title="File Organizer AI Agent API",
    description="API for organizing files using AI Agent",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define constants
API_KEY_FILE = os.environ.get('API_KEY_FILE', 'api_key.txt')
CONFIG_FILE = os.environ.get('CONFIG_FILE', 'config.json')
RECENT_FILES_LIMIT = 100

# API models
class OrganizeRequest(BaseModel):
    source_directory: str = Field(..., description="Directory containing files to organize")
    target_directory: str = Field(..., description="Directory where organized files will be placed")
    organize_by: str = Field("extension", description="Method to organize files (extension, date, size)")
    recursive: bool = Field(True, description="Whether to process subdirectories")
    
class ApiKeyRequest(BaseModel):
    description: str = Field("default", description="Description of the API key")

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any] = Field(..., description="Configuration to update")

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
class RecentFile(BaseModel):
    name: str
    path: str
    category: str
    size: str
    timestamp: str

# Global variables
api_keys = {}
recent_files = []
stats = {
    "total_files_processed": 0,
    "total_files_moved": 0,
    "total_files_skipped": 0,
    "total_errors": 0,
    "api_requests": 0,
    "last_run": None
}

def load_api_keys():
    """Load API keys from file"""
    global api_keys
    
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, 'r') as f:
                key = f.read().strip()
                if key:
                    api_keys = {"default": key}
                    return
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
    
    # If no keys found or error, generate a default key
    api_keys = {"default": secrets.token_hex(32)}
    save_api_keys()

def save_api_keys():
    """Save API keys to file"""
    try:
        with open(API_KEY_FILE, 'w') as f:
            f.write(api_keys.get("default", ""))
        return True
    except Exception as e:
        logger.error(f"Error saving API keys: {e}")
        return False

@lru_cache(maxsize=1)
def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        try:
            config_timestamp = os.path.getmtime(CONFIG_FILE)
            # Clear cache if file was modified
            load_config.cache_info = getattr(load_config, 'cache_info', 0)
            if load_config.cache_info != config_timestamp:
                load_config.cache_clear()
                load_config.cache_info = config_timestamp
                
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    return {}

def save_config(config):
    """Save configuration to file"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        load_config.cache_clear()  # Clear cache after saving
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def update_recent_files(file_path, destination, category="unknown"):
    """Add a file to the recent files list"""
    global recent_files
    
    try:
        file_stat = os.stat(file_path)
        file_size = file_stat.st_size
        
        # Convert file size to human-readable format
        size_str = format_file_size(file_size)
        
        # Create a record for the file
        file_info = {
            "name": os.path.basename(file_path),
            "path": destination,
            "category": category,
            "size": size_str,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to the front of the list
        recent_files.insert(0, file_info)
        
        # Limit the list size
        if len(recent_files) > RECENT_FILES_LIMIT:
            recent_files = recent_files[:RECENT_FILES_LIMIT]
    except Exception as e:
        logger.error(f"Error updating recent files: {e}")

def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def update_stats(new_stats):
    """Update global stats with new run"""
    global stats
    
    stats["total_files_processed"] += new_stats.get("files_processed", 0)
    stats["total_files_moved"] += new_stats.get("files_moved", 0)
    stats["total_files_skipped"] += new_stats.get("files_skipped", 0)
    stats["total_errors"] += new_stats.get("errors", 0)
    stats["api_requests"] += 1
    stats["last_run"] = datetime.now().isoformat()

def verify_api_key(x_api_key: str = Header(None)):
    """Verify the API key from request header"""
    if not api_keys:
        load_api_keys()
        
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is missing")
        
    # Check if the key exists
    if x_api_key not in api_keys.values():
        raise HTTPException(status_code=401, detail="Invalid API key")
        
    return x_api_key

class CustomFileOrganizer(FileOrganizer):
    """Custom version of FileOrganizer that updates recent files"""
    
    async def process_file(self, file_path: str) -> bool:
        """Override process_file to track recent files"""
        try:
            self.stats.files_processed += 1
            
            # Get destination path
            dest_dir = self.get_destination_path(file_path)
            if not dest_dir:
                logger.debug(f"Skipping file: {file_path}")
                self.stats.files_skipped += 1
                return False
                
            # Create target directory if it doesn't exist
            os.makedirs(dest_dir, exist_ok=True)
            
            # Handle duplicates
            target_path = os.path.join(dest_dir, os.path.basename(file_path))
            final_path = self.handle_duplicate(file_path, target_path)
            
            if not final_path:
                logger.debug(f"Skipped duplicate file: {file_path}")
                self.stats.files_skipped += 1
                return False
                
            # Move the file
            category = os.path.basename(dest_dir)
            shutil.move(file_path, final_path)
            logger.info(f"Moved file: {file_path} -> {final_path}")
            
            # Add to recent files
            update_recent_files(final_path, dest_dir, category)
            
            self.stats.files_moved += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.stats.errors += 1
            return False

@app.on_event("startup")
async def startup_event():
    """Run on API server startup"""
    logger.info("Starting File Organizer API Server")
    
    # Load API keys
    load_api_keys()
    
    # Load configuration
    load_config()
    
    logger.info(f"API Server started with {len(api_keys)} API keys")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "timestamp": datetime.now().isoformat()}

@app.post("/api/organize")
async def organize_files(request: OrganizeRequest, api_key: str = Depends(verify_api_key)):
    """Organize files in the specified directory"""
    source_dir = os.path.expanduser(request.source_directory)
    target_dir = os.path.expanduser(request.target_directory)
    
    if not os.path.exists(source_dir):
        raise HTTPException(status_code=400, detail=f"Source directory does not exist: {source_dir}")
    
    logger.info(f"Organizing files from {source_dir} to {target_dir}")
    
    # Create configuration
    config_data = load_config()
    
    # Update with request parameters
    config_data["source_directory"] = source_dir
    config_data["target_directory"] = target_dir
    config_data["organize_by"] = request.organize_by
    
    # Create config and organizer objects
    config = Config(None)
    config.config = config_data
    
    organizer = CustomFileOrganizer(config)
    
    # Start organization in a background task to avoid blocking
    try:
        # Run asynchronously and wait for result
        result = await organizer.organize()
        
        # Update stats
        update_stats(result)
        
        return {
            "status": "success",
            "message": f"Organized {result['files_moved']} files",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error organizing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recent-files")
async def get_recent_files(
    limit: int = Query(20, description="Maximum number of files to return"),
    api_key: str = Depends(verify_api_key)
):
    """Get list of recently organized files"""
    return recent_files[:min(limit, len(recent_files))]

@app.get("/api/stats")
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get organization statistics"""
    return stats

@app.post("/api/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update configuration"""
    config = load_config()
    
    # Update configuration with new values
    config.update(request.config)
    
    if save_config(config):
        return {"status": "success", "message": "Configuration updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@app.get("/api/config")
async def get_configuration(api_key: str = Depends(verify_api_key)):
    """Get current configuration"""
    return load_config()

@app.post("/api/keys")
async def generate_api_key(
    request: ApiKeyRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate a new API key"""
    new_key = secrets.token_hex(32)
    api_keys[request.description] = new_key
    
    if save_api_keys():
        return {"status": "success", "key": new_key}
    else:
        raise HTTPException(status_code=500, detail="Failed to save API key")

@app.get("/api/keys")
async def list_api_keys(api_key: str = Depends(verify_api_key)):
    """List API keys (only descriptions, not actual keys)"""
    return {"keys": list(api_keys.keys())}

@app.delete("/api/keys/{key_id}")
async def delete_api_key(key_id: str, api_key: str = Depends(verify_api_key)):
    """Delete an API key"""
    if key_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default API key")
    
    if key_id in api_keys:
        del api_keys[key_id]
        if save_api_keys():
            return {"status": "success", "message": f"Deleted API key: {key_id}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save API keys")
    else:
        raise HTTPException(status_code=404, detail=f"API key not found: {key_id}")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

def main():
    """Main function to run the API server"""
    parser = argparse.ArgumentParser(description="File Organizer API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", default=3333, type=int, help="Port to listen on")
    args = parser.parse_args()
    
    # Start the API server
    logger.info(f"Starting API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main() 