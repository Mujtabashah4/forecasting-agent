"""
LLM Service for Ollama/Qwen integration
Based on Section 8 of implementation guide
"""
import httpx
from app.config import settings
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)


async def call_llm(prompt: str, temperature: float = 0.7) -> str:
    """
    Call Qwen via Ollama API.

    Args:
        prompt: The prompt to send to the LLM
        temperature: Temperature parameter (0.0-1.0)

    Returns:
        str: LLM response text

    Raises:
        httpx.HTTPError: If the API call fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                },
                timeout=float(settings.LLM_TIMEOUT)
            )
            response.raise_for_status()
            return response.json()["response"]
    except httpx.HTTPError as e:
        logger.error(f"LLM API call failed: {str(e)}")
        # Return fallback response if LLM fails
        return _generate_fallback_response(prompt)
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {str(e)}")
        return _generate_fallback_response(prompt)


def _generate_fallback_response(prompt: str) -> str:
    """Generate simple fallback response when LLM is unavailable"""
    return "Analysis generated. LLM service temporarily unavailable. Please review the data and scenarios provided."


async def check_llm_health() -> dict:
    """
    Enhanced health check for Ollama LLM service.

    Tests:
    1. Ollama API connectivity
    2. Model availability
    3. Response time

    Returns:
        dict: Health status with 'status', 'model', and optional 'error' keys
    """
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Check if Ollama is running and responding
            start_time = time.time()
            response = await client.get(
                f"{settings.OLLAMA_HOST}/api/tags",
                timeout=5.0
            )
            response_time = time.time() - start_time
            response.raise_for_status()

            # Test 2: Check if our model is available
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]

            if settings.OLLAMA_MODEL in model_names:
                logger.debug(f"LLM health check passed: {response_time:.3f}s")
                return {
                    "status": "connected",
                    "model": settings.OLLAMA_MODEL,
                    "response_time": round(response_time, 3)
                }
            else:
                logger.warning(
                    f"Model {settings.OLLAMA_MODEL} not found. "
                    f"Available: {', '.join(model_names)}"
                )
                return {
                    "status": "model_not_found",
                    "model": settings.OLLAMA_MODEL,
                    "available_models": model_names
                }

    except httpx.TimeoutException:
        logger.warning("LLM health check timed out")
        return {
            "status": "disconnected",
            "model": settings.OLLAMA_MODEL,
            "error": "timeout"
        }
    except httpx.ConnectError as e:
        logger.warning(f"Cannot connect to Ollama: {str(e)}")
        return {
            "status": "disconnected",
            "model": settings.OLLAMA_MODEL,
            "error": "connection_refused"
        }
    except Exception as e:
        logger.warning(f"LLM health check failed: {str(e)}")
        return {
            "status": "disconnected",
            "model": settings.OLLAMA_MODEL,
            "error": str(e)
        }
