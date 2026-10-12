import logging
import os
import time
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from openai import APIConnectionError, APITimeoutError, RateLimitError
from pydantic import BaseModel, Field, field_validator

from services.ai import generate_tutor_reply, normalize_grade

# Load environment variables
load_dotenv()

# Setup console logging for every request and error
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_tutor_api")

app = FastAPI(
    title="CBSE AI Tutor API (Classes 9th to 12th — Local Qwen 2.5 7B)",
    description=(
        "Offline local backend API for a CBSE AI Tutor running natively on Qwen 2.5 7B, "
        "supporting Classes 9th to 12th and 3 function modes ('socratic', 'detailed_explanation', 'exam_ready')."
    ),
    version="2.0.0",
)

# CORS Middleware (allowing all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Error Logging Middleware / Handlers ---

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    """Log every incoming HTTP request, its status code, and processing duration."""
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "[REQUEST] %s %s from %s",
        request.method,
        request.url.path,
        client_ip,
    )
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "[RESPONSE] %s %s -> Status %d (%.2f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "[UNHANDLED ERROR] %s %s failed after %.2f ms: %s",
            request.method,
            request.url.path,
            elapsed_ms,
            exc,
        )
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log request validation errors clearly to the console for easier frontend integration debugging."""
    logger.warning(
        "[VALIDATION ERROR] %s %s - Details: %s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return await request_validation_exception_handler(request, exc)


# --- Request and Response Schemas ---

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message sender role: 'user' or 'assistant'")
    content: str = Field(..., max_length=2000, description="Content of the message")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role_cleaned = value.strip().lower()
        if role_cleaned not in ("user", "assistant"):
            raise ValueError("Role must be either 'user' or 'assistant'")
        return role_cleaned

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Content cannot be empty or only whitespace")
        return cleaned


class ChatRequest(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=100, description="Unique student identifier")
    student_name: str = Field(..., min_length=1, max_length=100, description="Student's name")
    message: str = Field(..., min_length=1, max_length=1000, description="Student's question or message (max 1000 chars)")
    grade: Optional[str] = Field(
        default="10",
        description="Student's grade/class from 9th to 12th: '9', '10', '11', or '12'",
    )
    history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Optional conversation history list of previous user/assistant messages",
    )
    mode: Optional[str] = Field(
        default="socratic",
        description="Tutoring mode matching frontend options: 'socratic' (Socratic Method), 'detailed_explanation' (Detailed Explanation), or 'exam_ready' (Exam Ready)",
    )

    @field_validator("student_id", "student_name", "message")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or contain only whitespace.")
        return cleaned

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, value: Optional[str]) -> str:
        return normalize_grade(value)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, value: Optional[str]) -> str:
        if not value:
            return "socratic"
        normalized = value.strip().lower().replace(" ", "_").replace("-", "_")
        if normalized not in ("socratic", "detailed_explanation", "exam_ready"):
            raise ValueError("mode must be 'socratic', 'detailed_explanation', or 'exam_ready'")
        return normalized


class ChatResponse(BaseModel):
    reply: str = Field(..., description="The AI tutor's response message")
    status: str = Field(..., description="Status of the response ('success' or 'fallback')")
    mode: str = Field(default="socratic", description="Active tutoring mode applied to the response")
    grade: str = Field(default="10", description="Active student grade ('9', '10', '11', or '12')")


# --- Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify local backend service status."""
    return {
        "status": "healthy",
        "service": "CBSE AI Tutor (Classes 9th to 12th)",
        "supported_grades": ["9", "10", "11", "12"],
        "provider": "Local Ollama (Offline)",
        "model": os.getenv("LOCAL_MODEL", "qwen2.5:7b"),
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Primary chat endpoint for students (Classes 9th to 12th).
    Invokes the local Qwen 2.5 7B CBSE AI tutor in the selected grade ('9'–'12') and mode.
    """
    active_grade = request.grade or "10"
    active_mode = request.mode or "socratic"

    logger.info(
        "[CHAT] Student='%s' (ID=%s) | Grade='%s' | Mode='%s' | Message='%s'",
        request.student_name,
        request.student_id,
        active_grade,
        active_mode,
        request.message[:80] + ("..." if len(request.message) > 80 else ""),
    )

    formatted_history = None
    if request.history:
        formatted_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]

    reply = ""
    response_status = "success"

    try:
        try:
            reply = generate_tutor_reply(
                student_message=request.message,
                history=formatted_history,
                mode=active_mode,
                grade=active_grade,
            )
        except TypeError:
            reply = generate_tutor_reply(
                student_message=request.message,
                history=formatted_history,
            )
        logger.info(
            "[AI SUCCESS] Generated reply for student_id=%s [grade=%s, mode=%s]",
            request.student_id,
            active_grade,
            active_mode,
        )

    except APITimeoutError as e:
        logger.error("[AI TIMEOUT] Local model timed out for student %s: %s", request.student_id, e)
        reply = "I took a little too long thinking about that. Could you ask again or try rephrasing your question?"
        response_status = "fallback"

    except RateLimitError as e:
        logger.error("[AI RATE LIMIT] Rate limit hit: %s", e)
        reply = "Please wait a moment and try asking again."
        response_status = "fallback"

    except APIConnectionError as e:
        logger.error("[AI CONNECTION ERROR] Local Ollama server not reachable: %s", e)
        reply = "I couldn't connect to the local Qwen 2.5 7B engine (http://localhost:11434). Make sure Ollama is running!"
        response_status = "fallback"

    except Exception as e:
        logger.exception("[AI ERROR] Unexpected error in /chat endpoint: %s", e)
        reply = "Something unexpected happened on my end. Please make sure the local Qwen 2.5 7B model is loaded and try again!"
        response_status = "fallback"

    return ChatResponse(
        reply=reply,
        status=response_status,
        mode=active_mode,
        grade=active_grade,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
