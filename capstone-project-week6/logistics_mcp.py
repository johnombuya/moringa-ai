# logistics_mcp.py - AfyaPlus Logistics MCP Server
"""
AfyaPlus Logistics MCP Server
-----------------------------
Production-grade Model Context Protocol (MCP) server providing health-logistics
tools and resources for rural Western Kenya clinic networks.

Exposes:
- Tools:
    1. check_stock: Query inventory of essential medicines across all partner clinics.
    2. plan_delivery_route: Heuristic delivery routing starting from a specific clinic.
    3. reorder_supplies: Validate and propose supply replenishment for a clinic.
- Resource:
    1. clinics://directory: Read-only directory of partner clinics and locations.

Standards:
- Strict input validation with informative error messages returned as structured data.
- Structured single-line logging per tool invocation for complete traceability.
- Safe execution: never raises unhandled exceptions to callers.
"""

import json
import logging
import math
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Configure structured single-line logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] logistics-mcp: %(message)s",
)
log = logging.getLogger("afyaplus-logistics")

mcp = FastMCP(
    "afyaplus-logistics",
    instructions="AfyaPlus health-logistics tools for inventory querying, route planning, and clinic directories.",
)

# Load clinic dataset relative to current file
DATA_FILE = Path(__file__).resolve().parent / "clinics.json"
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        CLINICS_DATA = json.load(f)["clinics"]
except Exception as exc:
    log.error("Failed to load clinics.json from %s: %s", DATA_FILE, exc)
    CLINICS_DATA = []

VALID_ITEMS = ["amoxicillin", "ors_sachets", "malaria_kits"]
LOW_STOCK_THRESHOLD = 10


def distance_km(a: dict, b: dict) -> float:
    """Calculate approximate geographical distance in kilometres between two clinics.

    Uses spherical approximation (equirectangular projection) for fast, low-overhead
    distance calculation suitable for Western Kenya coordinates.
    """
    dx = (a["lon"] - b["lon"]) * 111.32 * math.cos(math.radians((a["lat"] + b["lat"]) / 2))
    dy = (a["lat"] - b["lat"]) * 110.57
    return round(math.sqrt(dx * dx + dy * dy), 1)


@mcp.tool()
def check_stock(item: str) -> str:
    """Check how many units of a medical supply item each partner clinic holds.

    Args:
        item: The medical item identifier to check.
              Must be one of: 'amoxicillin', 'ors_sachets', 'malaria_kits'.

    Returns:
        JSON string containing the item queried, list of clinics with current stock levels,
        reorder flags (reorder_needed=true if units < 10), or an error payload if the item is invalid.
    """
    normalized_item = item.strip().lower()
    log.info("tool=check_stock item=%s raw_input=%r", normalized_item, item)

    if normalized_item not in VALID_ITEMS:
        log.warning("tool=check_stock status=rejected error=unknown_item item=%r", item)
        return json.dumps({
            "status": "error",
            "error": f"Unknown item '{item}'. Valid items: {VALID_ITEMS}",
            "hint": "Please choose from amoxicillin, ors_sachets, or malaria_kits.",
        })

    stock_records = [
        {
            "clinic_id": clinic["id"],
            "clinic": clinic["name"],
            "county": clinic["county"],
            "units": clinic["stock"].get(normalized_item, 0),
            "reorder_needed": clinic["stock"].get(normalized_item, 0) < LOW_STOCK_THRESHOLD,
        }
        for clinic in CLINICS_DATA
    ]

    low_stock_count = sum(1 for s in stock_records if s["reorder_needed"])
    log.info(
        "tool=check_stock item=%s clinics_checked=%d low_stock_count=%d",
        normalized_item, len(stock_records), low_stock_count,
    )

    return json.dumps({
        "status": "success",
        "item": normalized_item,
        "low_stock_threshold": LOW_STOCK_THRESHOLD,
        "clinics_in_need": low_stock_count,
        "stock": stock_records,
    })


