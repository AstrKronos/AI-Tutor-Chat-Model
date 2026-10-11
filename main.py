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

from services.ai import generate_tutor_reply

# Load environment variables
load_dotenv()

# Setup console logging for every request and error
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ai_tutor_api")

app = FastAPI(
    title="Class 10 CBSE AI Tutor API",
    description=(
        "Backend API for a Class 10 CBSE AI Tutor supporting 3 function modes "
        "('socratic', 'detailed_explanation', 'exam_ready')."
    ),
    version="1.0.0",
)

# CORS Middleware (Hackathon setup - allowing all origins)
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


# --- Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint to verify backend service status."""
    ai_provider = (os.getenv("AI_PROVIDER") or "opencode").strip().lower()
    if ai_provider == "gemini":
        provider_label = "Google Gemini"
        active_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    elif ai_provider == "nvidia":
        provider_label = "NVIDIA NIM"
        active_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")
    else:
        provider_label = "OpenCode Zen"
        active_model = os.getenv("OPENCODE_MODEL", "nemotron-3.5-lightning-free")

    return {
        "status": "healthy",
        "service": "Class 10 CBSE AI Tutor",
        "provider": provider_label,
        "model": active_model,
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Primary chat endpoint for students.
    Invokes the Class 10 CBSE AI tutor in the selected mode ('socratic', 'detailed_explanation', or 'exam_ready').
    """
    logger.info(
        "[CHAT] Student='%s' (ID=%s) | Mode='%s' | Message='%s'",
        request.student_name,
        request.student_id,
        request.mode,
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
                mode=request.mode or "socratic",
            )
        except TypeError:
            # Backward-compatibility if generate_tutor_reply is mocked with older signature in unit tests
            reply = generate_tutor_reply(
                student_message=request.message,
                history=formatted_history,
            )
        logger.info("[AI SUCCESS] Generated reply for student_id=%s [mode=%s]", request.student_id, request.mode)

    except APITimeoutError as e:
        logger.error("[AI TIMEOUT] Model timed out for student %s: %s", request.student_id, e)
        reply = "I took a little too long thinking about that. Could you ask again or try rephrasing your question?"
        response_status = "fallback"

    except RateLimitError as e:
        logger.error("[AI RATE LIMIT] Rate limit hit from AI service: %s", e)
        reply = "A lot of students are studying right now! Please wait a moment and try asking again."
        response_status = "fallback"

    except APIConnectionError as e:
        logger.error("[AI CONNECTION ERROR] Failed connecting to AI service: %s", e)
        reply = "I'm having a little trouble connecting to my study resources. Please give me a moment and try again."
        response_status = "fallback"

    except Exception as e:
        logger.exception("[AI ERROR] Unexpected error in /chat endpoint: %s", e)
        reply = "Something unexpected happened on my end. Please try asking your question again in a moment!"
        response_status = "fallback"

    return ChatResponse(
        reply=reply,
        status=response_status,
        mode=request.mode or "socratic",
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
