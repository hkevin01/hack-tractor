"""FastAPI backend for the Hack Tractor project."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from typing import List, Dict, Any, Optional
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hack Tractor API",
    description="API for controlling and monitoring agricultural equipment",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Basic routes
@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Hack Tractor API",
        "version": "0.1.0",
        "status": "online"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

# Equipment routes
@app.get("/equipment")
async def list_equipment():
    """List all connected equipment."""
    # Placeholder - would be implemented with real equipment discovery
    return {"equipment": [
        {"id": "tractor-01", "type": "tractor", "manufacturer": "John Deere", "model": "8R", "status": "connected"},
        {"id": "implement-01", "type": "implement", "manufacturer": "Generic", "model": "Attachment", "status": "connected"}
    ]}

@app.get("/equipment/{equipment_id}")
async def get_equipment(equipment_id: str):
    """Get information about specific equipment."""
    # Placeholder - would be implemented with real equipment lookup
    if equipment_id == "tractor-01":
        return {
            "id": "tractor-01", 
            "type": "tractor", 
            "manufacturer": "John Deere", 
            "model": "8R", 
            "status": "connected",
            "metrics": {
                "fuel": 78,
                "engine_temp": 92,
                "rpm": 1800,
                "speed": 5.2
            }
        }
    else:
        raise HTTPException(status_code=404, detail="Equipment not found")

@app.post("/equipment/{equipment_id}/command")
async def send_command(equipment_id: str, command: Dict[str, Any]):
    """Send a command to specific equipment."""
    # Placeholder - would be implemented with real command execution
    logger.info(f"Sending command to {equipment_id}: {command}")
    return {"status": "command_sent", "equipment_id": equipment_id, "command": command}

# Main entry point
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