@mcp.tool()
def plan_delivery_route(start_clinic_id: str) -> str:
    """Plan an efficient delivery route visiting every partner clinic starting from a specified clinic.

    Uses the nearest-neighbour heuristic: the delivery vehicle proceeds sequentially
    to the closest unvisited clinic until all network clinics have been serviced.

    Args:
        start_clinic_id: The ID of the clinic where the delivery starts (e.g., 'C01').

    Returns:
        JSON string with ordered route names, clinic IDs, segment distances, total kilometres,
        or an instructive error payload if start_clinic_id is not recognised.
    """
    normalized_id = start_clinic_id.strip().upper()
    log.info("tool=plan_delivery_route start_clinic_id=%s raw_input=%r", normalized_id, start_clinic_id)

    valid_ids = [c["id"] for c in CLINICS_DATA]
    start = next((c for c in CLINICS_DATA if c["id"].upper() == normalized_id), None)

    if start is None:
        log.warning("tool=plan_delivery_route status=rejected error=unknown_clinic start_clinic_id=%r", start_clinic_id)
        return json.dumps({
            "status": "error",
            "error": f"Unknown clinic id '{start_clinic_id}'. Valid ids: {valid_ids}",
            "hint": f"Choose one of the active partner clinic IDs: {', '.join(valid_ids)}",
        })

    route = [start]
    remaining = [c for c in CLINICS_DATA if c["id"].upper() != normalized_id]
    total_km = 0.0
    segments = []

    while remaining:
        current = route[-1]
        nearest = min(remaining, key=lambda c: distance_km(current, c))
        leg_dist = distance_km(current, nearest)
        total_km += leg_dist
        segments.append({
            "from": current["name"],
            "to": nearest["name"],
            "distance_km": leg_dist,
        })
        route.append(nearest)
        remaining.remove(nearest)

    total_km = round(total_km, 1)
    log.info(
        "tool=plan_delivery_route start=%s total_km=%.1f clinics_routed=%d",
        normalized_id, total_km, len(route),
    )

    return json.dumps({
        "status": "success",
        "start_clinic": start["name"],
        "start_clinic_id": start["id"],
        "route_order": [c["name"] for c in route],
        "route_ids": [c["id"] for c in route],
        "segments": segments,
        "total_km": total_km,
        "algorithm": "nearest-neighbour heuristic",
    })


@mcp.tool()
def reorder_supplies(clinic_id: str, item: str, quantity: int) -> str:
    """Validate and generate a supply reorder replenishment proposal for a clinic.

    Args:
        clinic_id: Target clinic identifier (e.g. 'C02').
        item: Medical item identifier ('amoxicillin', 'ors_sachets', or 'malaria_kits').
        quantity: Number of units to reorder (must be positive integer between 1 and 500).

    Returns:
        JSON string confirming proposal details or an error message if inputs fail validation.
    """
    normalized_id = clinic_id.strip().upper()
    normalized_item = item.strip().lower()
    log.info("tool=reorder_supplies clinic=%s item=%s qty=%d", normalized_id, normalized_item, quantity)

    clinic = next((c for c in CLINICS_DATA if c["id"].upper() == normalized_id), None)
    if not clinic:
        valid_ids = [c["id"] for c in CLINICS_DATA]
        log.warning("tool=reorder_supplies error=unknown_clinic clinic=%s", normalized_id)
        return json.dumps({
            "status": "error",
            "error": f"Unknown clinic id '{clinic_id}'. Valid ids: {valid_ids}",
        })

    if normalized_item not in VALID_ITEMS:
        log.warning("tool=reorder_supplies error=unknown_item item=%s", normalized_item)
        return json.dumps({
            "status": "error",
            "error": f"Unknown item '{item}'. Valid items: {VALID_ITEMS}",
        })

    if not isinstance(quantity, int) or quantity <= 0 or quantity > 500:
        log.warning("tool=reorder_supplies error=invalid_quantity qty=%r", quantity)
        return json.dumps({
            "status": "error",
            "error": f"Invalid reorder quantity {quantity}. Must be an integer between 1 and 500.",
        })

    current_units = clinic["stock"].get(normalized_item, 0)
    projected_units = current_units + quantity

    log.info(
        "tool=reorder_supplies status=proposed clinic=%s item=%s curr=%d add=%d projected=%d",
        normalized_id, normalized_item, current_units, quantity, projected_units,
    )

    return json.dumps({
        "status": "success",
        "action": "reorder_proposed",
        "clinic_id": clinic["id"],
        "clinic_name": clinic["name"],
        "county": clinic["county"],
        "item": normalized_item,
        "current_stock": current_units,
        "quantity_reordered": quantity,
        "projected_stock": projected_units,
        "approval_required": "coordinator",
    })


@mcp.resource("clinics://directory")
def clinic_directory() -> str:
    """Read-only directory listing all active AfyaPlus partner clinics with geographic coordinates.

    Returns:
        JSON string representing an array of clinic records containing id, name, county,
        latitude, longitude, and contact metadata.
    """
    log.info("resource=clinics://directory count=%d", len(CLINICS_DATA))
    directory = [
        {
            "id": c["id"],
            "name": c["name"],
            "county": c["county"],
            "latitude": c["lat"],
            "longitude": c["lon"],
        }
        for c in CLINICS_DATA
    ]
    return json.dumps({"resource": "clinics://directory", "count": len(directory), "clinics": directory})


if __name__ == "__main__":
    log.info("Starting AfyaPlus Logistics MCP Server via stdio transport...")
    mcp.run()
