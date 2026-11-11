# Solana program census — one Anchor program, and its reviewed mainnet pin verified live

## Target

The Solana side of the public SLOPCASH codebase (`SlopDotCash/slopdotcash`,
MIT) at development commit `ced75d782d5836f60d84f46d50604f75a5852438`:
the Anchor workspace `contracts/solana/` (`Anchor.toml`, `Cargo.toml`,
`programs/slop-escrow/src/lib.rs`, `token_policy.rs`, the checked-in IDL
`idl/slop_escrow.json`), the TypeScript adapter layer beside it
(`contracts/solana/*.ts`), and the program's live deployment on Solana
mainnet-beta, read through the public RPC endpoint
`https://api.mainnet-beta.solana.com`. Census checker:
`scripts/solana-program-census.py`; live checker:
`scripts/solana-program-livecheck.py`; tests:
`tests/test_solana_program_census.py`.

## Claim

The Solana side of the platform is exactly one Anchor program —
`slop_escrow`, 25 instructions — and the program ID that `Anchor.toml`
declares for localnet is the same ID whose live mainnet deployment
matches the platform's own reviewed pin in `contracts/solana/programs.ts`
(code-region SHA-256, upgrade authority, and all three Config
authorities), re-verified against public mainnet RPC on 2026-11-11 at
finalized slot 468,120,538.

## Evidence

### One workspace, one program

- `contracts/solana/Cargo.toml` is a workspace with
  `members = ["programs/*"]`, and `programs/` contains exactly one
  crate, `slop-escrow` (Anchor 0.32.1; `Anchor.toml` pins
  `anchor_version = "0.32.1"` and the crate's `Cargo.toml` depends on
  `anchor-lang = "=0.32.1"`).
- Three identifiers agree exactly: `declare_id!` in
  `programs/slop-escrow/src/lib.rs`, the single entry under
  `[programs.localnet]` in `Anchor.toml`, and the `address` field of
  the checked-in IDL are all
  `7E5ZRh5y6Xgg7k3kdS75CMiTE2efoq9PqNWR5fCVDavQ`. `Anchor.toml` has no
  mainnet, devnet, or testnet program section — localnet is the only
  cluster it declares.

### Instruction inventory (25)

The IDL instruction set is identical to the `pub fn` set of the
`#[program]` module; the only other public functions in `lib.rs` are
four non-program helpers (`award_id_for`, `monthly_message`,
`monthly_release_message`, `monthly_leaf`). Every IDL instruction
discriminator equals `sha256("global:<name>")[..8]`. Arguments below
are the IDL's; grouping is by name and argument shape.

- Setup: `initialize_config(identity_authority, fee_recipient,
  rotation_authority)` creates the singleton Config;
  `initialize(...)` / `initialize_native(...)` create one Project and
  its vault for a token mint / for native SOL (both take `project_id`,
  `network`, `identity_authority`, `fee_recipient`, `binding_delay`,
  `rotation_delay`, `purpose`); `migrate_project()` upgrades a stored
  Project.
- Funding in: `deposit(amount)` moves SPL tokens (classic or the
  admitted Token-2022 subset) into the vault with a checked transfer
  using the mint's decimals; `deposit_native(amount)` moves lamports
  through the system program. Both reject zero, increment
  `project.deposited`, and emit `Deposited` (handlers at
  `lib.rs:254` and `lib.rs:277` in the pinned source).
- Commitments: `commit(award_id, source_digest, actor_id, gross)` and
  `commit_bounty(...)` record one award obligation, gated on the
  project's `Purpose` (`Ordinary` vs `Bounty`, `lib.rs:1669`);
  `set_monthly_commitment(cap, enabled)`;
  `commit_monthly(period, allocation_root, total, frozen_at)` stores
  one period's 32-byte allocation root — the per-award amounts are
  computed off-chain and only the root is committed;
  `commit_monthly_award(..., index, count, proof)` commits one award
  against that root with a Merkle-style proof of `AllocationNode`s.
- Payout and release: `pay(expected_version)` / `pay_native(...)`
  settle a committed obligation to the bound wallet;
  `release_monthly_award(..., proof)` releases one monthly award;
  `release_monthly_reserve(period, expected_unsettled, released)`
  returns the unused part of a period's reserve.
- Owner recovery and fees: `withdraw(gross)` / `withdraw_native(gross)`
  take unused funds back out; `claim_fees()` / `claim_fees_native()`
  collect accrued fees to the Config's fee recipient.
