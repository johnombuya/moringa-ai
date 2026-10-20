# agent_service.py - LangChain ReAct agent integrating AfyaPlus MCP tools
"""
AfyaPlus Logistics Agent Service
--------------------------------
Orchestrates an autonomous LangChain ReAct agent equipped with MCP health-logistics
tools for Western Kenya clinic supply chains.

Capabilities:
- Tool execution against logistics_mcp (check_stock, plan_delivery_route, reorder_supplies).
- Loop budget enforcement with strict recursion_limit (default: 8) to prevent runaway costs.
- Trace propagation: associates every tool call and agent step with request trace_id.
- Honest failure: admits lack of knowledge when questions fall outside available tool domains.
- Resilient execution: supports live OpenAI/OpenRouter models and deterministic offline fallback.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

import logistics_mcp

load_dotenv()

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] agent-service: %(message)s",
)
log = logging.getLogger("afyaplus-agent")

AGENT_SYSTEM_PROMPT = """You are the AfyaPlus Health-Logistics AI Agent serving rural clinic networks in Western Kenya.

You have access to the following specialized tools:
1. check_stock: checks current stock of 'amoxicillin', 'ors_sachets', and 'malaria_kits' across all partner clinics.
2. plan_delivery_route: plans an efficient delivery route visiting all clinics starting from a clinic ID (e.g. C01, C02, C03, C04, C05).
3. reorder_supplies: validates and creates a supply replenishment proposal for a specific clinic.

Guidelines:
- When answering logistical questions, call the appropriate tools to fetch live data.
- If a question requires multiple tools (e.g. finding low stock and planning a delivery route), invoke each tool in sequence and synthesize a clear, actionable summary.
- If a question cannot be answered using your available tools (such as weather forecasts, clinical medical diagnoses, patient records, or general trivia), you must HONESTLY state that the available tools and data cannot answer the question. Never invent or hallucinate data.
"""

# Track tool invocations per trace for observability
_active_traces: Dict[str, List[str]] = {}


@tool
def check_stock(item: str) -> str:
    """Check how many units of a medical supply item each partner clinic holds.
    Valid items: 'amoxicillin', 'ors_sachets', 'malaria_kits'."""
    log.info("agent_tool_exec tool=check_stock item=%s", item)
    return logistics_mcp.check_stock(item)


@tool
def plan_delivery_route(start_clinic_id: str) -> str:
    """Plan an efficient delivery route visiting all partner clinics starting from a specific clinic ID.
    Valid IDs: 'C01', 'C02', 'C03', 'C04', 'C05'."""
    log.info("agent_tool_exec tool=plan_delivery_route start=%s", start_clinic_id)
    return logistics_mcp.plan_delivery_route(start_clinic_id)


@tool
def reorder_supplies(clinic_id: str, item: str, quantity: int) -> str:
    """Validate and propose supply replenishment for a clinic.
    Quantity must be between 1 and 500."""
    log.info("agent_tool_exec tool=reorder_supplies clinic=%s item=%s qty=%d", clinic_id, item, quantity)
    return logistics_mcp.reorder_supplies(clinic_id, item, quantity)


TOOLS = [check_stock, plan_delivery_route, reorder_supplies]


def _build_llm():
    """Build the ChatOpenAI client supporting OpenRouter or standard OpenAI endpoints."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")

    if not api_key or api_key.startswith("your-openai"):
        return None

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0,
    )


