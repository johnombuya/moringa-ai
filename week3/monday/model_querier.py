from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

SYSTEM_PROMPT = (
    "You are a clinical triage assistant for the AfyaPlus healthcare ecosystem. "
    "Answer questions clearly and concisely. Be specific about clinical metrics, "
    "timelines, and triage protocols. Keep your answer to 2-4 sentences."
)

def query_model(model_name: str, question: str) -> str:
    llm = ChatOpenAI(model=model_name, temperature=0, max_tokens=300)
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
    response = llm.invoke(messages)
    return response.content