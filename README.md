# langchain-1claw

[![PyPI](https://img.shields.io/pypi/v/langchain-1claw)](https://pypi.org/project/langchain-1claw/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

> ⭐ **Star [1clawAI/agent-templates](https://github.com/1clawAI/agent-templates)** — ready-to-run agent templates wired to 1Claw. It is our single starred repo.

You're building a LangChain agent that needs API keys, wallet signing, or memory that survives across sessions. Pasting credentials into `.env` files works until you deploy, share the repo, or the model accidentally echoes a secret in chat.

This package gives your agent 13 LangChain tools backed by [1Claw](https://1claw.co). Secrets live in an HSM-encrypted vault. A human grants access through policies, so the agent only reads paths you allow. Signing keys never leave the server. Memory is encrypted and searchable.

Install one package, pass an `ocv_` agent API key, and call `get_all_tools()`. You get vault CRUD, encrypted memory, EIP-191 signing, multi-chain transactions, and automation triggers without writing HTTP clients yourself.

## Features

| Category | Components | What it does |
|----------|-----------|--------------|
| **Secrets** | `OneclawGetSecretTool`, `OneclawPutSecretTool`, `OneclawListSecretsTool`, `OneclawRotateSecretTool` | CRUD and rotation for HSM-encrypted vault secrets |
| **Env vars** | `OneclawResolveEnvTool`, `OneclawListEnvVarsTool` | Resolve vault env vars with precedence; list scoped keys |
| **Memory** | `OneclawMemoryPutTool`, `OneclawMemoryGetTool`, `OneclawMemorySearchTool` | Encrypted persistent memory with semantic search |
| **Signing** | `OneclawSignMessageTool`, `OneclawSubmitTransactionTool`, `OneclawGetBalanceTool` | EIP-191 signing and multi-chain transaction submission (ETH, BTC, SOL, XRP, ADA, TRX) |
| **Automations** | `OneclawTriggerAutomationTool` | Trigger pre-configured workflow automations |
| **Chat History** | `OneclawChatMessageHistory`, `OneclawScratchChatMessageHistory` | `BaseChatMessageHistory` backed by encrypted memory |
| **Retriever** | `OneclawMemoryRetriever` | `BaseRetriever` backed by semantic memory search |

## Installation

```bash
pip install langchain-1claw
```

## Quick Start

### Tool-calling agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from langchain_1claw import OneclawClient, get_all_tools

# Authenticate with your agent's API key
client = OneclawClient(api_key="ocv_your_agent_key")

# Get all 13 tools
tools = get_all_tools(client)

# Build an agent
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant with access to a secure vault, "
               "blockchain signing, encrypted memory, and workflow automations."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "What API keys do we have stored?"})
print(result["output"])
```

### Individual tools

```python
from langchain_1claw import OneclawClient, OneclawGetSecretTool

client = OneclawClient(api_key="ocv_...")
tool = OneclawGetSecretTool(client=client)

# Use directly
api_key = tool.invoke({"path": "api-keys/openai"})

# Or with a specific vault
api_key = tool.invoke({"path": "api-keys/openai", "vault_id": "vault-uuid"})
```

### Persistent chat history

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_1claw import OneclawClient, OneclawChatMessageHistory

client = OneclawClient(api_key="ocv_...")

chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: OneclawChatMessageHistory(
        client=client,
        session_id=session_id,
        max_messages=100,  # trim old messages
    ),
)

# Messages persist across sessions, encrypted at rest with HSM-managed keys
result = chain_with_history.invoke(
    {"input": "Remember that my favorite color is blue"},
    config={"configurable": {"session_id": "user-123"}},
)
```

### Ephemeral scratch history (auto-expires)

```python
from langchain_1claw import OneclawScratchChatMessageHistory

history = OneclawScratchChatMessageHistory(
    client=client,
    session_id="temp-session",
    ttl_secs=600,  # auto-delete after 10 minutes
)
```

### Semantic memory retriever (RAG)

```python
from langchain_1claw import OneclawClient, OneclawMemoryRetriever

client = OneclawClient(api_key="ocv_...")
retriever = OneclawMemoryRetriever(
    client=client,
    namespace="knowledge",
    top_k=5,
)

# Use in a RAG chain
docs = retriever.invoke("How do I deploy to production?")
for doc in docs:
    print(f"[{doc.metadata['key']}] {doc.page_content[:100]}...")
```

### Multi-chain transaction signing

```python
from langchain_1claw import OneclawClient, OneclawSubmitTransactionTool

client = OneclawClient(api_key="ocv_...")
tx_tool = OneclawSubmitTransactionTool(client=client)

# Sign and broadcast — private key never leaves the HSM
result = tx_tool.invoke({
    "chain": "ethereum",
    "to": "0xRecipientAddress",
    "value": "0.01",
    "simulate_first": True,  # Tenderly simulation before signing
})
```

## Authentication

The client authenticates via agent API key exchange:

```python
# Key-only auth (auto-discovers agent_id and vault_id)
client = OneclawClient(api_key="ocv_your_key")

# Explicit IDs
client = OneclawClient(
    api_key="ocv_your_key",
    agent_id="agent-uuid",
    vault_id="vault-uuid",
)

# Custom API endpoint
client = OneclawClient(
    api_key="ocv_your_key",
    base_url="https://your-vault.example.com",
)
```

JWTs are cached and automatically refreshed 60 seconds before expiry.

## API Reference

### Client

| Method | Description |
|--------|-------------|
| `get_secret(path)` | Fetch a decrypted secret |
| `put_secret(path, value)` | Store or update a secret |
| `list_secrets()` | List secret paths |
| `delete_secret(path)` | Delete a secret |
| `rotate_secret(path)` | Server-side secret rotation |
| `memory_put(namespace, key, value)` | Store a memory entry |
| `memory_get(namespace, key)` | Retrieve a memory entry |
| `memory_search(namespace, query)` | Semantic search over memory |
| `memory_list(namespace)` | List memory entries |
| `memory_delete(namespace, key)` | Delete a memory entry |
| `sign_message(message)` | EIP-191 personal_sign |
| `sign_typed_data(typed_data)` | EIP-712 typed data signing |
| `submit_transaction(chain, to, value)` | Sign and broadcast a transaction |
| `sign_transaction(chain, to, value)` | Sign without broadcasting |
| `list_signing_keys()` | List agent signing keys |
| `get_signing_key_balance(chain)` | Get wallet balances |
| `trigger_automation(automation_id)` | Trigger an automation |
| `list_automations()` | List available automations |
| `list_vaults()` | List accessible vaults |

### Tools

All tools accept a shared `OneclawClient` via the `client` parameter. Use `get_all_tools(client)` to get all 13 tools at once.

## Platform v0.56+ (HITL, HFA, Safe, guardrail governance)

LangChain tools target 1Claw API **v0.58+**:

| Capability | Tool impact |
|------------|-------------|
| **Graduated HITL** | `OneclawSubmitTransactionTool` may return `awaiting_approval` — handle 202 in agent loops or use dashboard/mobile approvals. |
| **Guardrail governance** | Execution intents and guardrail widening use server-side approval queues. |
| **Safe foundation** | Agent Safe accounts via Vault API (CLI: `1claw agent accounts`). |
| **Multichain** | BTC/SOL/XRP/ADA/TRX signing unchanged; Vault/Shroud deps: `rust-bitcoin`, `solana-sdk` v4, `xrpl-rust` 1.1.0. |

## Development

```bash
git clone https://github.com/1clawAI/langchain-1claw.git
cd langchain-1claw
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src tests
ruff format src tests

# Type check
mypy
```

## License

MIT — see [LICENSE](LICENSE).
