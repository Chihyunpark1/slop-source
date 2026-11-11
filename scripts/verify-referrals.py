#!/usr/bin/env python3
"""Verify the referral-program claims of research/referrals/referral-flow-audit.md.

Reads the public SLOPCASH codebase (SlopDotCash/slopdotcash, MIT) and,
unless --offline is given, two public slop.cash endpoints. Standard
library only.

Usage:
    python3 scripts/verify-referrals.py [PATH_TO_SLOPDOTCASH_CHECKOUT] [--offline]

The checkout defaults to $SLOPDOTCASH_DIR, then ../slopdotcash-src,
then ./slopdotcash-src. Every check prints PASS/FAIL with the source it
read; the script exits non-zero if any check fails.
"""

import json
import os
import re
import sys
import urllib.request

REFERRAL_CODE_PATHS = [
    "backend/referrals/claims.ts",
    "backend/referrals/handler.ts",
    "backend/referrals/cache.ts",
    "workers/referral-accrual/core.ts",
    "workers/referral-accrual/config.ts",
    "workers/referral-accrual/store.ts",
    "src/ReferralClaims.tsx",
    "src/lib/referral-claims.ts",
    "contracts/evm/src/ReferralDistributor.sol",
]

EXPECTED_OUTCOMES = {
    "accrued",
    "project_cap",
    "pool_cap",
    "window_closed",
    "held",
    "referrer_excluded",
    "asset_not_eligible",
}

failures = []


def check(label, ok, detail=""):
    print(f"  [{'ok' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


def find_word(text, word):
    return re.findall(rf"\b{word}\b", text, flags=re.IGNORECASE)


def prd_numbers(prd):
    """Extract the published referral numbers from PRD section 11."""
    section = prd.split("### Referral program", 1)[1].split("\n### ", 1)[0]
    return {
        "rate": re.search(r"initial rate is (\d+) program tokens per 1 USDC", section),
        "pool": re.search(r"lifetime pool is ([\d,]+) tokens", section),
        "project_cap": re.search(r"([\d,]+)-token lifetime cap", section),
        "window": re.search(r"within (\d+) months of the project's first paid", section),
        "first_period": re.search(r"first period is (\w+ \d{4})", section),
    }


def parse_outcomes(core):
    block = core.split("export type Outcome =", 1)[1].split(";", 1)[0]
    return set(re.findall(r'"([a-z_]+)"', block))


def tier_hits(root):
    hits = []
    for rel in REFERRAL_CODE_PATHS:
        text = read(root, rel)
        for match in find_word(text, "tier"):
            hits.append(f"{rel}: {match}")
    return hits


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (verify-referrals)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    args = [a for a in sys.argv[1:] if a != "--offline"]
    offline = "--offline" in sys.argv
    root = (
        args[0]
        if args
        else os.environ.get("SLOPDOTCASH_DIR")
        or next(
            (p for p in ("../slopdotcash-src", "./slopdotcash-src") if os.path.isdir(p)),
            None,
        )
    )
    if not root or not os.path.isdir(root):
        print("error: slopdotcash checkout not found; pass its path as an argument")
        return 2

    print(f"checkout: {root}")
    print("PRD section 11 published numbers:")
    numbers = prd_numbers(read(root, "docs/slop-product-requirements.md"))
    check("rate is 3 program tokens per 1 USDC", bool(numbers["rate"]) and numbers["rate"].group(1) == "3")
    check("lifetime pool is 2,000,000 tokens", bool(numbers["pool"]) and numbers["pool"].group(1) == "2,000,000")
    check("per-project lifetime cap is 250,000 tokens", bool(numbers["project_cap"]) and numbers["project_cap"].group(1) == "250,000")
    check("window is 12 months from first paid obligation", bool(numbers["window"]) and numbers["window"].group(1) == "12")
    check("first period is November 2026", bool(numbers["first_period"]) and numbers["first_period"].group(1) == "November 2026")

    print("tiers:")
    hits = tier_hits(root)
    check("the word 'tier' appears in no referral code path", hits == [], f"{len(hits)} hits")

    print("attribution (invite and recording):")
    proposal = read(root, "src/ProjectProposalPage.tsx")
    check("proposal page reads a ?ref=<login> link", 'searchParams' in proposal or 'URLSearchParams(window.location.search).get("ref")' in proposal)
    handler = read(root, "backend/projects/handler.ts")
    for phrase in (
        "has not signed in to slop.cash",
        "You cannot refer your own project.",
        "The project steward cannot be recorded as its referrer.",
        "Slop team accounts cannot be recorded as referrers.",
    ):
        check(f"submission refuses: {phrase[:44]}...", phrase in handler)
    migration = read(root, "migrations/0055_project_referrer.sql")
    check("referrer pair trigger (id and login together)", "application referrer needs both id and login" in migration)
    check("referrer immutability trigger", "application referrer is immutable" in migration)

    print("accrual judging:")
    outcomes = parse_outcomes(read(root, "workers/referral-accrual/core.ts"))
    check("outcome set is exactly the 7 documented outcomes", outcomes == EXPECTED_OUTCOMES, ", ".join(sorted(outcomes)))
    store = read(root, "workers/referral-accrual/store.ts")
    check("candidates require state 'paid'", "o.state = 'paid'" in store)
    check("candidates require a recorded referrer", "p.referrer_github_id IS NOT NULL" in store)
    check("candidates exclude already-judged obligations", "NOT EXISTS (SELECT 1 FROM referral_accruals" in store)
    config = read(root, "workers/referral-accrual/config.ts")
    check("program flag gate: REFERRAL_PROGRAM_ENABLED must be 'true'", 'env.REFERRAL_PROGRAM_ENABLED ?? "").trim() !== "true"' in config)
    check("accrual modes are off / dry_run / live", 'mode !== "off" && mode !== "dry_run" && mode !== "live"' in config)
    check("rate comes from operator env, not a code constant", "REFERRAL_RATE_BASE_PER_MICRO" in config)

    if not offline:
        print("live public surface:")
        index = json.loads(fetch("https://slop.cash/api/v1/referrals/accruals"))
        check("accrual index schema", index.get("schema") == "slop-referral-accrual-index-v1", index.get("schema", "?"))
        print(f"        filed accrual files: {len(index.get('files', []))}")
        project = fetch("https://slop.cash/api/v1/projects/asi")
        check("public project record carries no referrer field", "referrer" not in project)

    print()
    if failures:
        print(f"result: {len(failures)} CHECK(S) FAILED")
        return 1
    print("result: ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
