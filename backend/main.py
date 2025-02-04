# app/main.py updates
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.auth import get_current_user
from app.api.shows import router as shows_router, cache_manager

app = FastAPI(title="The Jauntee Stream API")

# Protected route example
@app.get("/api/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(shows_router, prefix="/api/shows", tags=["shows"])
# app.include_router(app.api.songs.router, prefix="/api/songs", tags=["songs"])

# Add to main.py
async def start_cache_worker():
    await cache_manager.start_cache_worker()

# @app.on_event("startup")
# async def startup_event():
#     async.create_task(start_cache_worker())