"""Example: RAG chain with 1Claw semantic memory retriever.

Run:
    ONECLAW_AGENT_API_KEY=ocv_... OPENAI_API_KEY=sk-... python rag_with_memory.py
"""

import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from langchain_1claw import OneclawClient, OneclawMemoryRetriever


def format_docs(docs: list) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def main() -> None:
    api_key = os.environ["ONECLAW_AGENT_API_KEY"]
    client = OneclawClient(api_key=api_key)

    retriever = OneclawMemoryRetriever(
        client=client,
        namespace="knowledge",
        top_k=5,
    )

    llm = ChatOpenAI(model="gpt-4o")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Answer the question based on the following context from memory:\n\n"
            "{context}\n\n"
            "If the context doesn't contain relevant information, say so.",
        ),
        ("human", "{question}"),
    ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = chain.invoke("How do I deploy to production?")
    print(answer)


if __name__ == "__main__":
    main()