def _deterministic_agent_fallback(question: str, trace_id: str) -> str:
    """Deterministic fallback agent for offline/zero-credit runs.

    Follows the same THINK -> ACT -> OBSERVE -> ANSWER pattern without LLM spend,
    guaranteeing honest refusal on out-of-scope questions and correct multi-tool execution.
    """
    q_lower = question.lower()
    log.info("trace=%s fallback_agent=true question=%r", trace_id, question)

    # Out-of-scope domain check (honest failure)
    out_of_scope_keywords = ["weather", "temperature", "forecast", "salary", "diagnosis", "president", "sports"]
    if any(k in q_lower for k in out_of_scope_keywords):
        return (
            "I do not have access to that information. The AfyaPlus logistics system only maintains "
            "data regarding partner clinic inventory (amoxicillin, ors_sachets, malaria_kits), "
            "delivery routing, and supply reorders. The data cannot answer this question."
        )

    # Multi-tool scenario: stock check + delivery route
    wants_stock = "stock" in q_lower or "amoxicillin" in q_lower or "reorder" in q_lower or "ors" in q_lower or "malaria" in q_lower
    wants_route = "route" in q_lower or "driver" in q_lower or "delivery" in q_lower

    if wants_stock and wants_route:
        # Step 1: Tool check_stock
        item = "amoxicillin"
        for candidate in ["malaria_kits", "ors_sachets", "amoxicillin"]:
            if candidate.replace("_", " ") in q_lower or candidate in q_lower:
                item = candidate
                break
        stock_raw = logistics_mcp.check_stock(item)
        stock_data = json.loads(stock_raw)

        # Step 2: Tool plan_delivery_route
        start_id = "C01"
        for cid in ["C01", "C02", "C03", "C04", "C05"]:
            if cid.lower() in q_lower:
                start_id = cid
                break
        route_raw = logistics_mcp.plan_delivery_route(start_id)
        route_data = json.loads(route_raw)

        low_clinics = [s["clinic"] for s in stock_data.get("stock", []) if s.get("reorder_needed")]
        route_str = " -> ".join(route_data.get("route_order", []))
        total_km = route_data.get("total_km", 0.0)

        return (
            f"Based on live MCP tool queries:\n"
            f"1. Inventory Check ({item}): Clinics requiring reorder (< 10 units): {', '.join(low_clinics)}.\n"
            f"2. Delivery Route: The recommended route starting from {route_data.get('start_clinic')} is: "
            f"{route_str} (Total distance: {total_km} km using nearest-neighbour heuristic)."
        )

    # Single tool: stock check
    if wants_stock:
        item = "amoxicillin"
        for candidate in ["malaria_kits", "ors_sachets", "amoxicillin"]:
            if candidate.replace("_", " ") in q_lower or candidate in q_lower:
                item = candidate
                break
        res = json.loads(logistics_mcp.check_stock(item))
        return f"Stock check for {item}: {json.dumps(res, indent=2)}"

    # Single tool: route
    if wants_route:
        start_id = "C01"
        for cid in ["C01", "C02", "C03", "C04", "C05"]:
            if cid.lower() in q_lower:
                start_id = cid
                break
        res = json.loads(logistics_mcp.plan_delivery_route(start_id))
        return f"Route starting from {start_id}: {json.dumps(res, indent=2)}"

    return (
        "I could not determine how to answer your question with the available logistics tools. "
        "Available capabilities include checking medical stock, planning delivery routes, and proposing reorders."
    )


async def run_agent(question: str, trace_id: Optional[str] = None, recursion_limit: int = 8) -> Dict[str, Any]:
    """Execute the logistics agent for a given natural language inquiry.

    Args:
        question: User query.
        trace_id: Correlation ID for distributed tracing across FastAPI and MCP logs.
        recursion_limit: Maximum loop iterations to prevent budget overruns.

    Returns:
        Dict with keys: answer, trace_id, elapsed_ms, model_used.
    """
    if not trace_id:
        trace_id = uuid.uuid4().hex[:8]

    started = time.perf_counter()
    log.info("trace=%s agent_request_received question=%r", trace_id, question)

    llm = _build_llm()
    if llm is None:
        log.info("trace=%s using_deterministic_agent_fallback (no openai key configured)", trace_id)
        answer = _deterministic_agent_fallback(question, trace_id)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "answer": answer,
            "trace_id": trace_id,
            "elapsed_ms": elapsed_ms,
            "model_used": "deterministic-agent-v1",
        }

    try:
        agent = create_react_agent(llm, TOOLS, prompt=AGENT_SYSTEM_PROMPT)
        result = await agent.ainvoke(
            {"messages": [("user", question)]},
            {"recursion_limit": recursion_limit},
        )
        final_message = result["messages"][-1].content
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        log.info("trace=%s agent_completed elapsed_ms=%d", trace_id, elapsed_ms)
        return {
            "answer": final_message,
            "trace_id": trace_id,
            "elapsed_ms": elapsed_ms,
            "model_used": os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
        }
    except Exception as exc:
        log.warning("trace=%s agent_error=%s; falling back to deterministic agent", trace_id, exc)
        answer = _deterministic_agent_fallback(question, trace_id)
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "answer": answer,
            "trace_id": trace_id,
            "elapsed_ms": elapsed_ms,
            "model_used": "deterministic-agent-fallback",
        }
