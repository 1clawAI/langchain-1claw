"""LangChain tools for 1Claw — secrets, signing, memory, and automations.

Each tool wraps a 1Claw API endpoint and follows LangChain's ``BaseTool``
contract. All tools accept a shared ``OneclawClient`` instance.

Example::

    from langchain_1claw import OneclawClient, OneclawGetSecretTool

    client = OneclawClient(api_key="ocv_...")
    tool = OneclawGetSecretTool(client=client)
    result = tool.invoke({"path": "api-keys/openai"})
"""

from __future__ import annotations

import json

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from ._client import OneclawClient, OneclawError

# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------


class _GetSecretInput(BaseModel):
    path: str = Field(..., description="Secret path in the vault, e.g. 'api-keys/openai'")
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawGetSecretTool(BaseTool):
    """Fetch a decrypted secret from an HSM-backed 1Claw vault."""

    name: str = "oneclaw_get_secret"
    description: str = (
        "Fetch a secret value from the 1Claw vault by its path. Use this whenever "
        "you need an API key, token, connection string, or credential. Never ask the "
        "user to paste credentials — fetch them from the vault instead."
    )
    args_schema: type[BaseModel] = _GetSecretInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, path: str, vault_id: str | None = None) -> str:
        try:
            return self.client.get_secret(path, vault_id=vault_id)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _PutSecretInput(BaseModel):
    path: str = Field(..., description="Secret path, e.g. 'api-keys/new-key'")
    value: str = Field(..., description="The secret value to store")
    secret_type: str | None = Field(None, description="Secret type (api_key, password, etc.)")
    description: str | None = Field(None, description="Human-readable description")
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawPutSecretTool(BaseTool):
    """Store or update a secret in the 1Claw vault."""

    name: str = "oneclaw_put_secret"
    description: str = (
        "Store or update a secret in the 1Claw vault. Creates a new version if the "
        "path already exists. Use this to securely persist credentials, tokens, or "
        "sensitive configuration."
    )
    args_schema: type[BaseModel] = _PutSecretInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        path: str,
        value: str,
        secret_type: str | None = None,
        description: str | None = None,
        vault_id: str | None = None,
    ) -> str:
        try:
            result = self.client.put_secret(
                path, value, vault_id=vault_id, secret_type=secret_type, description=description
            )
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _ListSecretsInput(BaseModel):
    prefix: str | None = Field(None, description="Filter secrets by path prefix")
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawListSecretsTool(BaseTool):
    """List available secrets in the 1Claw vault."""

    name: str = "oneclaw_list_secrets"
    description: str = (
        "List secrets stored in the 1Claw vault. Returns paths and metadata "
        "(not values). Optionally filter by prefix."
    )
    args_schema: type[BaseModel] = _ListSecretsInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, prefix: str | None = None, vault_id: str | None = None) -> str:
        try:
            secrets = self.client.list_secrets(vault_id=vault_id, prefix=prefix)
            return json.dumps(secrets)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _RotateSecretInput(BaseModel):
    path: str = Field(..., description="Secret path to rotate")
    length: int = Field(32, description="Generated value length (8-1024)")
    charset: str = Field("base64", description="Charset: hex, base64, alphanumeric, ascii")
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawRotateSecretTool(BaseTool):
    """Rotate a secret with a server-generated cryptographic value."""

    name: str = "oneclaw_rotate_secret"
    description: str = (
        "Rotate a secret at the given path. The server generates a new "
        "cryptographically random value. Old versions are preserved. Use this "
        "for scheduled credential rotation."
    )
    args_schema: type[BaseModel] = _RotateSecretInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        path: str,
        length: int = 32,
        charset: str = "base64",
        vault_id: str | None = None,
    ) -> str:
        try:
            result = self.client.rotate_secret(
                path, vault_id=vault_id, length=length, charset=charset
            )
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


class _MemoryPutInput(BaseModel):
    namespace: str = Field("default", description="Memory namespace")
    key: str = Field(..., description="Memory entry key")
    value: str = Field(..., description="Value to store")
    tier: str = Field("durable", description="Storage tier: 'durable' or 'scratch'")
    ttl_secs: int | None = Field(None, description="TTL in seconds (scratch tier only)")


