"""Tests for scripts/solana-program-census.py and the pure helpers of
scripts/solana-program-livecheck.py.

The census tests build a minimal fixture checkout (Anchor.toml, one
program crate, a matching IDL, a programs.ts pin, one backend importer)
and check that the census accepts it and rejects a tampered IDL. The
live-check helper tests use fixed public vectors: the Config PDA and
the ProgramData address of the program ID studied in
research/contracts-solana/program-census.md, as observed on Solana
mainnet, and a Config account buffer rebuilt from its observed fields.
"""

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CENSUS = REPO_ROOT / "scripts" / "solana-program-census.py"
LIVECHECK = REPO_ROOT / "scripts" / "solana-program-livecheck.py"

FIXTURE_PROGRAM_ID = "11111111111111111111111111111111"
REAL_PROGRAM_ID = "7E5ZRh5y6Xgg7k3kdS75CMiTE2efoq9PqNWR5fCVDavQ"
CONFIG_PDA = "9hjoFnUrgF65K4DnWSDbS1WJjoGu4LChuz8XFq73UtaS"
PROGRAMDATA = "7rtCWezkARgmWBahGg4PYJf9oEmHwj5FwkWPrLrRM253"
LOADER = "BPFLoaderUpgradeab1e11111111111111111111111"


def load_livecheck():
    spec = importlib.util.spec_from_file_location("livecheck", LIVECHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha8(text):
    return list(hashlib.sha256(text.encode()).digest()[:8])


def build_fixture(root: Path):
    sol = root / "contracts" / "solana"
    (sol / "programs" / "demo" / "src").mkdir(parents=True)
    (sol / "idl").mkdir(parents=True)
    (sol / "Anchor.toml").write_text(
        '[programs.localnet]\nslop_escrow = "%s"\n' % FIXTURE_PROGRAM_ID
    )
    (sol / "Cargo.toml").write_text('[workspace]\nmembers = ["programs/*"]\n')
    (sol / "programs" / "demo" / "src" / "lib.rs").write_text(
        'declare_id!("%s");\n'
        "#[program]\n"
        "pub mod slop_escrow {\n"
        "    pub fn initialize(ctx: Context<Initialize>) -> Result<()> { Ok(()) }\n"
        "    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> { Ok(()) }\n"
        "}\n"
        "pub fn award_id_for() {}\n"
        "pub fn monthly_message() {}\n"
        "pub fn monthly_release_message() {}\n"
        "pub fn monthly_leaf() {}\n"
        "#[account]\n"
        "#[derive(InitSpace)]\n"
        "pub struct Project { pub deposited: u64 }\n"
        "#[event]\n"
        "pub struct Deposited { pub amount: u64 }\n"
        "#[error_code]\n"
        "pub enum EscrowError {\n"
        '    #[msg("wrong mint")]\n'
        "    WrongMint,\n"
        '    #[msg("zero amount")]\n'
        "    ZeroAmount,\n"
        "}\n" % FIXTURE_PROGRAM_ID
    )
    idl = {
        "address": FIXTURE_PROGRAM_ID,
        "instructions": [
            {"name": "initialize", "discriminator": sha8("global:initialize"), "args": []},
            {"name": "deposit", "discriminator": sha8("global:deposit"), "args": []},
        ],
        "accounts": [
            {"name": "Project", "discriminator": sha8("account:Project")}
        ],
        "events": [
            {"name": "Deposited", "discriminator": sha8("event:Deposited")}
        ],
        "errors": [
            {"code": 6000, "name": "WrongMint"},
            {"code": 6001, "name": "ZeroAmount"},
        ],
    }
    (sol / "idl" / "slop_escrow.json").write_text(json.dumps(idl))
    (sol / "programs.ts").write_text(
        "export const REVIEWED_SOLANA_PROGRAMS = [\n"
        "  {\n"
        '    network: "solana-mainnet",\n'
        '    programId: "%s",\n'
        '    codeSha256: "%s",\n'
        "  },\n"
        "];\n" % (FIXTURE_PROGRAM_ID, "a" * 64)
    )
    payments = root / "backend" / "payments"
    payments.mkdir(parents=True)
    (payments / "handler.ts").write_text(
        'import type { SolanaEscrowConfig } from "../../contracts/solana/adapter";\n'
    )
    return root


def run_census(path):
    return subprocess.run(
        [sys.executable, str(CENSUS), str(path)],
        capture_output=True,
        text=True,
    )


def test_census_accepts_consistent_fixture():
    with tempfile.TemporaryDirectory() as d:
        root = build_fixture(Path(d))
        result = run_census(root)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "CENSUS PASSED" in result.stdout
        assert "IDL instructions (2)" in result.stdout


def test_census_rejects_tampered_idl():
    with tempfile.TemporaryDirectory() as d:
        root = build_fixture(Path(d))
        idl_path = root / "contracts" / "solana" / "idl" / "slop_escrow.json"
        idl = json.loads(idl_path.read_text())
        idl["instructions"][1]["name"] = "deposit2"
        idl_path.write_text(json.dumps(idl))
        result = run_census(root)
        assert result.returncode == 1
        assert "CENSUS FAILED" in result.stdout


def test_census_rejects_missing_checkout():
    with tempfile.TemporaryDirectory() as d:
        result = run_census(Path(d))
        assert result.returncode == 1
        assert "CENSUS FAILED" in result.stdout


def test_base58_round_trip():
    lc = load_livecheck()
    assert lc.b58encode(b"\x00" * 32) == FIXTURE_PROGRAM_ID
    raw = lc.b58decode(REAL_PROGRAM_ID)
    assert len(raw) == 32
    assert lc.b58encode(raw) == REAL_PROGRAM_ID


def test_config_pda_vector():
    lc = load_livecheck()
    addr, bump = lc.find_program_address([b"config"], lc.b58decode(REAL_PROGRAM_ID))
    assert addr == CONFIG_PDA
    assert bump == 255


def test_programdata_pda_vector():
    lc = load_livecheck()
    addr, _ = lc.find_program_address(
        [lc.b58decode(REAL_PROGRAM_ID)], lc.b58decode(LOADER)
    )
    assert addr == PROGRAMDATA


def test_parse_config_account_round_trip():
    lc = load_livecheck()
    identity = "Eq6tYrPnkhj3hLmSZUL9xUWjkZ3Y5j3naBAJyQyKMYzS"
    fee = "9EyxVhhnCJH4QL5bDsRyukrkHFyitFMuf45UDdLxm4BY"
    rotation = "2tAA47aavW2mqtCAxbn21ZqLb8xZTeq8XvkRR9emduiy"
    data = (
        hashlib.sha256(b"account:Config").digest()[:8]
        + lc.b58decode(identity)
        + lc.b58decode(fee)
        + lc.b58decode(rotation)
        + bytes([255])
    )
    parsed = lc.parse_config_account(data)
    assert parsed == {
        "identity_authority": identity,
        "fee_recipient": fee,
        "rotation_authority": rotation,
        "bump": 255,
    }


def test_parse_config_account_rejects_bad_discriminator():
    lc = load_livecheck()
    try:
        lc.parse_config_account(b"\x00" * 105)
    except ValueError:
        return
    raise AssertionError("expected ValueError for bad discriminator")


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, fn in fns:
        fn()
        print(f"PASS {name}")
    print(f"{len(fns)} tests passed")
