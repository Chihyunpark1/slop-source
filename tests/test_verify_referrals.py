"""Tests for scripts/verify-referrals.py parsing helpers.

Run with: python3 -m pytest tests/test_verify_referrals.py
"""

import importlib.util
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "verify-referrals.py")
spec = importlib.util.spec_from_file_location("verify_referrals", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE_PRD = """## Section

### Referral program

The initial rate is 3 program tokens per 1 USDC of gross payout. The
lifetime pool is 2,000,000 tokens; each referred project has a
250,000-token lifetime cap. Only payouts within 12 months of the project's first paid obligation qualify.
The first period is November 2026.

### Another section

The initial rate is 9 program tokens per 1 USDC here and must be ignored.
"""


def test_prd_numbers_reads_only_the_referral_section():
    numbers = mod.prd_numbers(SAMPLE_PRD)
    assert numbers["rate"].group(1) == "3"
    assert numbers["pool"].group(1) == "2,000,000"
    assert numbers["project_cap"].group(1) == "250,000"
    assert numbers["window"].group(1) == "12"
    assert numbers["first_period"].group(1) == "November 2026"


def test_parse_outcomes():
    core = 'export type Outcome =\n  | "accrued"\n  | "pool_cap"\n  | "held";\n'
    assert mod.parse_outcomes(core) == {"accrued", "pool_cap", "held"}


def test_find_word_is_whole_word_and_case_insensitive():
    assert mod.find_word("No TIER here, just a frontier.", "tier") == ["TIER"]
    assert mod.find_word("nothing relevant", "tier") == []


def test_tier_hits_scans_the_referral_paths(tmp_path):
    for rel in mod.REFERRAL_CODE_PATHS:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("plain text\n", encoding="utf-8")
    assert mod.tier_hits(str(tmp_path)) == []
    target = tmp_path / mod.REFERRAL_CODE_PATHS[0]
    target.write_text("a tier appears\n", encoding="utf-8")
    assert len(mod.tier_hits(str(tmp_path))) == 1
