# Payouts & bounties — the three payment paths and what the public record shows actually moved

## Target

Issue #3 — how SLOPCASH pays contributors. Sources pinned for this
packet:

- Public codebase `SlopDotCash/slopdotcash` at development commit
  `ced75d782d5836f60d84f46d50604f75a5852438`: `src/DirectBountyPayment.tsx`,
  `src/SolanaBountyPayment.tsx`, `src/SolanaBountyRecovery.tsx`,
  `src/EscrowFunding.tsx`, `src/BountySubmittedPayments.tsx`,
  `src/PayoutRows.tsx`, `src/PayoutConsent.tsx`, `backend/payments/`,
  and the PRD (`docs/slop-product-requirements.md`, sections 7, 8, 10).
- The live project registry `GET https://slop.cash/api/v1/projects`
  and the public payment routes under
  `https://slop.cash/api/v1/payments/`, fetched 2026-11-11.
- Solana mainnet, read-only, via the public RPC
  `https://api.mainnet-beta.solana.com` (checker:
  `scripts/verify-payout-vaults.py`).

## Claim

The payout system is fully built — direct wallet-signed bounty
payments, consent-bound escrow settlement out of deployed vaults, and
a signature-only recovery flow — but the public record shows money
actually moving only outside the monthly escrow system: the August
2026 direct transfers and one $0.98 net vault payment, while every
live monthly pool is pledged with committed 0 and payments disabled,
and the one funded Solana vault (eliza, 1,000 USDC deposited) has
paid out nothing.

## Evidence

### 1. The three paths, as implemented

**Direct payments (bounties, off-escrow).** For private bounty awards
the payer pays from their own wallet; the server only prepares and
verifies. `DirectBountyPayment.tsx` takes server-prepared EVM
transactions (`DirectEvmTransaction[]`) and has the payer connect the
exact payer wallet, check chain and sender, and broadcast; every
wallet prompt is recorded before it can broadcast and unknown
outcomes are never retried automatically (file header comment and
`checkWallet`). `SolanaBountyPayment.tsx` does the same for Solana: a
server-built transaction (base64 plan plus `messageId`) is sent only
through the owner's selected wallet, and the returned signature is
retained and handed to a `verify` callback. Per the PRD (section 8),
each finalized leg is recorded separately and a direct payment is
marked paid only when the researcher amount and any Slop share are
both proved; per `backend/payments/README.md` (migration 0014), these
transfers are imported from reviewed `disclosures/*.json` records
into `payment_direct_transfers`, never become obligations or
`state=paid`, and are never added to verified payout totals.

**Solana/EVM escrow (monthly pools).** A funded project's monthly
pool lives in one vault (`EscrowFunding.tsx` renders the vault
snapshot — total deposited, free vs reserved, payout fees — from
`GET /api/v1/payments/projects/<id>/vault`). `backend/payments/monthly.ts`
runs the coordinator: a frozen reward base is proposed, the owner
reserves awards against the vault's finalized balance, and the
existing executor settles reserved awards one recipient at a time.
Before settlement the recipient binds a wallet to the reserved award
through `PayoutConsent.tsx`: a signed `bind-challenge` /
`bind-authorize` exchange whose own header states consent authorizes
only that vault's destination binding — a finalized payment is a
separate result. `PayoutRows.tsx` displays each payout with network,
gross, fee, and net (`grossBase`/`feeBase`/`netBase`) in the PRD
section 6 states.

**Recovery.** `SolanaBountyRecovery.tsx` never sends a transaction:
it signs only messages the API has established are expired, with the
original payer's wallet, and the client re-verifies each Ed25519
signature against the payer before submitting. `BountySubmittedPayments.tsx`
retains submitted-payment records so a verification path survives a
wallet change hiding the old send request.

### 2. Registry sweep: pledged is not funded

`GET /api/v1/projects` returned 32 project records carrying a reward
block on 2026-11-11. Every monthly pool in the registry reads the
same way:

| Field | Value in every monthly-pool record |
|---|---|
| committedMinor | "0" |
| paymentMode | "disabled" |
| fundingState | "pledged" (one exception below) |
| funding.addresses | [] (empty in all 32 records) |
| funding.mode | "direct-noncustodial" — "Funds go directly to the project wallet. Slop does not hold or recover funds." |

The single exception is `delta-star`, whose fundingState is
`external-opportunity`: it has no monthly pool and points at an
external prize (an `externalPrize` block naming the Ethereum
Foundation Proximity Prize). Monthly caps are display values only —
for example eliza shows a $1,000 cap with per-cycle caps of 0 for
2026-07 through 2026-10, and asi a $250 cap with 0 caps for
2026-08 through 2026-10.

