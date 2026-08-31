"""Tests for OneclawMemoryRetriever."""

from __future__ import annotations

import pytest
import respx

from langchain_1claw._client import OneclawClient
from langchain_1claw.retrievers import OneclawMemoryRetriever

BASE = "https://api.1claw.co"
TOKEN_RESP = {
    "access_token": "jwt_test",
    "expires_in": 3600,
    "agent_id": "agt",
    "vault_ids": ["vid"],
}


@pytest.fixture
def mock_api():
    with respx.mock(base_url=BASE, assert_all_called=False) as mock:
        mock.post("/v1/auth/agent-token").respond(json=TOKEN_RESP)
        yield mock


@pytest.fixture
def client(mock_api):
    c = OneclawClient(api_key="ocv_test", base_url=BASE)
    yield c
    c.close()


class TestRetriever:
    def test_returns_documents(self, client, mock_api):
        mock_api.post("/v1/agents/agt/memory/search").respond(
            json={
                "results": [
                    {
                        "key": "deploy-guide",
                        "value": "Run `make deploy`",
                        "score": 0.92,
                        "tier": "semantic",
                    },
                    {
                        "key": "test-guide",
                        "value": "Run `pytest`",
                        "score": 0.85,
                        "tier": "semantic",
                    },
                ]
            }
        )
        retriever = OneclawMemoryRetriever(client=client, namespace="docs", top_k=5)
        docs = retriever.invoke("How do I deploy?")
        assert len(docs) == 2
        assert "make deploy" in docs[0].page_content.lower()
        assert docs[0].metadata["key"] == "deploy-guide"
        assert docs[0].metadata["namespace"] == "docs"
        assert docs[0].metadata["score"] == 0.92

    def test_empty_on_no_results(self, client, mock_api):
        mock_api.post("/v1/agents/agt/memory/search").respond(json={"results": []})
        retriever = OneclawMemoryRetriever(client=client, namespace="empty")
        docs = retriever.invoke("anything")
        assert docs == []

    def test_empty_on_error(self, client, mock_api):
        mock_api.post("/v1/agents/agt/memory/search").respond(status_code=500)
        retriever = OneclawMemoryRetriever(client=client, namespace="broken")
        docs = retriever.invoke("query")
        assert docs == []
