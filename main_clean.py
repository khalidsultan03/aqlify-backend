from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "✅ AQLIFY BACKEND WORKING!", "status": "success", "working": True}

@app.get("/health")  
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
