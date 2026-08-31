import os
import traceback
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent, AgentExecutor
from langchain_core.agents import AgentFinish
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

@tool
def calculate_facility_utilization(active_beds: int, total_beds: int) -> str:
    """Calculates the capacity utilisation percentage for a clinic ward."""
    try:
        if total_beds <= 0:
            return "Error: total beds must be greater than zero."
        pct = (active_beds / total_beds) * 100
        return f"Utilisation: {pct:.1f}%"
    except Exception:
        return f"Error computing utilisation: {traceback.format_exc(limit=1)}"

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AfyaPlus operations assistant."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

tools = [calculate_facility_utilization]
agent = create_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

try:
    result = executor.invoke({"input": "If 84 of our 100 beds are occupied, what is utilisation?"})
    print(f"\n--- Final Answer ---")
    print(result.get("output", "No output returned"))
except Exception as e:
    print(f"Error running agent: {e}")
    import traceback
    traceback.print_exc()