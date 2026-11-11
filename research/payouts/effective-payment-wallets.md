# Effective payment wallets — registration never displaces an authorized wallet (Issue #3)

## Target

The payout destination rule in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the derived view in migration
`migrations/0100_effective_payment_wallets.sql`; the wallet-claim
lineage it reads, in migrations `0001_private_trace_backend.sql`
(rebuilt in `0003_wallet_claim_registry.sql`, chain column in
`0010_wallet_claim_chain.sql`); the authorization table in
`0011_payments.sql`; the challenge and authorize flow in
`backend/payments/README.md`; and the readers that pay against the
view in `backend/payments/dispatch.ts`, `backend/payments/handler.ts`,
`backend/payments/ledger.ts`, and
`workers/payment-executor/core.ts`. Adjacent, not duplicate:
mapmapdown's #36 documents the registration lineage itself (how a
claim chain is built); #97 documents the monthly payment authorization
(the signed execution input), a different table; #32 maps the three
payout paths and mentions wallets only in passing. This packet is
only about which claim counts as the live payout destination.

## Claim

A contributor's effective payout wallet is derived, never stored:
it is the last authorized claim on that actor's chain, and an
unsigned registration — however new — never displaces it; only the
pending leaf is exposed, and only before the first authorization on
that chain.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The two inputs: an immutable claim lineage and an immutable authorization

A wallet claim is one row per registered address, carrying the
contributor's GitHub actor id and login, the wallet address, the
source (a GitHub issue, a profile readme, or the authenticated
registry), a digest of the source body, an observation time, a unique
record digest, and the id of the claim it supersedes, if any. The
table is append-only: triggers refuse every update and every delete.
One root per actor per chain, and one successor per claim, are
enforced by unique indexes, so each actor holds exactly one lineage
per settlement network and that lineage has exactly one tip; forks
fail at the database boundary. A successor must stay on its
predecessor's chain and actor, so a Base claim can never retire a
Solana address or the reverse.

Authorization is a separate table with one row per claim, keyed by
the claim id and bound to a single-use challenge and a signature.
The payments README describes the flow: a challenge endpoint returns
a 15-minute message, the contributor signs that exact message, and
the authorize endpoint stores the signature. The authorization table
is immutable too — its trigger refuses every update. There is no
column on either table that names a "current" wallet; currentness is
derived.

### 2. The view: two branches, one recursive search, no stored state

Migration 0100 holds a single statement, a view that returns the
full claim row for whichever claim is effective. Its header states
the policy: registration records intent, only wallet authorization
replaces an active payout destination, and the view derives state
from the original immutable claims and authorizations, storing no
second wallet inventory.

The first branch covers the authorized case. A claim is effective
when it has an authorization row for the same actor, and no
authorized successor exists anywhere below it. "Below" is a
recursive walk: starting from the claim's direct successors on the
same actor and chain, the search follows each supersedes link down
to the tip of the lineage, and the claim is excluded if any row on
that walk carries an authorization. So authorizing the tip retires
every earlier authorized claim at once, while authorizing a middle
claim leaves it effective only until a descendant is authorized.

The second branch covers the time before any authorization. A claim
is effective when no authorized claim exists at all for that actor
on that chain, and the claim itself has no successor — that is, it
is the tip of the lineage. The pending leaf is therefore exposed
only before the first authorization. Once any claim on the chain is
authorized, the second branch goes silent for every claim, and the
first branch alone decides.

Because the view is a derivation, at most one claim per actor per
chain can be effective at any time, and the answer changes the
moment an authorization row is inserted, with no other write.

### 3. What the readers do with it

Every payout path resolves the destination through the view joined
to the authorization table, never through the raw claims table. The
dispatch path joins the reserved obligation to the effective claim
for the same actor and chain and reads the claim id, the record
digest, and the wallet address as the payment destination. The
outbox path does the same when marking obligations ready, the ledger
does it when enqueueing reserved obligations, and the payment
executor does it when building the signed send, including the
challenge id, expiry, message, and signature of the effective
claim's authorization.

The direct-payments and vault-setup readers add one more condition:
they accept only effective claims whose source is the authenticated
registry, so an issue- or readme-observed address can never be a
payout destination even if it is the effective claim.

The effective wallet is resolved when a dispatch starts, and a late
replacement does not redirect a payment already in flight. The
dispatch test suite exercises exactly this: a dispatch begins
against the original authorized claim, a successor is then
registered and authorized — the view immediately returns the
successor — but the in-flight dispatch still completes against the
original claim, and the recorded payment attempt carries the
original claim id. The replacement applies to the next dispatch,
not the one already running.

### 4. The policy behind it

The payments README records that the repository owner approved this
replacement and recovery policy directly in the 27 October 2026
review, and states it in one line: registration alone never
displaces an authorized wallet. The view keeps the last authorized
claim active through any unsigned successors, and exposes the pending
leaf only before the first authorization. The README also notes that
migration 0100 must be applied before the readers that depend on
the view are deployed, and that challenges and registration still
use the raw claim leaf — the view is a payout-time derivation, not
a registration rule.

## Verification

Replaying migrations 0001 through 0100 verbatim in a scratch
SQLite database (128 files, 0 failures, foreign-key check empty):
the view does not exist at 0099, and 0100 holds exactly one
statement, the view definition. Seeded claims and authorizations
then confirmed every branch of the rule:

- A registered but unauthorized Solana claim is the effective row:
  the pending leaf is exposed before the first authorization.
- Registering an unsigned successor moves the exposed leaf forward
  to the successor; the superseded claim drops out.
- Authorizing the successor makes it effective, and registering a
  further unsigned successor leaves the authorized claim effective
  — registration alone never displaces it.
- Authorizing that successor replaces the active destination, and
  authorizing the tip of a five-claim chain retires every earlier
  authorized claim at once, through the recursive successor search.
- A Base lineage is independent: its pending leaf is exposed while
  the Solana lineage keeps its authorized claim, and a second actor
  is independent of the first.
- The view returns the full claim row (id, address, chain, and the
  claim it supersedes), and at most one effective claim exists per
  actor per chain.
- The earlier guards still hold at 0100: a fork (a second successor
  of the same claim), a cross-chain successor, and a second root on
  the same chain are each refused; claim updates and deletes are
  refused as immutable and permanent; authorization updates are
  refused as immutable.

The dispatch suite's late-replacement case (`backend/payments/
dispatch.test.ts`) independently confirms the in-flight behavior:
after the successor is authorized the view returns the successor,
yet the running dispatch pays the original claim.

Open unknowns: none in the derivation itself. Whether any
production actor currently has an unsigned successor sitting above
an authorized claim — the state the view is designed to absorb —
is not visible from the public codebase and is not claimed here.
