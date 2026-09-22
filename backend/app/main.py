import logging
import os
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ChatRequest, ChatResponse, HealthResponse
from .service import AnswerService, ServiceConfigurationError, get_answer_service

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Campus Helper API",
    description="문서 검색 결과를 근거로 답변하는 RAG API",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=app.version)


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(
    request: ChatRequest,
    service: Annotated[AnswerService, Depends(get_answer_service)],
) -> ChatResponse:
    try:
        result = service.ask(request.question)
        return ChatResponse(**result)
    except ServiceConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("RAG answer generation failed")
        raise HTTPException(
            status_code=500,
            detail="답변을 생성하지 못했습니다. 잠시 후 다시 시도해주세요.",
        ) from exc