Only 5 of the 32 records carry a non-empty escrow deployment, all
under one policy (fee 200 basis points, withdrawal fee 200, fees
deducted from gross):

| Project | Network | Vault | Asset |
|---|---|---|---|
| eliza | solana-mainnet | `6NhxSaed6SF3uCAgzQViCZixETGpvxuFzo5eRGiaGM7` | USDC (`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`) |
| hyperliquid-source | solana-mainnet | `7PJ9FvVQaiNEiGDPDc4dytUinerkhWJq3qFd8bGp5PVK` | EPYH (`ABkr21iDncsKabf4CVfXuvkUjCWQkJszGyASL9M7pump`) |
| pumpfun-source | solana-mainnet | `DF4GtzFxZ5gMZhbS5ntMaTRFKepcHMqEX2YRHrQ48ahk` | PMUP (`35fWL6pdJqpconRZPrawUAQegw1QF3p2tgN7mzhTpump`) |
| slopdotcash | base-mainnet | `0x6c1297c3b96a00347cb501f572cb5811c2a8ed36` | USDC (`0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`) |
| thenetwork | robinhood-mainnet | `0xff77d3f1ca375b03fe12536c8d8111bb6a08805f` | USDG (`0x5fc5360d0400a0fd4f2af552add042d716f1d168`) |

### 3. On-chain: what the Solana vaults actually hold

`python3 scripts/verify-payout-vaults.py` at finalized slot
468,111,310 (2026-11-11) read each published Solana vault account
directly. Each vault is itself an SPL token account for its
deployment asset:

| Project | Vault balance (live RPC) |
|---|---|
| eliza | 1,000,000,000 base units = 1,000 USDC |
| hyperliquid-source | 0 EPYH |
| pumpfun-source | 0 PMUP |

The platform's own public snapshot agrees independently:
`GET /api/v1/payments/projects/eliza/vault` reports
`totalDeposited` 1000000000, `totalPaid` 0, `freeBalance` 1000000000
(observed 2026-10-30). A deposit is not a payout: the public paid
history `GET /api/v1/payments/projects/<id>/vault-payments` returns
`total` 0 for eliza, hyperliquid-source, and pumpfun-source, and
exactly one record overall — slopdotcash on Base, net 980000 base
units (0.98 USDC), transaction
`0x4b9290966d9bacbe77d0e936ccb749cc8c0b9622331bf8f4a42b965c1fa704d8`,
indexed 2026-10-27T09:46:01Z.

### 4. What actually moved: the August 2026 direct transfers

The public route `GET /api/v1/payments/projects/<id>/direct-transfers`
publishes the disclosed direct (off-escrow) transfers. Both projects
that have any show only contribution month 2026-08, settled on Solana
in USDC in September 2026:

| Project | Rows | totalMicro (USDC base units) | Block times |
|---|---|---|---|
| eliza | full list at the route | 4219710147 (= 4,219.710147 USDC) | 2026-09-11 |
| asi | 19 | 1785267199 (= 1,785.267199 USDC) | 2026-09-12 |

