#!/usr/bin/env python3

# RENDER.COM DEBUG VERSION
# This file is designed to diagnose Render deployment issues

import os
import sys
from fastapi import FastAPI

print("=== AQLIFY DEPLOYMENT DEBUG ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print(f"PORT environment variable: {os.environ.get('PORT', 'NOT SET')}")
print("=== STARTING FASTAPI APP ===")

app = FastAPI(
    title="Aqlify Debug Version",
    description="Debugging Render deployment issues",
    version="debug-1.0"
)

@app.get("/")
def root():
    return {
        "message": "🔧 AQLIFY DEBUG VERSION - SUCCESS!",
        "status": "WORKING",
        "deployment": "RENDER.COM",
        "debug_info": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "port": os.environ.get('PORT', '8000'),
            "files_count": len(os.listdir('.')),
        },
        "test": "If you see this, the deployment is working!"
    }

@app.get("/debug")
def debug_info():
    return {
        "environment_variables": dict(os.environ),
        "current_directory": os.getcwd(),
        "directory_contents": os.listdir('.'),
        "python_path": sys.path
    }

@app.get("/health")
def health():
    return {"status": "healthy", "debug": True}

# Make sure this runs
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
else:
    print("App module loaded successfully")