- Wallet binding and authority rotation: `bind_wallet(actor_id,
  network, expected_version, claim_digest, expires_at)`,
  `veto_binding(actor_id, version)`, and the four-step rotation
  `propose_authority_rotation(next)` → `confirm_authority_rotation()` /
  `cancel_authority_rotation()` → `execute_authority_rotation()`.

Five instruction pairs are token/native twins (`initialize`,
`deposit`, `pay`, `withdraw`, `claim_fees`); the other fifteen are
asset-agnostic.

### State, events, errors

- Seven `#[account]` state types, identical to the IDL account list:
  `Config` (singleton, PDA seeds `[b"config"]`), `Project` (seeds
  `[b"project", owner, project_id, purpose]`), `MonthlyAllocation`,
  `Obligation`, `WalletBinding`, `BindingVeto`, `Origin`. PDA seed
  literals appearing in `lib.rs`: `award`, `config`, `month`,
  `origin`, `project`, `settled`, `vault`, `veto`, `wallet`. The
  per-project token vault is itself a PDA (seeds `[b"vault", project]`)
  whose authority is the Project account.
- 17 `#[event]` structs, identical to the IDL event list, each with
  discriminator `sha256("event:<Name>")[..8]`.
- 38 `EscrowError` variants, identical in name and order to the IDL
  error list, codes 6000–6037.

### The off-chain reviewed pin

`contracts/solana/programs.ts` holds exactly one reviewed program
entry: network `solana-mainnet`, the same program ID, `sourceCommit
c9564479a65523756fd2998e04d192be3f88579a` (the source the deployed
artifact was built from — an earlier commit than the research target
above), `codeSha256
f250228d87493c024737de9dea4290ed0d28ed777eaddf17b874d493b77274a6`,
upgrade authority `EmMRRFhjZmr2SN5RdhV98WPnUhgJxKMoE1itSwUsU8tr`,
identity authority `Eq6tYrPnkhj3hLmSZUL9xUWjkZ3Y5j3naBAJyQyKMYzS`,
fee recipient `9EyxVhhnCJH4QL5bDsRyukrkHFyitFMuf45UDdLxm4BY`,
rotation authority `2tAA47aavW2mqtCAxbn21ZqLb8xZTeq8XvkRR9emduiy`.
Its header comment states the pin "permits owner setup only on
configured networks; it does not enable wallet binding, attester
signing, payments or a keeper", and that project vaults are registered
in D1 after creation. `contracts/solana/adapter.ts` re-checks the pin
before use: it reads the ProgramData account, requires the 45-byte
loader header, compares the upgrade authority and the SHA-256 of the
code region after that header with the pin, and reads the Config PDA's
pinned roles.

### Live mainnet observation (2026-11-11, finalized)

Read-only `getAccountInfo` calls at finalized commitment (context
slot 468,120,538); no transaction was sent.

- Program account `7E5Z…avQ`: exists, `executable: true`, owned by
  `BPFLoaderUpgradeab1e11111111111111111111111` (upgradeable loader).
- ProgramData `7rtCWezkARgmWBahGg4PYJf9oEmHwj5FwkWPrLrRM253` (address
  read from the program account and independently re-derived as the
  loader PDA): last-deploy slot **462,466,131** — the slot the
  `programs.ts` comment names for the Token-2022 upgrade; upgrade
  authority `EmMRRF…UsU8tr`, matching the pin; code region after the
  45-byte header is 731,040 bytes and its SHA-256 is
  `f250228d…74a6`, matching the pinned `codeSha256` exactly — i.e. the
  adapter's own pre-use comparison passes against live state.
- Config PDA derived from seeds `[b"config"]`:
  `9hjoFnUrgF65K4DnWSDbS1WJjoGu4LChuz8XFq73UtaS` (bump 255) — the
  address `contracts/DEPLOY-MAINNET.md` records. The account is owned
  by the program, its Anchor discriminator matches
  `sha256("account:Config")[..8]`, and its three stored authorities
  parse to exactly the pinned identity authority, fee recipient, and
  rotation authority; the stored bump equals the derived bump.

### How the platform connects

