# Owner vault setup, registration verification, and withdrawal rules

## Target

Issue #8 — how a project owner creates, registers, and withdraws from an
ordinary (or bounty) vault in the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`: the vault setup route
(`backend/projects/handler.ts`, `backend/projects/vault-setup.ts`), the
registry documentation (`backend/projects/README.md`, "Owner vault
setup"), the creation-transaction verifiers
(`contracts/evm/adapter.ts` and the Solana owner-creation path), the
owner UI (`src/OwnerVaultSetup.tsx`, `src/VaultActions.tsx`), the vault
totals shape (`contracts/vault-totals.ts`), and the live public
registry at `https://slop.cash/api/v1/projects` read on 2026-11-11.

The packet is the procedure and its verification rules: who may set a
vault up, what the server checks before creation and again at
registration, what happens when the monthly amount moves while a
creation is pending, and which owner actions survive a project
restriction. What the vaults hold and what has been paid out is the
payouts packet's subject (issue #3); amounts are cited here only where
the setup rules themselves turn on them.

## Claim

An owner vault exists in the registry only after a server-verified,
owner-signed procedure: the platform checks current GitHub authority
and a confirmed owner wallet, verifies the reviewed factory (EVM) or
program (Solana) before creation, and at registration verifies the
exact finalized creation transaction against the registry revision
before appending the project's one deployment record — and once
registered, the vault's free funds stay withdrawable by the owner
alone, with reads, transaction checks, and withdrawals surviving a
project restriction that stops new setup and deposits.

## Evidence

### The route, and who may use it

- One route pair does setup: `GET /api/v1/project-vaults/:id` lists the
  served setup networks and the current revision, and
  `POST /api/v1/project-vaults/:id` "reviews an unsigned ordinary-vault
  creation or registers its finalized transaction" (routes table,
  `backend/projects/README.md:53-54`). Both need a site session; the
  POST additionally needs a confirmed wallet.
- Write access is not enough. After the session, maintainer-ban, and
  restriction checks, the handler requires the caller to be the project
  steward or a repository admin — anyone else gets HTTP 403
  `vault_authority_required` (`backend/projects/handler.ts:1397`,
  `ownerVault` at line 1343). The code comment states the reason: a
  project has one ordinary vault and no replacement, and its owner
  controls refunds and the monthly switch.
- The registry's ordinary edit route can never create the record: an
  owner revision "never adds or changes an `escrow.deployments` record:
  this API reads no chain state, so it cannot verify the vault"
  (`backend/projects/README.md:150-154`). The vault route is the only
  way in.

### Before creation: wallet, preconditions, factory

- The owner first confirms a current wallet through the payment
  wallet-claim route. The server derives the project digest, asset, and
  cap from the current registry revision; the wallet signs the exact
  creation and "the server never signs or broadcasts"
  (`backend/projects/README.md:445-452`). In the service, the claim is
  looked up among effective payment wallet claims joined to the
  caller's own authorizations for that chain; no claim, no creation —
  HTTP 403 `wallet_signature_required`
  (`backend/projects/vault-setup.ts:263-272`).
- Preconditions fail closed with HTTP 422 `vault_setup_unavailable`:
  an ordinary vault needs a saved monthly-pool reward whose chain
  matches the chosen network and a positive monthly cap in base units;
  a bounty vault needs saved USDC bounty terms on the matching network
  and may not request the monthly setting
  (`backend/projects/vault-setup.ts`, `resolve`). The Solana cap must
  also fit the program's unsigned 64-bit limit.
- Setup lists only served networks that have a factory record. The
  candidate factories/programs are the reviewed set plus infrastructure
  read from existing D1 deployment records, reduced to each template's
  current review — a new vault never inherits another project's owner,
  asset, vault, or upgrade history (`vault-setup.ts`, `currentReview`
  and `factories`/`programs`). The platform fee wallet must be separate
  from the vault owner and the identity authority, or the request fails
  with HTTP 422 `vault_role_conflict` (`vault-setup.ts:406`).
