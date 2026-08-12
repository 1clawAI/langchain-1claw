"""LangChain chat message history backed by 1Claw's encrypted Memory API.

Persists conversation messages across sessions using 1Claw's HSM-encrypted
agent memory. Each conversation is stored as a JSON-serialized list of
messages under a configurable namespace and key.

Example::

    from langchain_1claw import OneclawClient, OneclawChatMessageHistory

    client = OneclawClient(api_key="ocv_...")
    history = OneclawChatMessageHistory(client=client, session_id="user-123")

    # Use with RunnableWithMessageHistory or ConversationChain
    from langchain_core.runnables.history import RunnableWithMessageHistory

    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: OneclawChatMessageHistory(
            client=client, session_id=session_id
        ),
    )
"""

from __future__ import annotations

import json

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    messages_from_dict,
    messages_to_dict,
)

from ._client import OneclawClient, OneclawError


class OneclawChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in 1Claw's encrypted agent memory.

    Each session's messages are serialized as a JSON array and stored
    as a single memory entry. Messages are encrypted at rest with the
    org's HSM-managed KEK.

    Args:
        client: An authenticated ``OneclawClient`` instance.
        session_id: Unique identifier for this conversation session.
        namespace: Memory namespace (default: ``"chat_history"``).
        max_messages: Maximum messages to retain (oldest trimmed). None = unlimited.
    """

    def __init__(
        self,
        client: OneclawClient,
        session_id: str,
        *,
        namespace: str = "chat_history",
        max_messages: int | None = None,
    ) -> None:
        self._client = client
        self._session_id = session_id
        self._namespace = namespace
        self._max_messages = max_messages

    @property
    def messages(self) -> list[BaseMessage]:
        """Retrieve all messages for this session from 1Claw memory."""
        raw = self._client.memory_get(self._namespace, self._session_id)
        if raw is None:
            return []
        try:
            dicts = json.loads(raw)
            if not isinstance(dicts, list):
                return []
            return messages_from_dict(dicts)
        except (json.JSONDecodeError, Exception):
            return []

    def add_message(self, message: BaseMessage) -> None:
        """Append a message and persist to 1Claw memory."""
        current = self.messages
        current.append(message)
        if self._max_messages is not None and len(current) > self._max_messages:
            current = current[-self._max_messages :]
        serialized = json.dumps(messages_to_dict(current))
        self._client.memory_put(self._namespace, self._session_id, serialized)

    def clear(self) -> None:
        """Delete all messages for this session."""
        try:
            self._client.memory_delete(self._namespace, self._session_id)
        except OneclawError:
            pass


class OneclawScratchChatMessageHistory(OneclawChatMessageHistory):
    """Ephemeral chat history using 1Claw's scratch memory tier.

    Messages auto-expire after ``ttl_secs`` (default: 1 hour). Useful for
    short-lived sessions that should not persist permanently.
    """

    def __init__(
        self,
        client: OneclawClient,
        session_id: str,
        *,
        namespace: str = "chat_scratch",
        max_messages: int | None = 50,
        ttl_secs: int = 3600,
    ) -> None:
        super().__init__(client, session_id, namespace=namespace, max_messages=max_messages)
        self._ttl_secs = ttl_secs

    def add_message(self, message: BaseMessage) -> None:
        current = self.messages
        current.append(message)
        if self._max_messages is not None and len(current) > self._max_messages:
            current = current[-self._max_messages :]
        serialized = json.dumps(messages_to_dict(current))
        self._client.memory_put(
            self._namespace,
            self._session_id,
            serialized,
            tier="scratch",
            ttl_secs=self._ttl_secs,
        )
