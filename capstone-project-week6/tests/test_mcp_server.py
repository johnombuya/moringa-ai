# tests/test_mcp_server.py - Verification for Deliverable 3 (MCP Server)
"""
Unit tests for the AfyaPlus Logistics MCP Server.
Verifies:
- Tool execution: check_stock, plan_delivery_route, reorder_supplies
- Resource reading: clinics://directory
- Input checking and boundaries
- Errors returned as instructive data (never unhandled exceptions)
- Deliberate invalid calls producing informative error structures
"""

import json
import pytest
import logistics_mcp


def test_check_stock_valid_item():
    """Verify check_stock returns valid inventory across all partner clinics."""
    raw = logistics_mcp.check_stock("amoxicillin")
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["item"] == "amoxicillin"
    assert len(data["stock"]) == 5
    assert data["low_stock_threshold"] == 10
    assert data["clinics_in_need"] >= 1


def test_check_stock_invalid_item_returns_instructive_data():
    """Verify check_stock rejects invalid items and returns instructive data (not exceptions)."""
    raw = logistics_mcp.check_stock("paracetamol_extra")
    data = json.loads(raw)
    assert data["status"] == "error"
    assert "Unknown item 'paracetamol_extra'" in data["error"]
    assert "amoxicillin" in data["error"]
    assert "hint" in data


def test_plan_delivery_route_valid_start():
    """Verify plan_delivery_route generates a valid circuit visiting all 5 clinics."""
    raw = logistics_mcp.plan_delivery_route("C01")
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["start_clinic_id"] == "C01"
    assert len(data["route_order"]) == 5
    assert data["total_km"] > 50.0
    assert data["algorithm"] == "nearest-neighbour heuristic"


def test_plan_delivery_route_invalid_clinic_id_returns_instructive_data():
    """Verify plan_delivery_route deliberately rejects unknown clinic IDs with instructive error data."""
    raw = logistics_mcp.plan_delivery_route("C99_INVALID")
    data = json.loads(raw)
    assert data["status"] == "error"
    assert "Unknown clinic id 'C99_INVALID'" in data["error"]
    assert "Valid ids" in data["error"]
    assert "hint" in data


def test_reorder_supplies_valid():
    """Verify valid supply reorder calculates projected stock and marks approval."""
    raw = logistics_mcp.reorder_supplies("C02", "amoxicillin", 40)
    data = json.loads(raw)
    assert data["status"] == "success"
    assert data["clinic_id"] == "C02"
    assert data["quantity_reordered"] == 40
    assert data["projected_stock"] == data["current_stock"] + 40
    assert data["approval_required"] == "coordinator"


def test_reorder_supplies_invalid_quantity():
    """Verify negative or excessive reorder quantity returns instructive error data."""
    raw = logistics_mcp.reorder_supplies("C02", "amoxicillin", -5)
    data = json.loads(raw)
    assert data["status"] == "error"
    assert "Invalid reorder quantity" in data["error"]


def test_clinic_directory_resource():
    """Verify the clinics://directory resource returns read-only clinic directory."""
    raw = logistics_mcp.clinic_directory()
    data = json.loads(raw)
    assert data["resource"] == "clinics://directory"
    assert data["count"] == 5
    assert any(c["id"] == "C01" for c in data["clinics"])
