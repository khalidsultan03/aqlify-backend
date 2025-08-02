"""
Minimal test version to debug 404 issues
"""

from fastapi import FastAPI
from datetime import datetime

# Create FastAPI app
app = FastAPI(
    title="Aqlify Test",
    description="Testing deployment",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "✅ Aqlify Backend is LIVE and WORKING!",
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "test": "Root endpoint working correctly"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "aqlify-test"}

@app.get("/test")
def test_endpoint():
    return {"test": "All endpoints working", "success": True}

# No conflicting server config
