"""Example: Persistent chat with 1Claw-backed message history.

Run:
    ONECLAW_AGENT_API_KEY=ocv_... OPENAI_API_KEY=sk-... python chat_with_memory.py
"""

import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from langchain_1claw import OneclawChatMessageHistory, OneclawClient


def main() -> None:
    api_key = os.environ["ONECLAW_AGENT_API_KEY"]
    client = OneclawClient(api_key=api_key)

    llm = ChatOpenAI(model="gpt-4o")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant. Remember what the user tells you."),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    chain = prompt | llm

    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: OneclawChatMessageHistory(
            client=client, session_id=session_id, max_messages=50
        ),
        input_messages_key="input",
        history_messages_key="history",
    )

    config = {"configurable": {"session_id": "demo-session"}}

    print("Chat with memory (type 'quit' to exit)")
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break
        response = chain_with_history.invoke({"input": user_input}, config=config)
        print(f"\nAssistant: {response.content}")


if __name__ == "__main__":
    main()
