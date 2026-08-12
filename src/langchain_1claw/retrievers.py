"""LangChain retriever backed by 1Claw's semantic memory search.

Uses 1Claw's vector-indexed agent memory (pgvector embeddings) for
similarity search. Memory entries are encrypted at rest and decrypted
only during search.

Example::

    from langchain_1claw import OneclawClient, OneclawMemoryRetriever

    client = OneclawClient(api_key="ocv_...")
    retriever = OneclawMemoryRetriever(client=client, namespace="knowledge")

    docs = retriever.invoke("How do I deploy to production?")
"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field

from ._client import OneclawClient, OneclawError


class OneclawMemoryRetriever(BaseRetriever):
    """Retriever that searches 1Claw agent memory using semantic similarity.

    Memory entries must be in the ``semantic`` tier (vector-indexed) to
    appear in search results. Use ``OneclawMemoryPutTool`` or the client's
    ``memory_put()`` with ``tier="semantic"`` to populate searchable entries.

    Args:
        client: An authenticated ``OneclawClient`` instance.
        namespace: Memory namespace to search (default: ``"knowledge"``).
        top_k: Number of results to return per query (default: 5, max: 50).
    """

    client: OneclawClient
    namespace: str = Field(default="knowledge")
    top_k: int = Field(default=5, ge=1, le=50)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun | None = None,
    ) -> list[Document]:
        try:
            results = self.client.memory_search(self.namespace, query, top_k=self.top_k)
        except OneclawError:
            return []

        docs: list[Document] = []
        for entry in results:
            value = entry.get("value", "")
            metadata: dict[str, Any] = {
                "namespace": self.namespace,
                "key": entry.get("key", ""),
                "tier": entry.get("tier", ""),
                "score": entry.get("score"),
                "created_at": entry.get("created_at"),
                "updated_at": entry.get("updated_at"),
            }
            docs.append(Document(page_content=value, metadata=metadata))
        return docs
