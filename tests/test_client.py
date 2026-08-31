"""Tests for OneclawClient — token exchange, secrets, memory, signing."""

from __future__ import annotations

import pytest
import respx

from langchain_1claw._client import (
    OneclawAuthError,
    OneclawClient,
    OneclawNotFoundError,
    OneclawValidationError,
)

BASE = "https://api.1claw.co"
TOKEN_RESP = {
    "access_token": "jwt_test_token",
    "expires_in": 3600,
    "agent_id": "agt-uuid",
    "vault_ids": ["vault-uuid"],
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


# --- auth ---


class TestAuth:
    def test_auto_resolves_agent_id(self, client: OneclawClient, mock_api):
        assert client.agent_id == "agt-uuid"

    def test_auto_resolves_vault_id(self, client: OneclawClient, mock_api):
        assert client.vault_id == "vault-uuid"

    def test_auth_failure_raises(self, mock_api):
        mock_api.post("/v1/auth/agent-token").respond(status_code=401)
        c = OneclawClient(api_key="ocv_bad", base_url=BASE)
        with pytest.raises(OneclawAuthError):
            c.agent_id

    def test_explicit_ids_skip_resolution(self, mock_api):
        c = OneclawClient(api_key="ocv_x", agent_id="my-agent", vault_id="my-vault", base_url=BASE)
        mock_api.post("/v1/auth/agent-token").respond(json=TOKEN_RESP)
        mock_api.get("/v1/vaults/my-vault/secrets/test").respond(json={"value": "secret"})
        assert c.get_secret("test") == "secret"
        c.close()


# --- secrets ---


class TestSecrets:
    def test_get_secret(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/vaults/vault-uuid/secrets/api-keys%2Fopenai").respond(
            json={"value": "sk-test"}
        )
        assert client.get_secret("api-keys/openai") == "sk-test"

    def test_get_secret_not_found(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/vaults/vault-uuid/secrets/missing").respond(status_code=404)
        with pytest.raises(OneclawNotFoundError):
            client.get_secret("missing")

    def test_put_secret(self, client: OneclawClient, mock_api):
        mock_api.put("/v1/vaults/vault-uuid/secrets/new-key").respond(json={"version": 1})
        result = client.put_secret("new-key", "value123")
        assert result["version"] == 1

    def test_list_secrets(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/vaults/vault-uuid/secrets").respond(
            json={"secrets": [{"path": "a"}, {"path": "b"}]}
        )
        secrets = client.list_secrets()
        assert len(secrets) == 2

    def test_delete_secret(self, client: OneclawClient, mock_api):
        mock_api.delete("/v1/vaults/vault-uuid/secrets/old").respond(json={"deleted": True})
        result = client.delete_secret("old")
        assert result["deleted"] is True

    def test_rotate_secret(self, client: OneclawClient, mock_api):
        mock_api.post("/v1/vaults/vault-uuid/secret-rotate/creds%2Fdb").respond(
            json={"version": 2, "value": "new_random"}
        )
        result = client.rotate_secret("creds/db", length=64, charset="hex")
        assert result["version"] == 2


# --- memory ---


class TestMemory:
    def test_memory_put(self, client: OneclawClient, mock_api):
        mock_api.put("/v1/agents/agt-uuid/memory/default/test-key").respond(json={"status": "ok"})
        result = client.memory_put("default", "test-key", "test-value")
        assert result["status"] == "ok"

    def test_memory_get(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/memory/default/test-key").respond(
            json={"value": "stored"}
        )
        assert client.memory_get("default", "test-key") == "stored"

    def test_memory_get_not_found(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/memory/default/missing").respond(status_code=404)
        assert client.memory_get("default", "missing") is None

    def test_memory_list(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/memory/ns").respond(
            json={"entries": [{"key": "a"}, {"key": "b"}]}
        )
        entries = client.memory_list("ns")
        assert len(entries) == 2

    def test_memory_search(self, client: OneclawClient, mock_api):
        mock_api.post("/v1/agents/agt-uuid/memory/search").respond(
            json={"results": [{"key": "k1", "value": "v1", "score": 0.95}]}
        )
        results = client.memory_search("default", "query")
        assert results[0]["score"] == 0.95

    def test_memory_delete(self, client: OneclawClient, mock_api):
        mock_api.delete("/v1/agents/agt-uuid/memory/ns/k").respond(json={})
        client.memory_delete("ns", "k")

    def test_memory_list_namespaces(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/memory").respond(
            json={"namespaces": ["chat_history", "knowledge"]}
        )
        ns = client.memory_list_namespaces()
        assert "knowledge" in ns


# --- signing ---


class TestSigning:
    def test_sign_message(self, client: OneclawClient, mock_api):
        mock_api.post("/v1/agents/agt-uuid/sign").respond(
            json={"signature": "0xabc", "message_hash": "0x123", "from": "0xdef"}
        )
        result = client.sign_message("Hello", chain="ethereum")
        assert result["signature"] == "0xabc"

    def test_submit_transaction(self, client: OneclawClient, mock_api):
        mock_api.post("/v1/agents/agt-uuid/transactions").respond(
            json={"tx_hash": "0x999", "status": "broadcast"}
        )
        result = client.submit_transaction(chain="ethereum", to="0xrecipient", value="0.01")
        assert result["status"] == "broadcast"

    def test_list_signing_keys(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/signing-keys").respond(
            json={"signing_keys": [{"chain": "ethereum", "address": "0xabc"}]}
        )
        keys = client.list_signing_keys()
        assert keys[0]["chain"] == "ethereum"

    def test_get_balance(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/agents/agt-uuid/signing-keys/ethereum/balance").respond(
            json={"native_balance": "1.5", "chain": "ethereum"}
        )
        result = client.get_signing_key_balance("ethereum")
        assert result["native_balance"] == "1.5"


# --- automations ---


class TestAutomations:
    def test_trigger(self, client: OneclawClient, mock_api):
        mock_api.post("/v1/automations/auto-uuid/trigger").respond(
            json={"run_id": "run-1", "status": "running"}
        )
        result = client.trigger_automation("auto-uuid")
        assert result["status"] == "running"

    def test_list(self, client: OneclawClient, mock_api):
        mock_api.get("/v1/automations").respond(
            json={"automations": [{"id": "a1", "name": "rotate"}]}
        )
        autos = client.list_automations()
        assert len(autos) == 1


# --- error handling ---


class TestErrors:
    def test_validation_error(self, client: OneclawClient, mock_api):
        mock_api.put("/v1/vaults/vault-uuid/secrets/bad").respond(status_code=422)
        with pytest.raises(OneclawValidationError):
            client.put_secret("bad", "")
