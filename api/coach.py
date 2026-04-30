import os
from dotenv import load_dotenv
from pathlib import Path
from prompts import system_prompt

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("history"),
    ("human", "{input}")
])

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    )
chain = prompt | llm

def get_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(session_id, "sqlite:///cornea.db")

chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
)

def generate_coach_response(context_data, user_message, session_id):
    try:
      response = chain_with_memory.invoke(
          {"input": user_message, "context": context_data},
          config={"configurable": {"session_id": session_id}},
      ).content[0]["text"]
      return response
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