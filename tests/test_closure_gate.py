"""Tests for scripts/closure_gate.py.

These tests verify the re-implementation of Slopbot's
closure-eligibility gate against the behavior documented in
research/workers/slopbot-closure-eligibility.md: five ordered checks,
each with its own failure reason, and branch precedence (an earlier
failing check decides, even when later checks would also fail).

They are offline: they test the gate logic in this repository, not the
live TypeScript source. The live source check is
`python3 scripts/closure_gate.py --verify-source`.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "closure_gate.py"

spec = importlib.util.spec_from_file_location("closure_gate", SCRIPT)
closure_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure_gate)

eligibility = closure_gate.closure_eligibility

GOOD = {
    "exemption": "not-exempt",
    "item_kind": "pull_request",
    "member": True,
    "recorded_skill_run": True,
}


def test_all_checks_pass_is_eligible():
    eligible, why = eligibility(GOOD)
    assert eligible is True
    assert why == "verified member with a recorded Slop run for this pull request"


def test_maintainer_is_never_closed():
    eligible, why = eligibility({**GOOD, "exemption": "exempt"})
    assert eligible is False
    assert why == "maintainers are never closed by Slopbot"


def test_unknown_maintainer_status_is_not_closed():
    eligible, why = eligibility({**GOOD, "exemption": "unknown"})
    assert eligible is False
    assert why == "maintainer status unknown"


def test_issue_is_not_closed():
    eligible, why = eligibility({**GOOD, "item_kind": "issue"})
    assert eligible is False
    assert why == "only Slop-skill pull requests can be closed"


def test_non_member_is_not_closed():
    eligible, why = eligibility({**GOOD, "member": False})
    assert eligible is False
    assert why == "author is not a verified slop.cash member"


def test_no_recorded_run_is_not_closed():
    eligible, why = eligibility({**GOOD, "recorded_skill_run": False})
    assert eligible is False
    assert why == "no recorded Slop run for this pull request"


def test_maintainer_check_wins_over_all_later_failures():
    evidence = {
        "exemption": "exempt",
        "item_kind": "issue",
        "member": False,
        "recorded_skill_run": False,
    }
    eligible, why = eligibility(evidence)
    assert eligible is False
    assert why == "maintainers are never closed by Slopbot"


def test_status_check_precedes_membership():
    evidence = {**GOOD, "exemption": "unknown", "member": False}
    eligible, why = eligibility(evidence)
    assert eligible is False
    assert why == "maintainer status unknown"
