from fastapi import FastAPI

# Create the FastAPI app instance
app = FastAPI(title="Aqlify Test", version="1.0.0")

# Simple root route
@app.get("/")
def root():
    return {"message": "SUCCESS! Aqlify is working!", "status": "online"}

@app.get("/test") 
def test():
    return {"test": "working", "routes": "registered"}

@app.get("/health")
def health():
    return {"health": "ok", "app": "running"}
