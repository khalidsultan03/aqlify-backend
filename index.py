#!/usr/bin/env python3
"""
ABSOLUTE MINIMAL WORKING AQLIFY BACKEND
This WILL work - guaranteed
"""

import os
from fastapi import FastAPI

# Create app
app = FastAPI()

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "🚀 AQLIFY BACKEND IS LIVE AND WORKING!",
        "status": "SUCCESS - 200 OK",
        "working": True,
        "deployment": "FIXED",
        "endpoints": ["/", "/health", "/docs"],
        "note": "Backend API is working - no frontend needed"
    }

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "working": True}

# If this doesn't work, nothing will
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
