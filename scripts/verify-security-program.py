#!/usr/bin/env python3
"""Sweep the public Slop project registry for security bounty programs.

Reads GET https://slop.cash/api/v1/projects (public, read-only) and checks
every published `securityBounty` block against the program rules stated in
the public SLOPCASH codebase (SlopDotCash/slopdotcash, PRD section 8 and
src/lib/security-bounty.mjs):

- the split's basis points sum to 10,000;
- under the standard 75/25 split the gross amount (integer minor units)
  is divisible by four, so both shares are exact integers;
- under the full-award exception split (100/0) the researcher share is
  the whole gross;
- the program status is one of the five published statuses.

With --offline it runs the same aggregation and checks over a small
embedded sample instead of the network, so the checker itself can be
tested anywhere. Standard library only.
"""

import json
import sys
import urllib.request

REGISTRY_URL = "https://slop.cash/api/v1/projects"
KNOWN_STATUSES = {"draft", "pending-approval", "open", "paused", "closed"}
STANDARD_SPLIT = (7500, 2500)
FULL_AWARD_SPLIT = (10000, 0)

# Embedded sample for --offline: one standard-split program, one
# full-award program, and one project with no bounty block. Shapes mirror
# the live registry records.
SAMPLE_RECORDS = [
    {
        "id": "sample-standard",
        "securityBounty": {
            "status": "open",
            "eligibility": "critical-loss-of-funds",
            "fundingPolicy": "after-approval",
            "rewardMode": "separate",
            "funding": {"state": "pledged"},
            "amount": {
                "currency": "USDC",
                "decimals": 6,
                "network": "base",
                "grossMinor": "10000000000",
            },
            "split": {"researcherBasisPoints": 7500, "slopBasisPoints": 2500},
        },
    },
    {
        "id": "sample-full-award",
        "securityBounty": {
            "status": "open",
            "eligibility": "critical-loss-of-funds",
            "fundingPolicy": "after-approval",
            "rewardMode": "bounty-only",
            "funding": {"state": "pledged"},
            "amount": {"currency": "USD", "decimals": 2, "grossMinor": "1000000"},
            "split": {"researcherBasisPoints": 10000, "slopBasisPoints": 0},
        },
    },
    {"id": "sample-no-bounty"},
]


def records_from(payload):
    """Accept the registry list shape or a single-project shape."""
    if isinstance(payload, dict) and isinstance(payload.get("projects"), list):
        return payload["projects"]
    if isinstance(payload, dict) and isinstance(payload.get("project"), dict):
        return [payload["project"]]
    if isinstance(payload, list):
        return payload
    raise ValueError("unrecognized registry payload shape")


def amount_fields(amount):
    """Return (label, decimals, gross_minor) for either amount shape.

    Older terms carry {currency, decimals, grossMinor}; newer terms freeze
    an asset record {asset: {symbol, decimals, ...}, grossMinor}.
    """
    asset = amount.get("asset") or {}
    label = amount.get("currency") or asset.get("symbol") or "?"
    decimals = amount.get("decimals", asset.get("decimals"))
    return label, decimals, int(amount["grossMinor"])


def summarize(records):
    """Aggregate the registry records into program rows and check results."""
    rows = []
    problems = []
    for record in records:
        bounty = record.get("securityBounty")
        if not bounty:
            continue
        project_id = record.get("id", "?")
        split = bounty.get("split") or {}
        researcher_bps = split.get("researcherBasisPoints")
        slop_bps = split.get("slopBasisPoints")
        label, decimals, gross = amount_fields(bounty.get("amount") or {})
        row = {
            "id": project_id,
            "status": bounty.get("status"),
            "eligibility": bounty.get("eligibility"),
            "fundingPolicy": bounty.get("fundingPolicy"),
            "fundingState": (bounty.get("funding") or {}).get("state"),
            "rewardMode": bounty.get("rewardMode"),
            "currency": label,
            "decimals": decimals,
            "grossMinor": gross,
            "researcherBps": researcher_bps,
            "slopBps": slop_bps,
        }
        if row["status"] not in KNOWN_STATUSES:
            problems.append(f"{project_id}: unknown status {row['status']!r}")
        if researcher_bps is None or slop_bps is None:
            problems.append(f"{project_id}: split missing")
        elif researcher_bps + slop_bps != 10000:
            problems.append(
                f"{project_id}: split sums to {researcher_bps + slop_bps}, not 10000"
            )
        elif (researcher_bps, slop_bps) == STANDARD_SPLIT:
            if gross % 4 != 0:
                problems.append(
                    f"{project_id}: gross {gross} not divisible by 4 under 75/25"
                )
            row["researcherMinor"] = gross * 3 // 4
            row["slopMinor"] = gross - row["researcherMinor"]
        elif (researcher_bps, slop_bps) == FULL_AWARD_SPLIT:
            row["researcherMinor"] = gross
            row["slopMinor"] = 0
        else:
            problems.append(
                f"{project_id}: unpublished split {researcher_bps}/{slop_bps}"
            )
        rows.append(row)
    return rows, problems


def render(records, rows, problems):
    lines = []
    lines.append(f"projects swept: {len(records)}")
    lines.append(f"security bounty programs: {len(rows)}")
    by_status = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    for status in sorted(by_status):
        lines.append(f"  status {status}: {by_status[status]}")
    for row in rows:
        lines.append(
            "- {id}: status={status} eligibility={eligibility} "
            "fundingPolicy={fundingPolicy} funding={fundingState} "
            "rewardMode={rewardMode} gross={grossMinor} {currency} "
            "(decimals {decimals}) split={researcherBps}/{slopBps}".format(**row)
        )
        if "researcherMinor" in row:
            lines.append(
                "    derived shares: researcher {researcherMinor}, "
                "slop {slopMinor} (minor units)".format(**row)
            )
    if problems:
        lines.append("PROBLEMS:")
        lines.extend(f"  ! {problem}" for problem in problems)
    else:
        lines.append("all program checks passed")
    return lines


def main(argv):
    if "--offline" in argv:
        records = SAMPLE_RECORDS
        print("mode: offline (embedded sample)")
    else:
        request = urllib.request.Request(
            REGISTRY_URL, headers={"User-Agent": "slop-source-verify/1"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
        records = records_from(payload)
        print(f"mode: live ({REGISTRY_URL})")
    rows, problems = summarize(records)
    for line in render(records, rows, problems):
        print(line)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
