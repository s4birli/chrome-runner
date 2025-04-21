from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime

from routers.youtube import router as youtube_router

app = FastAPI(
    title="YouTube Endpoint",
    description="API for YouTube related operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(youtube_router)

@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Endpoint API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 