- Factory verification happens before creation: "Slop verifies that
  factory's current code and compatibility. On Solana it verifies the
  program bytes, upgrade authority and pinned Config"
  (`backend/projects/README.md:454-456`). For EVM,
  `verifyEvmFactory` (`contracts/evm/adapter.ts:329`) checks that the
  reviewed identity is complete (factory, registrar, identity
  authority, fee recipient, and SHA-256 pins for the vault and factory
  code) and reads the proxy's EIP-1967 implementation slot, so proxy
  bytecode alone does not identify the logic; the upgrade authority
  must also differ from the fee recipient and identity authority.

### Registration: the exact finalized transaction, verified

- "Registration verifies the exact finalized transaction, project
  digest, owner, asset, purpose, code and monthly setting before
  appending one revision" (`backend/projects/README.md:456-458`).
  Registration re-runs the factory check at the finalized block tag
  (`vault-setup.ts:511`) and then verifies the creation transaction
  itself (`verifyEvmVaultCreation`, `contracts/evm/adapter.ts:1253`):
  the receipt must exist and sit at or below the finalized block —
  otherwise verification returns nothing and the handler answers
  `{status: "pending"}` (`backend/projects/handler.ts:1542`); the
  receipt must match its canonical block; the sender must be the
  owner, the target the reviewed factory, the calldata exactly the
  reviewed creation, and the value zero; the receipt status must be
  success; and the deployed vault is verified at both the creation
  block and the finalized block against the expected project digest.
  The monthly cap and monthly-enabled flag are read at the creation
  block, so a later owner change cannot block registration of an
  earlier reviewed creation.
- Registration is idempotent and single: a retry whose transaction is
  already recorded returns the registered deployment
  (`handler.ts:1443-1453`); a second vault is refused with HTTP 409
  `vault_already_registered` (`vault-setup.ts:594`, bounty at line
  560). A bounty registration pins the settlement terms — 25% bounty
  fee (2500 basis points), 2% withdrawal fee, fees deducted from the
  gross amount (`vault-setup.ts:571-573`) — and records the current
  UTC cycle as the effective cycle.
- A send whose outcome is unknown stays pending: "An unknown send
  stays pending until the owner recovers its transaction hash; it
  never sends again by itself" (`backend/projects/README.md:458-461`).
  The UI mirrors this: an already-existing vault produces "This vault
  already exists. Recover its creation transaction instead of sending
  another." (`src/OwnerVaultSetup.tsx:320`). An owner with exactly one
  current confirmed wallet on the network can review an existing vault
  and recover its registration without a connected browser wallet; if
  no existing vault is found, that path offers no creation transaction
  (`backend/projects/README.md:461-463`; `src/OwnerVaultSetup.tsx:281`).

### When the monthly amount changes while creation is pending

- The review step pins the registry revision: a review against a stale
  revision fails with HTTP 409 `stale_revision`
  (`handler.ts`, `ownerVault`). Registration is the exception: when
  the expected revision is no longer current, the server loads the
  stored text of the reviewed revision and checks policy compatibility
  — reward kind and chain, the escrow block, and the reward asset must
  still match (for a bounty vault, the amount's currency, network,
  decimals, and asset, plus the settlement block). A mismatch fails
  with HTTP 409 `vault_policy_changed`; the monthly amount itself is
  deliberately not part of the compatibility check
  (`handler.ts:1480-1525`).
- The consequence, per the registry documentation: "registration
  checks that transaction against its original immutable revision. The
  current asset and vault policy must still match. Registration keeps
  the current project amount and shows both amounts. The owner can
  then apply the current amount through the existing automatic payment
  control" (`backend/projects/README.md:469-473`). The same
  next-month discipline applies to the amount itself: a financial
  policy change applies from the next UTC calendar month, and the new
  amount pins every month from the reward start through the open cycle
  that has no recorded cap to the previous amount
  (`backend/projects/README.md:158-167`).

