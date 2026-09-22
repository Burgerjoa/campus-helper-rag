import json

import pytest

from backend.app.rag_service import load_documents
from backend.app.service import ServiceConfigurationError


def test_load_documents_reads_required_fields(tmp_path) -> None:
    data_path = tmp_path / "documents.json"
    data_path.write_text(
        json.dumps(
            [
                {
                    "title": "테스트 공지",
                    "url": "https://example.com/notice",
                    "content": "테스트 내용",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    documents = load_documents(data_path)

    assert documents[0].page_content == "테스트 내용"
    assert documents[0].metadata["title"] == "테스트 공지"


def test_load_documents_rejects_missing_content(tmp_path) -> None:
    data_path = tmp_path / "documents.json"
    data_path.write_text(
        '[{"title": "테스트", "url": "https://example.com"}]',
        encoding="utf-8",
    )

    with pytest.raises(ServiceConfigurationError):
        load_documents(data_path)
