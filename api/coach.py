import os
from dotenv import load_dotenv
from pathlib import Path
from utils.prompts import build_system_prompt
from utils.functions import COACH_TOOLS, COACH_TOOLS_BY_NAME

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

llm_with_tools = llm.bind_tools(COACH_TOOLS)

MAX_TOOL_ITERATIONS = 5


def get_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(session_id, "sqlite:///cornea.db")


def _run_with_tools(prompt_value):
    messages = prompt_value.to_messages()
    response = None
    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            return response
        for tc in tool_calls:
            tool_fn = COACH_TOOLS_BY_NAME.get(tc["name"])
            if tool_fn is None:
                result = f"Unknown tool: {tc['name']}"
            else:
                result = tool_fn.invoke(tc.get("args") or {})
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return response


def generate_coach_response(context_data, user_message, session_id,
                            coach_language="mixed", coach_tone="Balanced"):
    system_prompt = build_system_prompt(coach_language, coach_tone)

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | RunnableLambda(_run_with_tools)

    chain_with_memory = RunnableWithMessageHistory(
        chain,
        get_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    try:
        response = chain_with_memory.invoke(
            {"input": user_message, "context": context_data},
            config={"configurable": {"session_id": session_id}},
        )
        content = response.content
        if isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", str(content))
        return str(content)
    except Exception as e:
        return f"Failed with error: {e}"


def get_formatted_history(session_id: str):
    history = get_history(session_id)
    messages = history.messages
    formatted = []
    for msg in messages:
        text = msg.content
        if isinstance(text, list) and len(text) > 0 and isinstance(text[0], dict):
            text = text[0].get("text", str(text))
        elif isinstance(text, dict):
            text = text.get("text", str(text))

        if msg.type == "human":
            formatted.append({"role": "user", "text": str(text)})
        elif msg.type == "ai":
            formatted.append({"role": "assistant", "text": str(text)})
    return formatted
