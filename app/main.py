from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
from app.routes.weather import router as weather_router
from app.routes.rag import router as rag_router
from app.routes.auth import router as auth_router 
from app.database import create_db               
import os
import google.generativeai as genai
from app.config import GROQ_API_KEY



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    # Startup: Initialize Gemini client or DB connections here
    if GROQ_API_KEY:
        genai.configure(api_key=GROQ_API_KEY)
    yield
    # Shutdown: Clean up resources

# 2. Use ORJSONResponse for faster JSON serialization
app = FastAPI(docs_url="/", redoc_url=None, title="IoT Weather API", version="1.0.0")

# 3. Secure CORS: Dynamic origins from environment variables
# Avoid "*" in production; explicitly list trusted domains
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173, http://192.168.0.1:8086").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

# 4. Structured Routing
app.include_router(weather_router, prefix="/api/weather", tags=["weather"])
app.include_router(rag_router, prefix="/api/rag", tags=["AI Assistant"])
app.include_router(auth_router)

# 5. Lightweight Health Check
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "version": "1.1.0"}