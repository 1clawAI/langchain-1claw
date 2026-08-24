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

__version__ = "0.2.2"

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
