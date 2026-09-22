from functools import lru_cache
from typing import Protocol


class AnswerService(Protocol):
    def ask(self, question: str) -> dict: ...


class ServiceConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_answer_service() -> AnswerService:
    # 무거운 RAG 의존성은 실제 요청이 들어왔을 때만 불러온다.
    from .rag_service import RAGService

    return RAGService.from_environment()
