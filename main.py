import time
import hashlib
import os
import redis.asyncio as redis
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

# Importing your specific configurations from database.py
from config.settings import settings
from storage.database import init_db, AsyncSessionLocal, ThreatLog

logger = structlog.get_logger()

# 1. Configure AI and Redis
genai.configure(api_key=settings.GEMINI_API_KEY)
ai_model = genai.GenerativeModel('gemini-2.5-flash')

# Connect to your Podman Redis container
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# 2. Define the Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Nadiaris Labs Threat Audit API...")
    await init_db()
    # Ping Redis to make sure the container is awake
    await redis_client.ping()
    logger.info("Database AND Redis Cache connections established!")
    yield
    await redis_client.aclose()
    logger.info("Shutting down server...")

# 3. Initialize FastAPI
app = FastAPI(
    title="Nadiaris Labs Threat Audit API",
    description="AI-powered code vulnerability and malware scanning.",
    version="1.0.0",
    lifespan=lifespan
)

class ScanRequest(BaseModel):
    code_snippet: str

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# 4. The Core API Endpoint (Now with Caching!)
@app.post("/api/v1/scan")
async def scan_code(request: ScanRequest, db: AsyncSession = Depends(get_db)):
    logger.info("Received new code snippet for threat analysis.")
    start_time = time.time()
    
    # --- PHASE 5: THE REDIS CACHE CHECK ---
    # Turn the code snippet into a unique, tiny 64-character hash
    code_hash = hashlib.sha256(request.code_snippet.encode('utf-8')).hexdigest()
    cache_key = f"scan:{code_hash}"
    
    # Ask Redis: "Have we seen this exact code before?"
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        # CACHE HIT! Return the answer instantly without calling Gemini
        latency = (time.time() - start_time) * 1000
        logger.info("CACHE HIT! Returning lightning-fast response.", latency_ms=latency)
        return {
            "status": "success (cached)",
            "latency_ms": round(latency, 2),
            "analysis": cached_result
        }

    # --- CACHE MISS: Ask Gemini ---
    prompt = f"""
    Act as an expert cybersecurity auditor. Analyze the following code snippet for malware, 
    vulnerabilities, or malicious intent. Be concise.
    
    Code to analyze:
    ```
    {request.code_snippet}
    ```
    """
    
    try:
        response = await ai_model.generate_content_async(prompt)
        analysis_text = getattr(response, "text", "No response from AI")
        latency = (time.time() - start_time) * 1000
        
        # Save to Postgres Vault
        new_audit = ThreatLog(
            task="gemini_code_scan",
            is_threat=True if "malware" in analysis_text.lower() or "critical" in analysis_text.lower() else False,
            confidence=0.99,
            severity="HIGH" if "critical" in analysis_text.lower() else "MEDIUM",
            provider_used="gemini-2.5-flash",
            latency_ms=latency,
            explanation_json={"code_snippet": request.code_snippet, "ai_analysis": analysis_text}
        )
        db.add(new_audit)
        await db.commit()          
        await db.refresh(new_audit) 
        
        # --- PHASE 5: SAVE TO REDIS ---
        # Save the Gemini answer in Redis for 24 hours (86400 seconds)
        await redis_client.setex(cache_key, 86400, analysis_text)
        
        logger.info("Successfully generated and saved threat analysis.", audit_id=str(new_audit.id))
        
        return {
            "status": "success",
            "log_id": str(new_audit.id),
            "latency_ms": round(latency, 2),
            "analysis": analysis_text
        }
        
    except Exception as e:
        logger.error("Failed to process scan", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error during analysis.")