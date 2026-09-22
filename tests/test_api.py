from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.service import get_answer_service


class FakeAnswerService:
    def ask(self, question: str) -> dict:
        return {
            "answer": f"테스트 답변: {question}",
            "sources": [
                {
                    "title": "테스트 문서",
                    "url": "https://example.com/test",
                    "excerpt": "테스트 근거입니다.",
                }
            ],
        }


client = TestClient(app)


def setup_function() -> None:
    app.dependency_overrides[get_answer_service] = lambda: FakeAnswerService()


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_chat_returns_answer_and_sources() -> None:
    response = client.post("/chat", json={"question": "수강신청은 언제야?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "테스트 답변: 수강신청은 언제야?"
    assert response.json()["sources"][0]["title"] == "테스트 문서"


def test_chat_rejects_blank_question() -> None:
    response = client.post("/chat", json={"question": "   "})

    assert response.status_code == 422


def test_chat_rejects_overlong_question() -> None:
    response = client.post("/chat", json={"question": "가" * 501})

    assert response.status_code == 422