Nothing outside `contracts/solana/` talks to the Rust program
directly; the connection is the TypeScript adapter layer in the same
directory (`adapter.ts`, `commitment.ts`, `funding.ts`,
`monthly-commitment.ts`, `monthly-reserve.ts`, `owner-creation.ts`,
`owner-instructions.ts`, `token*.ts`, `transactions.ts`,
`wallet-transactions.ts`, `programs.ts`). The census lists every file
outside `contracts/solana/` that imports it; the production importers
include `backend/payments/handler.ts` (adapter, commitment, funding,
monthly-commitment), `backend/payments/solana-funding.ts`,
`backend/projects/vault-setup.ts` (adapter, owner-creation,
owner-instructions, programs, wallet-transactions),
`backend/security/direct-solana.ts`, `src/lib/solana-vault-actions.ts`,
`src/lib/monthly-*-actions.ts`, `workers/payment-executor/*`,
`workers/fee-converter/*`, and `workers/payments/*`. Per-project
deployment records (RPC URL, project PDA, vault, mint, the same
authority pins) are carried in the `SolanaEscrowConfig` shape defined
by `adapter.ts` and, per the `programs.ts` comment, registered in D1
after a vault is created.

### On-chain vs off-chain

| On-chain (verifiable from the chain) | Off-chain (code/config/trust) |
|---|---|
| Program code in the ProgramData account; its SHA-256 is publicly recomputable | Which deployment is *reviewed*: the `programs.ts` pin and its source commit |
| Config authorities; Project, Obligation, MonthlyAllocation, WalletBinding, BindingVeto, Origin accounts | Per-project deployment registry in D1 (RPC URL, PDA, vault, mint) |
| Vault token/lamport balances held at the vault PDAs | The monthly allocation amounts; only their 32-byte root is committed on-chain |
| Instruction effects and the 17 event types in transaction logs | Transaction construction and signing flow in the adapter layer; keeper/executor operation |

## Verification

All commands run against a checkout of `SlopDotCash/slopdotcash` at
`ced75d782d5836f60d84f46d50604f75a5852438`.

- `python3 scripts/solana-program-census.py <checkout>` — observed:
  one Anchor.toml program section (`localnet`) and one entry; one
  program crate; `declare_id!` == Anchor.toml == IDL address; source
  instruction set == IDL set (25) plus the 4 named helpers; all
  instruction/account/event discriminators match the Anchor
  convention; 7 accounts, 17 events, 38 errors in order (codes
  6000–6037); seed literal list as above; the `programs.ts` pin set
  extracted; the external importer list printed; final line `CENSUS
  PASSED`.
- `python3 scripts/solana-program-livecheck.py <checkout>` — observed
  at finalized slot 468,120,538: all eight comparisons (loader owner,
  executable, ProgramData address, upgrade authority, code SHA-256,
  Config identity/fee/rotation authorities, Config bump) printed OK;
  final line `LIVECHECK PASSED`. Re-running it later checks the pin
  against whatever the chain holds at that time.
- `python3 -m pytest tests/test_solana_program_census.py` — 8 tests:
  census over a fixture tree (accept, tampered-IDL reject, missing
  checkout reject) and live-check helper vectors (base58 round-trip,
  Config PDA, ProgramData PDA, Config parse round-trip and reject).
  In this environment pytest was not installed, so the test functions
  were executed directly; all 8 passed. The pre-existing selector
  tests were not touched.

## Notes

- Scope boundaries: the EVM contracts (issue #10) are a separate
  packet. Within issue #11, PR #41 already covers the Token-2022
  admission helpers in `token_policy.rs` and PR #51 the deposit
  counter behavior of the two deposit handlers, both pinned to an
  older upstream commit (`7dc83b50…`); this packet is the
  program-level census and pin verification at the current tip and
  cites those two for their slices. The SLOP token itself (PR #22),
  payout paths (PR #32), and owner vault procedure (PR #54) are cited
  only where they touch this surface.
- `contracts/DEPLOY-MAINNET.md` also records an earlier Solana upgrade
  (finalized slot 461,493,344, code-region SHA-256 `38c8d776…2005`).
  That hash does **not** match the code region observed live; the
  `programs.ts` pin (deploy slot 462,466,131) does. Both records are
  in the same document set; the live check is the deciding evidence.
- Control observation: the same program ID also resolves on devnet
  (checked 2026-11-11), but with a different code hash
  (`8392ce12…8a38`), a different upgrade authority, and last-deploy
  slot 515,667,540 — i.e. a separate deployment, not the reviewed
  mainnet pin. Only mainnet was checked against the pin.
- Limits: the IDL was taken as checked in; no Anchor build was run to
  regenerate it. Live values are a point-in-time observation at the
  stated finalized slot — the upgrade authority can replace the
  program at any later slot, after which the live check would report
  a mismatch rather than pass. No Project account census was taken;
  per-project activation state is D1-side data, not read here.
