"""Stateful LangChain agent runner with session memory."""

from __future__ import annotations

from typing import Dict

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from src.agent.prompts import SYSTEM_PROMPT
from src.config import get_chat_model, get_openai_api_key
from src.rag.retriever_tool import search_afyaplus_knowledge_manual
from src.tools.clinical_math import calculate_diagnostic_metric, calculate_medication_volume

MAX_ITERATIONS = 6
MAX_HISTORY_MESSAGES = 12

_session_store: Dict[str, InMemoryChatMessageHistory] = {}


def _trim_history(history: InMemoryChatMessageHistory) -> None:
    if len(history.messages) > MAX_HISTORY_MESSAGES:
        history.messages = history.messages[-MAX_HISTORY_MESSAGES:]


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _session_store:
        _session_store[session_id] = InMemoryChatMessageHistory()
    history = _session_store[session_id]
    _trim_history(history)
    return history


def clear_session_history(session_id: str) -> None:
    _session_store.pop(session_id, None)


def build_agent_with_memory() -> RunnableWithMessageHistory:
    llm = ChatOpenAI(
        model=get_chat_model(),
        temperature=0.0,
        api_key=get_openai_api_key(),
    )
    tools = [
        search_afyaplus_knowledge_manual,
        calculate_medication_volume,
        calculate_diagnostic_metric,
    ]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=MAX_ITERATIONS,
        handle_parsing_errors=True,
    )
    return RunnableWithMessageHistory(
        executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