Two rows were re-verified on-chain against the public RPC
(`getTransaction`, finalized): eliza's largest row, 1,407,908,903 to
ss251, transaction
`XJGEmhbY3sWFtLoHSXXPhnWohFcDcgRDbo7f1fiTerd1HPwDYH3JuYCDSL2j8XbCfzrCL7hnJrKgFBu47bMf2GE`
(slot 446,210,805; a `transferChecked` of exactly 1,407,908,903 USDC
base units, blockTime matching the route's 2026-09-11T17:12:54Z), and
asi's first row, 386,680,391 to Prabhat1308, transaction
`3AE8idRMcSm9GE11WJTNqQvpvZZgQxJtdQ29SkrP62bXhHriewKL5Sx9sn4g4uHpvbFK3fNXuBxoSyg78Ci6DaFa`
(slot 446,295,825, same exact-amount match). So the only substantial
contributor payments visible in public records bypassed escrow
entirely — consistent with the registry's `direct-noncustodial`
funding mode.

### 5. Bounty terms: after-approval pledges, published splits

- General rule (PRD section 7): a project offers a monthly pool or a
  private bounty. New bounties use a 75/25 researcher/Slop split and
  an after-approval pledge; creation neither proves funds nor
  requires a bounty vault. Section 8 adds: an unfunded award decision
  creates no reservation or payment claim; approval and verified
  funds are required before reservation, and a vault-backed award
  reserves only its bounty vault's finalized free balance.
- Umia Protocol (PRD protected program terms, and the registry's
  `securityBounty` block for `umia-protocol`, status open): each
  accepted critical loss-of-funds finding carries a 10,000 USDC gross
  offer on Base — 7,500 to the first qualifying reporter, 2,500 to
  Slop — as an after-approval pledge; Slop fronts an approved award
  through its separate bounty vault after verified funding and Umia
  reimburses off-chain; no single-award program limit. The registry
  block agrees (grossMinor 10000000000, split 7500/2500,
  fundingPolicy after-approval, funding state pledged).
- Slop mainnet contracts (PRD protected program terms): each accepted
  critical loss-of-funds finding carries a $10,000 offer paid
  entirely (100%) to the first qualifying reporter — an authorized
  full-award exception with no Slop share or payout fee; scope is
  reviewed mainnet deployments from `contracts/evm/src` and
  `contracts/solana/programs`; also an after-approval offer.
- Orbio contracts (registry `securityBounty` block, the only other
  one in the registry): status open, bounty-only, after-approval,
  gross 2,000 CREDIT (grossMinor 2000000000, 6 decimals), split
  75/25, funding state pledged.

### 6. Public vs server-only

Public without sign-in: the project registry (caps, committed,
payment mode, funding state, escrow deployments), per-project vault
snapshots, paid vault-payment history, disclosed direct transfers,
and received totals (`backend/payments/public-records.ts` reads only
the ordinary payment tables; its header states security settlement
tables stay private). Server-only: an individual's awards, balances,
and wallet claims sit behind the GitHub session at
`GET /api/v1/payments/me`; bounty case contents and security
settlement records are not published; the `disclosures/*.json`
source records behind the direct-transfer import are not in the
public repository (only their imported, published rows are).

## Verification

What was run for this packet, and what a reviewer can re-run:

1. `git show ced75d782…:<path>` for every cited source file in
   `SlopDotCash/slopdotcash` (paths named in Target); PRD lines were
   read from `docs/slop-product-requirements.md` at the same commit
   (bounty rules in sections 7 and 8; protected programs under
   "Protected program terms").
2. `GET https://slop.cash/api/v1/projects` — full sweep of all 32
   reward-bearing records for `committedMinor`, `paymentMode`,
   `fundingState`, `funding.addresses`, and non-empty
   `escrow.deployments` (exactly 5), plus both `securityBounty`
   blocks.
3. `python3 scripts/verify-payout-vaults.py` — live read-only RPC
   check; observed output at slot 468,111,310: eliza 1,000 USDC,
   hyperliquid-source 0 EPYH, pumpfun-source 0 PMUP.
   `python3 scripts/verify-payout-vaults.py --offline` validates the
   embedded registry records with no network.
4. `GET /api/v1/payments/projects/eliza/vault` — public snapshot
   agreeing with the RPC read (deposited 1,000 USDC, paid 0).
5. `GET /api/v1/payments/projects/<id>/vault-payments` for
   slopdotcash (total 1, net 0.98 USDC), eliza,
   hyperliquid-source, pumpfun-source (total 0 each).
6. `GET /api/v1/payments/projects/eliza/direct-transfers` and
   `.../asi/direct-transfers` — totals quoted above; two sample
   transactions re-read with Solana RPC `getTransaction` and matched
   on amount, mint, and block time.
7. `python3 -m pytest tests/ -q` — the 3 new tests in
   `tests/test_verify_payout_vaults.py` pass, and the existing
   selector tests still pass (7 passed in total when run directly).

## Notes

- Boundaries: whether points themselves are redeemable is Issue
  #2's packet (PR #23); owner vault setup and withdrawal procedure
  are Issue #8 — vaults appear here only as payout rails
  (deployments, balances, paid history).
- The two EVM vaults (Base, Robinhood Chain) were not read on-chain
  in this packet; their public footprint is the registry deployment
  records and, for slopdotcash, the public vault-payment history
  above. Their live balances are therefore not claimed here.
- Direct-transfer rows beyond the two sampled transactions were not
  individually re-verified on-chain; the route totals are the
  platform's published figures, and the import pipeline (README,
  migration 0014) states each row reproduces from a reviewed
  disclosure before import.
- Balances and registry fields are point-in-time reads
  (2026-11-11); caps and cycle caps in the registry are display
  values set by project owners, not evidence of funds.
