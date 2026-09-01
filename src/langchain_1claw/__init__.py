"""langchain-1claw — LangChain integration for 1Claw secrets, signing, memory & automations."""

from ._client import (
    OneclawAuthError,
    OneclawClient,
    OneclawError,
    OneclawNotFoundError,
    OneclawValidationError,
)
from .memory import OneclawChatMessageHistory, OneclawScratchChatMessageHistory
from .retrievers import OneclawMemoryRetriever
from .tools import (
    OneclawGetBalanceTool,
    OneclawGetSecretTool,
    OneclawListEnvVarsTool,
    OneclawListSecretsTool,
    OneclawMemoryGetTool,
    OneclawMemoryPutTool,
    OneclawMemorySearchTool,
    OneclawPutSecretTool,
    OneclawResolveEnvTool,
    OneclawRotateSecretTool,
    OneclawSignMessageTool,
    OneclawSubmitTransactionTool,
    OneclawTriggerAutomationTool,
    get_all_tools,
)

# Single source of truth: the version lives in pyproject.toml and is read
# from the installed distribution metadata. A hand-maintained literal here
# drifts the moment a release bumps one and not the other — 0.59.8 shipped
# reporting 0.59.6, so anyone checking __version__ got the wrong answer.
try:  # pragma: no cover - trivial
    from importlib.metadata import PackageNotFoundError, version as _dist_version

    __version__ = _dist_version("langchain-1claw")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0+unknown"
__all__ = [
    # Client
    "OneclawClient",
    "OneclawError",
    "OneclawAuthError",
    "OneclawNotFoundError",
    "OneclawValidationError",
    # Tools
    "OneclawGetSecretTool",
    "OneclawPutSecretTool",
    "OneclawListSecretsTool",
    "OneclawRotateSecretTool",
    "OneclawResolveEnvTool",
    "OneclawListEnvVarsTool",
    "OneclawMemoryPutTool",
    "OneclawMemoryGetTool",
    "OneclawMemorySearchTool",
    "OneclawSignMessageTool",
    "OneclawSubmitTransactionTool",
    "OneclawGetBalanceTool",
    "OneclawTriggerAutomationTool",
    "get_all_tools",
    # Memory
    "OneclawChatMessageHistory",
    "OneclawScratchChatMessageHistory",
    # Retriever
    "OneclawMemoryRetriever",
]
