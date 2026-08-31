import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import initialize_agent, AgentType, create_tool_calling_agent, AgentExecutor
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

# Instantiate the reasoning brain
llm = ChatOpenAI(model="gpt-5.4-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages(["system", "You are an AfyaPlus operations assistant."], ["placeholder", "{chat_history}"], ["human", "{input}"], ["placeholder", "{agent_scratchpad}"])

# TODO: Step 1 - Complete this custom tool using the @tool decorator
@tool
def lookup_specialist_department(specialty_name: str) -> str:
    """Use this tool to find out the location or status of a specific medical specialty department at AfyaPlus."""
    roster = {
        "pediatrics": "Located in Wing A, open until 8 PM.",
        "cardiology": "Located in Main Tower, requires pre-booking.",
        "dermatology": "Nairobi Hub clinic, fully booked this week."
    }
    # Write logic to normalize text and pull from the roster dict
    return ""

web_search = DuckDuckGoSearchRun()

# TODO: Step 2 - Construct your tools array including both the web search and your new custom roster tool
tools = [lookup_specialist_department, web_search]

# TODO: Step 3 - Initialize the autonomous agent executor with verbose output enabled
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

store = {}
def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

agent_with_memory = RunnableWithMessageHistory(
    executor, get_session_history,
    input_messages_key="input", history_messages_key="chat_history"
)
# --- Runtime Invocation Task ---
# Test the agent with a compound query:
# "Find out which clinic handles 'cardiology' at AfyaPlus, and then find out what the general pre-booking prep is for cardiology on the web."
Stuck? Unlock hints 

tools = [get_clinic_stock_count, refer_to_specialist]
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)