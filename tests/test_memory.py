"""Tests for OneclawChatMessageHistory and OneclawScratchChatMessageHistory."""

from __future__ import annotations

import json

import pytest
import respx
from langchain_core.messages import AIMessage, HumanMessage, messages_to_dict

from langchain_1claw._client import OneclawClient
from langchain_1claw.memory import OneclawChatMessageHistory, OneclawScratchChatMessageHistory

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


class TestChatMessageHistory:
    def test_empty_on_not_found(self, client, mock_api):
        mock_api.get("/v1/agents/agt/memory/chat_history/sess1").respond(status_code=404)
        history = OneclawChatMessageHistory(client=client, session_id="sess1")
        assert history.messages == []

    def test_loads_persisted_messages(self, client, mock_api):
        msgs = [HumanMessage(content="hi"), AIMessage(content="hello")]
        serialized = json.dumps(messages_to_dict(msgs))
        mock_api.get("/v1/agents/agt/memory/chat_history/sess1").respond(json={"value": serialized})
        history = OneclawChatMessageHistory(client=client, session_id="sess1")
        loaded = history.messages
        assert len(loaded) == 2
        assert loaded[0].content == "hi"
        assert loaded[1].content == "hello"

    def test_add_message_persists(self, client, mock_api):
        mock_api.get("/v1/agents/agt/memory/chat_history/sess2").respond(status_code=404)
        mock_api.put("/v1/agents/agt/memory/chat_history/sess2").respond(json={})
        history = OneclawChatMessageHistory(client=client, session_id="sess2")
        history.add_message(HumanMessage(content="test"))

    def test_clear_deletes(self, client, mock_api):
        mock_api.delete("/v1/agents/agt/memory/chat_history/sess3").respond(json={})
        history = OneclawChatMessageHistory(client=client, session_id="sess3")
        history.clear()

    def test_max_messages_trims(self, client, mock_api):
        existing = [HumanMessage(content=f"msg{i}") for i in range(5)]
        serialized = json.dumps(messages_to_dict(existing))
        mock_api.get("/v1/agents/agt/memory/chat_history/sess4").respond(json={"value": serialized})
        mock_api.put("/v1/agents/agt/memory/chat_history/sess4").respond(json={})
        history = OneclawChatMessageHistory(client=client, session_id="sess4", max_messages=3)
        history.add_message(AIMessage(content="new"))
        # Should have trimmed to 3 most recent


class TestScratchHistory:
    def test_uses_scratch_tier(self, client, mock_api):
        mock_api.get("/v1/agents/agt/memory/chat_scratch/s1").respond(status_code=404)
        mock_api.put("/v1/agents/agt/memory/chat_scratch/s1").respond(json={})
        history = OneclawScratchChatMessageHistory(client=client, session_id="s1", ttl_secs=600)
        history.add_message(HumanMessage(content="ephemeral"))
