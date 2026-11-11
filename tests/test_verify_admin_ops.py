"""Tests for scripts/verify-admin-ops.py.

These tests verify the checker's clearance classification against the
public vetting-summary shapes that GET /api/v1/projects/<id> actually
returns (observed live on 2026-11-11 and recorded in
research/admin/admin-operations.md). They run offline: they test that
the checker reads the three clearance kinds correctly, not the live
platform state.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "verify-admin-ops.py"

spec = importlib.util.spec_from_file_location("verify_admin_ops", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_admission_scan_clears_with_basis():
    vetting = {"state": "cleared", "basis": "admission", "assessment": {"state": "clean"}}
    assert module.clearance_kind(vetting) == "basis:admission"


def test_existing_project_exemption_is_grandfathered():
    vetting = {"state": "cleared", "assessment": None, "grandfathered": True}
    assert module.clearance_kind(vetting) == "grandfathered"


def test_owner_approved_exemption_carries_its_kind():
    vetting = {
        "state": "cleared",
        "assessment": None,
        "exemption": {"kind": "owner-approved-admission"},
    }
    assert module.clearance_kind(vetting) == "exemption:owner-approved-admission"


def test_unscanned_summary_is_other():
    vetting = {"state": "unscanned", "assessment": None}
    assert module.clearance_kind(vetting) == "other"
