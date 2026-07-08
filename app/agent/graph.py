from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import build_tools
from app.db.crud import get_or_create_customer, get_recent_messages, save_message
from app.db.session import get_session
from app.llm.factory import get_chat_model

HISTORY_TURNS = 10


def _history_to_messages(history) -> list:
    role_map = {"user": HumanMessage, "assistant": AIMessage}
    return [role_map[m.role](content=m.content) for m in history if m.role in role_map]


def run_agent(wa_id: str, user_message: str, contact_name: str | None = None) -> str:
    """Run one turn of the support agent for a given WhatsApp user and return the reply text.

    Conversation history is persisted in Postgres (not just in-memory), so the bot
    keeps context across process restarts / multiple worker instances.
    """
    with get_session() as db:
        get_or_create_customer(db, wa_id, name=contact_name)
        history = get_recent_messages(db, wa_id, limit=HISTORY_TURNS)
        save_message(db, wa_id, "user", user_message)

    agent = create_react_agent(model=get_chat_model(), tools=build_tools(wa_id))

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(_history_to_messages(history))
    messages.append(HumanMessage(content=user_message))

    result = agent.invoke({"messages": messages})
    reply = result["messages"][-1].content

    with get_session() as db:
        save_message(db, wa_id, "assistant", reply)

    return reply
