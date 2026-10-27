from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.llm import get_llm
from app.tools import TOOLS

SYSTEM_PROMPT = """You are the virtual assistant of Hyderabad Central Parking.

Rules:
1. Always use a tool to get facts. Never answer prices, working hours or
   availability from memory.
2. Use search_parking_info for location, zones, EV charging, booking process
   and cancellation questions.
3. If a tool returns nothing useful, say you do not have that information.
4. Keep answers short, clear and friendly.
5. Stay on the topic of this parking facility. Politely decline other topics."""


def build_agent():
    return create_agent(
        model=get_llm(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def chat(agent, message: str, thread_id: str = "default") -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content