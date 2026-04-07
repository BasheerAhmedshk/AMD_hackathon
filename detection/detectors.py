import time
from typing import Dict, Any
import structlog
from config.settings import settings
from ml.models import engine
from storage.cache import get_cached_result, set_cached_result, generate_cache_key

log = structlog.get_logger()

def calculate_severity(confidence: float, threshold: float) -> str:
    """Maps confidence to Nadiaris Labs severity levels."""
    if confidence < threshold:
        return "LOW"
    elif confidence >= 0.85:
        return "CRITICAL"
    elif confidence >= 0.70:
        return "HIGH"
    return "MEDIUM"

async def analyze_threat(task: str, input_text: str, threshold: float) -> Dict[str, Any]:
    """
    Core pipeline: Cache Check -> GPU Inference -> Result Formatting.
    """
    start_time = time.perf_counter()
    cache_key = generate_cache_key(task, input_text)
    
    # 1. Check Redis Cache
    cached_data = await get_cached_result(cache_key)
    if cached_data:
        cached_data["cached"] = True
        cached_data["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
        return cached_data

    # 2. Run GPU Inference (via ml/models.py)
    try:
        if task == "phishing":
            prediction = engine.phishing.predict(input_text)
        elif task == "malware":
            prediction = engine.malware.predict(input_text)
        else:
            raise ValueError(f"Unknown task: {task}")
    except Exception as e:
        log.error("Inference failed", task=task, error=str(e))
        raise

    confidence = prediction["confidence"]
    # Usually index 1 is the positive/threat class in these HF models
    is_threat = bool(prediction["label_id"] == 1 and confidence >= threshold)
    
    result = {
        "task": task,
        "is_threat": is_threat,
        "confidence": round(confidence, 4),
        "severity": calculate_severity(confidence, threshold) if is_threat else "SAFE",
        "provider": prediction["provider"],
        "cached": False
    }

    # 3. Save to Redis
    await set_cached_result(cache_key, result)

    # Calculate final latency
    result["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
    return result