### The monthly setting

- Monthly payment is On by default at creation, and "the owner can
  choose Off before review to opt out (owner decision, 25 Oct 2026).
  The atomic creation builder records that setting and the cap in one
  transaction" (`backend/projects/README.md:465-467`). The setup form
  starts from On (`src/OwnerVaultSetup.tsx:128`) and forces the
  setting off for bounty vaults, which have no monthly setting.
- After registration the switch lives with the owner: a
  `monthly-settings` write (`automatic`) "turns the automatic default
  off or on again", while write-or-maintain permission can read the
  month and prepare its commitment but cannot change the automatic
  default, allocations, finalization, or reserve release
  (`backend/payments/README.md:298-300`). The scheduled freeze that
  drives automatic payment is skipped when the owner turned the
  default off, when the project is restricted or paused, or when the
  vault network is not served (`backend/payments/README.md:303-307`).

### Withdrawals and reserve release

- Withdrawing is owner-only at the wallet level: the funding UI
  requires the vault owner's wallet to withdraw free funds — "Only the
  owner may withdraw; any other wallet can only deposit", and a
  non-owner connection is switched to deposit
  (`src/VaultActions.tsx:164-169`, and the form note at line 512).
  Withdrawal is limited to free funds: "Reserved awards cannot be
  withdrawn. Funds go only to" the deployment's owner, and deposits
  carry no refund right for the depositor
  (`src/VaultActions.tsx:565-574`). Solana funding actions go through
  a review/check pair in which the check verifies the wallet signature
  over the finalized message and requires the reviewed instructions,
  accounts, privileges, and token deltas; withdrawals keep exact
  message matching (`backend/payments/README.md:214-231`).
- Reserve release is a separate, narrow repair path, not a general
  withdrawal: the owner release UI (`src/OwnerReserveRelease.tsx:29-33`)
  keeps the reserve held unless the complete original allocation is
  available and a wrong-sum fault is proven — its refusal states are
  that the allocation is unavailable, the reserve is not proven
  faulty, the total is correct, or the reserve has already changed.

### Restrictions: what stops, what survives

- A restriction stops new setup and deposits: the ordinary branch of
  the setup route fails with HTTP 409 `project_restricted`
  ("Request reinstatement before setting up a vault.",
  `handler.ts:1386`), and a Solana bounty deposit review under
  restriction fails the same way (`handler.ts:1334`).
- What survives: "A restriction stops new setup and deposits in Slop,
  but the owner can still read funded state, check transactions and
  withdraw free funds. Chain transactions remain public"
  (`backend/projects/README.md:479-481`). The bounty branch of the
  setup route keeps its read open during a restriction — it returns
  the funded state and a `canSetup` flag that is true only when the
  project is clear and neither the actor nor the steward is banned —
  under the code comment "Reading funded obligations and owner exits
  remains available during a restriction"
  (`handler.ts:1358-1366`).

### Public data versus server-only data

- Public: the registry manifest itself, including each deployment
  record's 19 fields (network, vault, owner, asset, factory, program
  id, code hashes, authorities, delays, source commit, and the
  deployment transaction). Vault totals are public as snapshots: one
  row per vault read at one finalized block or slot, with the counters
  of `contracts/vault-totals.ts` (deposited, paid, payout fees, gross
  withdrawn, withdrawal fees, free balance, reserved principal and
  fees, accrued fees, combined reserve; a counter a vault type does
  not have is null). The public route
  `GET /api/v1/payments/projects/<id>/vault` serves these rows from
  the snapshot store with a 30-minute staleness bound; page views
  never read a chain RPC, and a null counter shows as "not reported",
  never zero (`backend/payments/README.md:203-212`).
- Server-only or owner-gated: "The Manage page shows bounty funds only
  after a current GitHub owner check; public payment queries never
  read private snapshots" (`backend/projects/README.md:477-479`).
  Funding addresses are not published at all: every one of the 32
  public manifests carries a funding block, and none of them lists an
  address (live read below).

