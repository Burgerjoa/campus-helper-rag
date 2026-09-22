# Campus Helper RAG

대학 공지처럼 여러 문서에 흩어진 정보를 검색하고, 검색된 문서를 근거로 답변하는 RAG 챗봇 예제입니다.

이 저장소는 졸업작품으로 만든 학사 정보 챗봇을 공개 포트폴리오용으로 정리한 버전입니다. 원본 수집 데이터와 학교 연락처는 포함하지 않고, 동작 구조를 확인할 수 있는 익명 예시 문서만 제공합니다.

```text
질문
  ↓
FastAPI 입력 검증
  ↓
ChromaDB 유사도 검색 (Top 3)
  ↓
검색 문서 + 질문을 LLM에 전달
  ↓
답변 + 참고 문서 반환
  ↓
Streamlit UI 표시
```

## 주요 기능

- JSON 문서를 500자 단위로 분할하고 ChromaDB에 적재
- 질문과 가까운 문서 3개를 검색해 답변 컨텍스트로 사용
- 답변과 함께 문서 제목, URL, 발췌문 반환
- FastAPI와 Streamlit을 분리해 API를 다른 클라이언트에서도 재사용
- 데이터 변경 시 해시를 비교해 로컬 벡터 저장소 재생성
- 입력 길이, 빈 질문, 서버 오류를 API 경계에서 처리

## 기술 선택

### FastAPI와 Streamlit 분리

RAG 로직을 Streamlit 안에 직접 넣으면 화면과 검색 로직의 실행 주기가 결합됩니다. 검색·답변 흐름을 FastAPI로 분리해 웹이나 모바일 클라이언트가 추가되어도 같은 API를 사용할 수 있도록 했습니다.

### ChromaDB

졸업작품 규모에서 별도 검색 서버를 운영하지 않고 로컬에 벡터를 저장하기 위해 선택했습니다. 대규모 운영 환경이라면 데이터 갱신, 동시성, 백업을 고려해 관리형 벡터 DB를 다시 검토해야 합니다.

### 익명 샘플 데이터

원본 저장소에는 학교 공지 수집 데이터가 있었지만 공개 저장소에는 포함하지 않았습니다. `backend/data/sample_documents.json`은 코드 실행 확인만을 위한 가상 데이터이며 실제 학사 정보가 아닙니다.

## 프로젝트 구조

```text
campus-helper-rag/
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI 엔드포인트와 오류 처리
│  │  ├─ rag_service.py   # 문서 로드, 벡터 검색, 답변 생성
│  │  ├─ schemas.py       # 요청·응답 모델
│  │  └─ service.py       # 서비스 인터페이스와 의존성 주입
│  └─ data/
│     └─ sample_documents.json
├─ frontend/
│  └─ app.py              # Streamlit 채팅 UI
└─ tests/
   ├─ test_api.py
   └─ test_documents.py
```

## 실행

Python 3.11을 권장합니다.

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

`.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`를 입력합니다.

백엔드:

```bash
uvicorn backend.app.main:app --reload
```

프론트엔드:

```bash
streamlit run frontend/app.py
```

- API 문서: <http://localhost:8000/docs>
- Streamlit: <http://localhost:8501>

## 테스트

외부 API를 호출하지 않는 가짜 서비스로 요청 검증과 응답 형식을 확인합니다.

```bash
pip install -r requirements-dev.txt
ruff check .
ruff format --check .
pytest -q
```

## AI 도구 사용 원칙

AI 도구는 구조 대안 탐색, 반복 코드 초안, 테스트 누락 확인에 사용했습니다. 생성된 내용을 그대로 채택하지 않고 다음 순서로 검증했습니다.

1. 사용 중인 라이브러리의 문서와 실제 인터페이스 확인
2. 오류 재현과 입출력 경계 확인
3. 자동 테스트와 로컬 실행으로 결과 확인
4. 프로젝트 제약에 맞는지 직접 판단한 뒤 반영

## 제한사항

- 공개 저장소에는 실제 학교 데이터와 운영 사용자 정보가 없습니다.
- OpenAI API 키와 사용 비용이 필요합니다.
- 로컬 ChromaDB는 단일 인스턴스 데모용 선택이며 운영 확장성을 검증하지 않았습니다.
- 실제 서비스 배포·사용자 규모·처리량 개선 성과를 주장하지 않습니다.
