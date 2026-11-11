#!/usr/bin/env python3
"""Independent re-implementation of Slopbot's closure-eligibility gate.

The gate lives in the public SLOPCASH codebase at
`workers/slopbot/closure-eligibility.ts` (SlopDotCash/slopdotcash).
This script re-implements its decision logic from the documented
behavior — same checks, same order, same reason strings — so the
packet's claim can be re-checked without the TypeScript toolchain:

    python3 scripts/closure_gate.py
        Print the gate's decision for the canonical evidence cases.

    python3 scripts/closure_gate.py --verify-source
        Download the TypeScript source at the pinned commit and check
        that the gate's six decision reasons appear in it in branch
        order, alongside the two database lookups the packet cites.

The research packet is `research/workers/slopbot-closure-eligibility.md`.
Pure Python standard library only.
"""

import sys
import urllib.request

PINNED_COMMIT = "5330c937c4a896b576648512cb2bd053454a4b20"
SOURCE_URL = (
    "https://raw.githubusercontent.com/SlopDotCash/slopdotcash/"
    f"{PINNED_COMMIT}/workers/slopbot/closure-eligibility.ts"
)

# The gate's decision reasons, in branch order. The last one is the
# eligible outcome; the first five are the failure reasons.
REASONS_IN_BRANCH_ORDER = [
    "maintainers are never closed by Slopbot",
    "maintainer status unknown",
    "only Slop-skill pull requests can be closed",
    "author is not a verified slop.cash member",
    "no recorded Slop run for this pull request",
    "verified member with a recorded Slop run for this pull request",
]


def closure_eligibility(evidence):
    """Return (eligible, why) for one evidence record.

    Evidence fields mirror the TypeScript gate:
      exemption: "exempt" (maintainer), "not-exempt", or anything else
                 for an unresolved maintainer status.
      item_kind: "pull_request" or "issue".
      member: True when a points_members row matches the author's
              immutable GitHub ID.
      recorded_skill_run: True when the author's own authenticated Slop
              run recorded pull_request_opened for this exact PR.
    """
    if evidence["exemption"] == "exempt":
        return False, REASONS_IN_BRANCH_ORDER[0]
    if evidence["exemption"] != "not-exempt":
        return False, REASONS_IN_BRANCH_ORDER[1]
    if evidence["item_kind"] != "pull_request":
        return False, REASONS_IN_BRANCH_ORDER[2]
    if not evidence["member"]:
        return False, REASONS_IN_BRANCH_ORDER[3]
    if not evidence["recorded_skill_run"]:
        return False, REASONS_IN_BRANCH_ORDER[4]
    return True, REASONS_IN_BRANCH_ORDER[5]


GOOD = {
    "exemption": "not-exempt",
    "item_kind": "pull_request",
    "member": True,
    "recorded_skill_run": True,
}

CANONICAL_CASES = [
    ("all checks pass", GOOD),
    ("maintainer author", {**GOOD, "exemption": "exempt"}),
    ("maintainer status unknown", {**GOOD, "exemption": "unknown"}),
    ("an issue, not a pull request", {**GOOD, "item_kind": "issue"}),
    ("author not a member", {**GOOD, "member": False}),
    ("no recorded Slop run", {**GOOD, "recorded_skill_run": False}),
]


def verify_source(url=SOURCE_URL):
    """Check the pinned TypeScript source carries the gate as claimed."""
    with urllib.request.urlopen(url, timeout=30) as response:
        source = response.read().decode("utf-8")
    failures = []
    position = -1
    for reason in REASONS_IN_BRANCH_ORDER:
        found = source.find(reason)
        if found == -1:
            failures.append(f"reason not found: {reason!r}")
        elif found < position:
            failures.append(f"reason out of branch order: {reason!r}")
        else:
            position = found
    for needle, label in [
        ("points_members", "membership lookup table"),
        ("pull_request_opened", "recorded-run event kind"),
        ("isMember", "membership helper"),
        ("hasRecordedSkillRun", "recorded-run helper"),
        ("trace_runs", "trace runs table"),
        ("run_progress_events", "run progress events table"),
    ]:
        if needle not in source:
            failures.append(f"{label} not found: {needle!r}")
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--verify-source" in argv:
        print(f"source:    {SOURCE_URL}")
        failures = verify_source()
        if failures:
            for failure in failures:
                print(f"FAIL:      {failure}")
            return 1
        print("result:    gate reasons present, in branch order, with both")
        print("           database lookups (points_members, recorded run)")
        return 0
    for label, evidence in CANONICAL_CASES:
        eligible, why = closure_eligibility(evidence)
        outcome = "eligible" if eligible else "not eligible"
        print(f"{label:32} -> {outcome}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
