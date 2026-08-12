"""Example: LangChain agent with all 1Claw tools.

Run:
    ONECLAW_AGENT_API_KEY=ocv_... OPENAI_API_KEY=sk-... python agent_with_tools.py
"""

import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from langchain_1claw import OneclawClient, get_all_tools


def main() -> None:
    api_key = os.environ["ONECLAW_AGENT_API_KEY"]
    client = OneclawClient(api_key=api_key)
    tools = get_all_tools(client)

    llm = ChatOpenAI(model="gpt-4o")
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful assistant with access to a secure 1Claw vault, "
            "blockchain signing keys, encrypted agent memory, and workflow automations. "
            "Use the tools to help the user manage secrets, sign transactions, "
            "remember information, and trigger workflows.",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    result = executor.invoke({"input": "List the secrets I have stored."})
    print(result["output"])


if __name__ == "__main__":
    main()