### Live registry census (2026-11-11)

Read from `GET https://slop.cash/api/v1/projects` on 2026-11-11:

| Measure | Count |
|---|---|
| Projects in the public registry | 32 (18 active, 14 paused) |
| Projects with an escrow block | 10 |
| Projects with a registered ordinary vault deployment | 5 |
| Registered deployments by network | solana-mainnet 3, base-mainnet 1, robinhood-mainnet 1 |
| Projects with a registered bounty settlement deployment | 0 |
| Projects publishing a funding address | 0 of 32 |
| Projects with registry payments disabled | 32 of 32 |

The five registered ordinary deployments belong to eliza
(solana-mainnet), hyperliquid-source (solana-mainnet), pumpfun-source
(solana-mainnet), slopdotcash (base-mainnet), and thenetwork
(robinhood-mainnet). The restrictions list in the same response was
empty. Registry payment mode is a platform gate separate from the
vault's own monthly setting described above. The public totals route
returned a current snapshot row for slopdotcash (finalized Base block
56034409, block time 2026-11-11T11:40:57Z, observed
2026-11-11T11:55:59Z); the amounts in that row are payout data and are
analyzed in the payouts packet, not here.

## Verification

- Pinned the upstream commit:
  `git ls-remote https://github.com/SlopDotCash/slopdotcash.git refs/heads/development`
  returned `ced75d782d5836f60d84f46d50604f75a5852438`; every file and
  line cited above was read at that commit.
- Read the setup route end to end (`ownerVault` and
  `ownerBountySolanaFunding` in `backend/projects/handler.ts`), the
  setup service (`backend/projects/vault-setup.ts`), the EVM creation
  verifier (`contracts/evm/adapter.ts`), and the "Owner vault setup"
  section of `backend/projects/README.md` (lines 445-490), and
  cross-checked each documented rule against the code path that
  enforces it (error code and line).
- Re-ran the census with one public read and `jq` filters over
  `.projects[].escrow.deployments`, `.projects[].securityBounty`,
  `.projects[].funding.addresses`, and `.projects[].status`; the
  counts in the table are the outputs of those filters.
- Read one public totals response
  (`GET https://slop.cash/api/v1/payments/projects/slopdotcash/vault`)
  and confirmed the snapshot shape matches
  `contracts/vault-totals.ts` and the documented staleness bound
  (`staleAfterMs` 1800000).
- This repository's checks: pytest is not installed in this
  environment, so the existing test file's four test functions were
  executed directly — 4/4 pass — and the packet's heading and table
  were checked against the markdown rules in
  `.github/workflows/pr-checks.yml`.

## Notes

- Boundaries with neighbouring packets: payout paths, balances, and
  payment history are issue #3 (PR #32); the contract-level gross,
  net, and fee arithmetic of an EVM withdrawal is PR #46; vault
  snapshot refresh ordering is PR #33; the EVM monthly commitment
  window is PR #40. This packet cites those results rather than
  repeating them and covers only the setup, registration-verification,
  and withdrawal rules of issue #8.
- Per-award commitments (`src/OwnerCommitment.tsx`) are mentioned only
  where the monthly-settings authority split touches them; the
  commitment flow itself belongs to the cycles and contracts areas.
- Not verified here: no vault was created, registered, or withdrawn
  from — the study is read-only against the public codebase and public
  API, and no wallet was connected or signed anything. Whether the
  five registered deployments are the complete historical set cannot
  be told from the public registry alone; the census is the current
  registry state at the read time above.
- The issue lists `src/OwnerBountyVault.tsx`; its flow is the bounty
  branch of the same setup route documented above (saved USDC terms,
  monthly setting forced off, 25% bounty fee), enforced in
  `backend/projects/vault-setup.ts` and `handler.ts` as cited.
