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

__version__ = "0.1.0"

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