class OneclawMemoryPutTool(BaseTool):
    """Store a value in the agent's encrypted memory."""

    name: str = "oneclaw_memory_put"
    description: str = (
        "Store a value in the agent's HSM-encrypted persistent memory. "
        "Use 'durable' tier for long-term storage, 'scratch' tier with a TTL "
        "for ephemeral session data."
    )
    args_schema: type[BaseModel] = _MemoryPutInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        key: str,
        value: str,
        namespace: str = "default",
        tier: str = "durable",
        ttl_secs: int | None = None,
    ) -> str:
        try:
            self.client.memory_put(namespace, key, value, tier=tier, ttl_secs=ttl_secs)
            return f"Stored '{key}' in namespace '{namespace}'"
        except OneclawError as e:
            return f"[1claw error] {e}"


class _MemoryGetInput(BaseModel):
    namespace: str = Field("default", description="Memory namespace")
    key: str = Field(..., description="Memory entry key")


class OneclawMemoryGetTool(BaseTool):
    """Retrieve a value from the agent's encrypted memory."""

    name: str = "oneclaw_memory_get"
    description: str = (
        "Retrieve a previously stored value from the agent's memory by key. "
        "Returns the value or a 'not found' message."
    )
    args_schema: type[BaseModel] = _MemoryGetInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, key: str, namespace: str = "default") -> str:
        try:
            value = self.client.memory_get(namespace, key)
            if value is None:
                return f"Memory entry '{key}' not found in namespace '{namespace}'"
            return value
        except OneclawError as e:
            return f"[1claw error] {e}"


class _MemorySearchInput(BaseModel):
    namespace: str = Field("default", description="Memory namespace to search")
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(5, description="Number of results to return (1-50)")


class OneclawMemorySearchTool(BaseTool):
    """Semantic search over the agent's memory entries."""

    name: str = "oneclaw_memory_search"
    description: str = (
        "Search the agent's memory using natural language. Returns the most "
        "relevant stored entries ranked by similarity. Useful for finding "
        "previously learned facts, user preferences, or context."
    )
    args_schema: type[BaseModel] = _MemorySearchInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, query: str, namespace: str = "default", top_k: int = 5) -> str:
        try:
            results = self.client.memory_search(namespace, query, top_k=top_k)
            return json.dumps(results)
        except OneclawError as e:
            return f"[1claw error] {e}"


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


class _SignMessageInput(BaseModel):
    message: str = Field(..., description="Message to sign (hex-encoded or plain text)")
    chain: str = Field("ethereum", description="Chain for signing key resolution")


class OneclawSignMessageTool(BaseTool):
    """Sign a message with the agent's blockchain key (EIP-191)."""

    name: str = "oneclaw_sign_message"
    description: str = (
        "Sign a message using the agent's blockchain signing key (EIP-191 personal_sign). "
        "Returns the signature, message hash, and signer address. The private key "
        "never leaves the HSM."
    )
    args_schema: type[BaseModel] = _SignMessageInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, message: str, chain: str = "ethereum") -> str:
        try:
            result = self.client.sign_message(message, chain=chain)
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _SubmitTransactionInput(BaseModel):
    chain: str = Field(..., description="Blockchain name (ethereum, base, solana, bitcoin, etc.)")
    to: str = Field(..., description="Recipient address")
    value: str = Field("0", description="Amount in native units (ETH, SOL, BTC, etc.)")
    data: str | None = Field(None, description="Hex-encoded calldata (EVM only)")
    token_mint: str | None = Field(None, description="Token contract address for token transfers")
    simulate_first: bool = Field(False, description="Run Tenderly simulation before signing")


class OneclawSubmitTransactionTool(BaseTool):
    """Sign and broadcast a blockchain transaction."""

    name: str = "oneclaw_submit_transaction"
    description: str = (
        "Sign and broadcast a blockchain transaction using the agent's signing key. "
        "Supports EVM chains (Ethereum, Base, etc.), Bitcoin, Solana, XRP, Cardano, "
        "and Tron. Transaction guardrails (allowlists, spend caps) are enforced "
        "server-side. The private key never leaves the HSM."
    )
    args_schema: type[BaseModel] = _SubmitTransactionInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        chain: str,
        to: str,
        value: str = "0",
        data: str | None = None,
        token_mint: str | None = None,
        simulate_first: bool = False,
    ) -> str:
        try:
            result = self.client.submit_transaction(
                chain=chain,
                to=to,
                value=value,
                data_hex=data,
                token_mint=token_mint,
                simulate_first=simulate_first,
            )
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _GetBalanceInput(BaseModel):
    chain: str = Field(..., description="Blockchain name (ethereum, solana, bitcoin, etc.)")
    tokens: str | None = Field(
        None, description="Comma-separated token contract addresses for balance queries"
    )


