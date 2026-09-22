import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .service import ServiceConfigurationError

load_dotenv()

PROMPT = PromptTemplate(
    template="""당신은 학사 안내 문서를 바탕으로 답변하는 도우미입니다.
아래 문서에서 확인되는 내용만 사용하세요.
근거가 없으면 '제공된 문서에서는 확인할 수 없습니다'라고 답하세요.

문서:
{context}

질문: {question}
답변:""",
    input_variables=["context", "question"],
)


def load_documents(data_path: Path) -> list[Document]:
    try:
        raw_documents = json.loads(data_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ServiceConfigurationError(
            f"문서 파일을 찾을 수 없습니다: {data_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ServiceConfigurationError(
            "문서 파일이 올바른 JSON 형식이 아닙니다."
        ) from exc

    if not isinstance(raw_documents, list) or not raw_documents:
        raise ServiceConfigurationError("문서 목록이 비어 있습니다.")

    documents: list[Document] = []
    for index, item in enumerate(raw_documents):
        if not isinstance(item, dict):
            raise ServiceConfigurationError(f"{index}번 문서 형식이 올바르지 않습니다.")

        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        content = str(item.get("content", "")).strip()
        if not title or not url or not content:
            raise ServiceConfigurationError(
                f"{index}번 문서에 title, url, content가 모두 필요합니다."
            )

        documents.append(
            Document(page_content=content, metadata={"title": title, "url": url})
        )

    return documents


class RAGService:
    def __init__(
        self,
        data_path: Path,
        chroma_path: Path,
        api_key: str,
        chat_model: str,
        embedding_model: str,
    ) -> None:
        if not api_key:
            raise ServiceConfigurationError("OPENAI_API_KEY가 설정되지 않았습니다.")

        self.data_path = data_path
        self.chroma_path = chroma_path
        self.embeddings = OpenAIEmbeddings(model=embedding_model, api_key=api_key)
        self.llm = ChatOpenAI(model=chat_model, temperature=0, api_key=api_key)
        self.vectorstore = self._load_or_create_vectorstore()
        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT},
        )

    @classmethod
    def from_environment(cls) -> "RAGService":
        return cls(
            data_path=Path(
                os.getenv("RAG_DATA_PATH", "backend/data/sample_documents.json")
            ),
            chroma_path=Path(os.getenv("CHROMA_PATH", ".cache/chroma")),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ),
        )

    def _load_or_create_vectorstore(self) -> Chroma:
        fingerprint = hashlib.sha256(self.data_path.read_bytes()).hexdigest()
        marker = self.chroma_path / ".source-sha256"

        if marker.exists() and marker.read_text(encoding="utf-8") == fingerprint:
            return Chroma(
                persist_directory=str(self.chroma_path),
                embedding_function=self.embeddings,
            )

        if self.chroma_path.exists():
            shutil.rmtree(self.chroma_path)

        source_documents = load_documents(self.data_path)
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
        ).split_documents(source_documents)

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(self.chroma_path),
        )
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        marker.write_text(fingerprint, encoding="utf-8")
        return vectorstore

    def ask(self, question: str) -> dict[str, Any]:
        result = self.chain.invoke({"query": question})
        sources = []
        seen: set[tuple[str, str]] = set()

        for document in result["source_documents"]:
            title = str(document.metadata.get("title", "제목 없음"))
            url = str(document.metadata.get("url", ""))
            identity = (title, url)
            if identity in seen:
                continue
            seen.add(identity)
            sources.append(
                {
                    "title": title,
                    "url": url,
                    "excerpt": document.page_content[:240],
                }
            )

        return {"answer": result["result"], "sources": sources}
