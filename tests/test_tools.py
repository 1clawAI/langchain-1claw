"""Tests for LangChain tools."""

from __future__ import annotations

import json

import pytest
import respx

from langchain_1claw._client import OneclawClient
from langchain_1claw.tools import (
    OneclawGetBalanceTool,
    OneclawGetSecretTool,
    OneclawListSecretsTool,
    OneclawMemoryGetTool,
    OneclawMemoryPutTool,
    OneclawMemorySearchTool,
    OneclawPutSecretTool,
    OneclawRotateSecretTool,
    OneclawSignMessageTool,
    OneclawSubmitTransactionTool,
    OneclawTriggerAutomationTool,
    get_all_tools,
)

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


class TestGetSecretTool:
    def test_returns_secret_value(self, client, mock_api):
        mock_api.get("/v1/vaults/vid/secrets/key").respond(json={"value": "s3cret"})
        tool = OneclawGetSecretTool(client=client)
        assert tool.invoke({"path": "key"}) == "s3cret"

    def test_returns_error_on_failure(self, client, mock_api):
        mock_api.get("/v1/vaults/vid/secrets/bad").respond(status_code=403)
        tool = OneclawGetSecretTool(client=client)
        result = tool.invoke({"path": "bad"})
        assert "[1claw error]" in result


class TestPutSecretTool:
    def test_stores_secret(self, client, mock_api):
        mock_api.put("/v1/vaults/vid/secrets/new").respond(json={"version": 1})
        tool = OneclawPutSecretTool(client=client)
        result = tool.invoke({"path": "new", "value": "val"})
        parsed = json.loads(result)
        assert parsed["version"] == 1


class TestListSecretsTool:
    def test_lists_secrets(self, client, mock_api):
        mock_api.get("/v1/vaults/vid/secrets").respond(json={"secrets": [{"path": "a"}]})
        tool = OneclawListSecretsTool(client=client)
        result = json.loads(tool.invoke({}))
        assert len(result) == 1


class TestRotateSecretTool:
    def test_rotates(self, client, mock_api):
        mock_api.post("/v1/vaults/vid/secret-rotate/k").respond(json={"version": 2})
        tool = OneclawRotateSecretTool(client=client)
        result = json.loads(tool.invoke({"path": "k"}))
        assert result["version"] == 2


class TestMemoryTools:
    def test_put(self, client, mock_api):
        mock_api.put("/v1/agents/agt/memory/default/k1").respond(json={})
        tool = OneclawMemoryPutTool(client=client)
        result = tool.invoke({"key": "k1", "value": "v1"})
        assert "Stored" in result

    def test_get(self, client, mock_api):
        mock_api.get("/v1/agents/agt/memory/default/k1").respond(json={"value": "stored_val"})
        tool = OneclawMemoryGetTool(client=client)
        assert tool.invoke({"key": "k1"}) == "stored_val"

    def test_get_not_found(self, client, mock_api):
        mock_api.get("/v1/agents/agt/memory/default/missing").respond(status_code=404)
        tool = OneclawMemoryGetTool(client=client)
        result = tool.invoke({"key": "missing"})
        assert "not found" in result

    def test_search(self, client, mock_api):
        mock_api.post("/v1/agents/agt/memory/search").respond(
            json={"results": [{"key": "k", "value": "v", "score": 0.9}]}
        )
        tool = OneclawMemorySearchTool(client=client)
        results = json.loads(tool.invoke({"query": "test"}))
        assert results[0]["score"] == 0.9


class TestSigningTools:
    def test_sign_message(self, client, mock_api):
        mock_api.post("/v1/agents/agt/sign").respond(json={"signature": "0xabc", "from": "0xdef"})
        tool = OneclawSignMessageTool(client=client)
        result = json.loads(tool.invoke({"message": "hello"}))
        assert result["signature"] == "0xabc"

    def test_submit_transaction(self, client, mock_api):
        mock_api.post("/v1/agents/agt/transactions").respond(
            json={"tx_hash": "0x1", "status": "broadcast"}
        )
        tool = OneclawSubmitTransactionTool(client=client)
        result = json.loads(
            tool.invoke({"chain": "ethereum", "to": "0xrecipient", "value": "0.01"})
        )
        assert result["status"] == "broadcast"

    def test_get_balance(self, client, mock_api):
        mock_api.get("/v1/agents/agt/signing-keys/ethereum/balance").respond(
            json={"native_balance": "1.0"}
        )
        tool = OneclawGetBalanceTool(client=client)
        result = json.loads(tool.invoke({"chain": "ethereum"}))
        assert result["native_balance"] == "1.0"


class TestAutomationTool:
    def test_trigger(self, client, mock_api):
        mock_api.post("/v1/automations/a1/trigger").respond(
            json={"run_id": "r1", "status": "running"}
        )
        tool = OneclawTriggerAutomationTool(client=client)
        result = json.loads(tool.invoke({"automation_id": "a1"}))
        assert result["status"] == "running"


class TestGetAllTools:
    def test_returns_all_tools(self, client):
        tools = get_all_tools(client)
        assert len(tools) == 13
        names = {t.name for t in tools}
        assert "oneclaw_get_secret" in names
        assert "oneclaw_submit_transaction" in names
        assert "oneclaw_memory_search" in names