class OneclawGetBalanceTool(BaseTool):
    """Check the agent's signing key balance on a blockchain."""

    name: str = "oneclaw_get_balance"
    description: str = (
        "Get the native currency and token balances for the agent's signing key "
        "on a specific blockchain. Use this to check available funds before "
        "submitting a transaction."
    )
    args_schema: type[BaseModel] = _GetBalanceInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, chain: str, tokens: str | None = None) -> str:
        try:
            result = self.client.get_signing_key_balance(chain, tokens=tokens)
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


# ---------------------------------------------------------------------------
# Environment Variables
# ---------------------------------------------------------------------------


class _ResolveEnvInput(BaseModel):
    environment: str | None = Field(
        None, description="Environment name (production, preview, development)"
    )
    git_branch: str | None = Field(
        None, description="Git branch for branch-specific overrides"
    )
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawResolveEnvTool(BaseTool):
    """Resolve environment variables for a vault with precedence rules."""

    name: str = "oneclaw_resolve_env"
    description: str = (
        "Resolve environment variables for the vault with Vercel-style precedence: "
        "org shared vars < vault vars < branch-specific overrides. Returns the final "
        "merged key-value map and sources. Use this to get the runtime config for a "
        "specific environment and branch."
    )
    args_schema: type[BaseModel] = _ResolveEnvInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(
        self,
        environment: str | None = None,
        git_branch: str | None = None,
        vault_id: str | None = None,
    ) -> str:
        try:
            result = self.client.resolve_env_vars(
                vault_id=vault_id, environment=environment, git_branch=git_branch
            )
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


class _ListEnvVarsInput(BaseModel):
    environment: str | None = Field(None, description="Filter by environment name")
    vault_id: str | None = Field(None, description="Vault UUID (uses default if omitted)")


class OneclawListEnvVarsTool(BaseTool):
    """List environment variables defined on a vault."""

    name: str = "oneclaw_list_env_vars"
    description: str = (
        "List environment variables defined on the vault. Returns keys, environments, "
        "and metadata (sensitive vars have values omitted). Optionally filter by "
        "environment name."
    )
    args_schema: type[BaseModel] = _ListEnvVarsInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, environment: str | None = None, vault_id: str | None = None) -> str:
        try:
            result = self.client.list_env_vars(vault_id=vault_id, environment=environment)
            return json.dumps(result)
        except OneclawError as e:
            return f"[1claw error] {e}"


# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------


class _TriggerAutomationInput(BaseModel):
    automation_id: str = Field(..., description="UUID of the automation to trigger")
    context: str | None = Field(None, description="JSON context data to pass to the automation")


class OneclawTriggerAutomationTool(BaseTool):
    """Trigger a 1Claw automation workflow."""

    name: str = "oneclaw_trigger_automation"
    description: str = (
        "Trigger a pre-configured 1Claw automation workflow by its ID. "
        "Automations can perform multi-step tasks like rotating secrets, "
        "sending notifications, making API calls, or running AI-powered workflows."
    )
    args_schema: type[BaseModel] = _TriggerAutomationInput
    client: OneclawClient

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _run(self, automation_id: str, context: str | None = None) -> str:
        try:
            ctx = json.loads(context) if context else None
            result = self.client.trigger_automation(automation_id, context=ctx)
            return json.dumps(result)
        except (json.JSONDecodeError, OneclawError) as e:
            return f"[1claw error] {e}"


# ---------------------------------------------------------------------------
# Toolkit factory
# ---------------------------------------------------------------------------


def get_all_tools(client: OneclawClient) -> list[BaseTool]:
    """Return all 1Claw tools initialized with the given client.

    This is the recommended way to add 1Claw capabilities to a LangChain agent.

    Example::

        from langchain_1claw import OneclawClient, get_all_tools
        from langchain_openai import ChatOpenAI

        client = OneclawClient(api_key="ocv_...")
        tools = get_all_tools(client)
        agent = create_tool_calling_agent(ChatOpenAI(), prompt, tools)
    """
    return [
        OneclawGetSecretTool(client=client),
        OneclawPutSecretTool(client=client),
        OneclawListSecretsTool(client=client),
        OneclawRotateSecretTool(client=client),
        OneclawResolveEnvTool(client=client),
        OneclawListEnvVarsTool(client=client),
        OneclawMemoryPutTool(client=client),
        OneclawMemoryGetTool(client=client),
        OneclawMemorySearchTool(client=client),
        OneclawSignMessageTool(client=client),
        OneclawSubmitTransactionTool(client=client),
        OneclawGetBalanceTool(client=client),
        OneclawTriggerAutomationTool(client=client),
    ]
