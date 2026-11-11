# Solana expiry recovery — an expired signed send settles at zero cost only on two independent retained block histories (Issue #3)

## Target

The Solana expiry recovery for the native gas journal in the SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the schema change in migration
`migrations/0095_fee_solana_expiry.sql`; the expiry resolution in
`workers/fee-converter/native-gas.ts`; the expiry proof builder in
`workers/fee-converter/solana-expiry.ts`; the recovery call site in
`workers/fee-converter/solana.ts`; the fee-converter README section on
expiry; the formal model in `formal/models/fees/solana_expiry.qnt`; and
the tests in `workers/fee-converter/native-gas.test.ts`. The Solana
reservation and signed commit this recovery settles are covered in
separate packets (migrations 0092 and 0094); this packet covers only
what 0095 adds for expiry.

## Claim

A signed Solana fee send whose blockhash expired without landing can
be released from the native gas journal, settling at zero cost, only
when two independent RPC providers each prove with a retained,
complete, finalized block history that the transaction never landed —
and the database re-checks that proof, the live lease, and the signed
row's blockhash anchor before the settlement commits.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The anchor: the reservation pins the slot of its blockhash

Migration 0095 adds one column to the gas journal, the Solana
blockhash slot, with a trigger that refuses any later change to it,
so the anchor is immutable once recorded. The reservation code
records that slot with the reservation: it is the slot of the
blockhash inside the signed message, the point from which the
transaction's validity window is measured. A reservation made before
this migration carries no anchor, and, as shown below, no expiry
proof can ever settle it.

### 2. Why expiry needs a proof, not a missing receipt

A Solana blockhash is only valid for a bounded window, so a signed
send can expire unlanded while its reservation keeps holding the full
lamport ceiling in the journal. The recovery path therefore has to
distinguish "never landed" from "not seen yet". The worker code is
explicit that a missing transaction alone never releases gas: when the
finalized lookup returns nothing, the send is only a candidate for
expiry, and the reservation stays held unless a full proof is built
and stored. Pruned history, an unknown RPC operator, or a single
provider's word all keep the hold.

### 3. The proof builder: two independent providers, full history each

The proof builder takes the transaction id, its blockhash, and its
blockhash slot, and requires exactly two providers with different
known operators. The known operators are the Solana public service,
PublicNode, Alchemy, and Helius, recognised from the endpoint host;
anything else is unknown and the proof is refused. The default
secondary endpoint is the Allnodes PublicNode service, and a
custodian may point it at another independently operated endpoint,
with an explicit warning not to disguise aliases of one operator as
independent services.

Each provider must pass the same sequence of checks at finalized
commitment: it must report the expected mainnet genesis hash; its
first available block must be at or before the anchor slot, so its
history reaches back far enough; the block at the anchor slot must
carry the signed blockhash; the blockhash must report as invalid at
finalized commitment; the signature status lookup with history search
must return exactly one null entry; and a direct transaction lookup
must return nothing. Only then does the builder walk the chain: it
takes a fixed horizon from the expiry context (or from a retained
earlier scan), fetches each finalized block with its full signature
list, checks that every parent slot and blockhash links to the next,
and confirms no block contains the signed transaction. Each run
processes at most thirty-two blocks per provider and persists its
cursor and page evidence, so a restart resumes the same fixed
horizon instead of starting over. Both completed scans must agree on
the common horizon, the block count, and the cumulative block and
signature digest; a disagreement keeps the reservation even when
neither scan lists the target transaction.

### 4. The retained scans: immutable pages under a strict revision chain

The migration stores the scan evidence in two tables. One holds the
latest retained coverage per transaction and operator; the other
holds every immutable scan step, with a revision that must advance
by exactly one from the previous revision, starting at zero. A step
is accepted only while the matching signed Solana row is still
unsettled and its run's lease is live, and the retained coverage
advances only when the step's prior revision matches the stored
revision, so two writers cannot silently fork the evidence. Steps
cannot be updated or deleted, and neither can the retained scans be
rewritten except through a chained step. The worker's coverage store
reads and writes through exactly these tables, so the code and the
schema agree on what "retained" means.

### 5. The proof gate: the database re-checks everything before settling

The proof itself is one immutable row naming the transaction, the
fee wallet, the run, the full proof document, its SHA-256 digest, and
the observation time. A before-insert trigger refuses the proof
unless it carries exactly two providers with different operators,
its transaction id matches the row, both providers' coverages agree
on tip slot, tip hash, block count, and digest, and — the decisive
check — both coverages match a retained complete scan byte for byte,
with the same blockhash and blockhash slot as the proof. A single
provider, two aliases of one operator, disagreeing histories, or a
proof built from scans that were never retained are all refused with
the same coverage error.

If the gate passes, an after-insert trigger settles the signed row in
the same commit: the actual cost becomes zero, the settlement day is
taken from the observation time, and the receipt records the proof
digest prefixed as an expiry receipt. The settlement applies only to
a signed Solana row for that transaction and wallet whose cost is
still unset and whose blockhash slot is set, and only while the run's
network lease is still live at the observation time. If exactly one
row is not updated, the whole proof insert aborts and no proof row
exists. The worker repeats the same checks in code before inserting
— two providers, distinct operators, the anchor slot matching the
reservation, retained coverage complete and identical to the proof,
and both coverages in agreement — so a proof that fails in code
never reaches the database gate.

### 6. What stays held

Three cases keep the reservation held, each verified in the replay
below. A proof naming a run with no live lease is refused, so an
expired lease cannot release gas. A signed row with no blockhash
anchor — a reservation made before this migration — passes the
coverage gate but matches no row in the settlement update, so the
proof is refused and the row stays unsettled. And any disagreement
between the two providers' completed histories keeps the hold even
when neither lists the target. The proof row, the scan steps, and the
blockhash anchor are all immutable and permanent once stored, and a
settled expiry row cannot have its zero cost rewritten afterwards.
The formal model for this mechanism states the same invariant in
miniature: a release implies the hold is zero, the history is
complete, and both observations report the transaction as expired
and absent — and its negative tests show that a missing history or a
disagreeing observation cannot release.

### 7. The boundary: two observations, not a cryptographic proof

The README states the limit plainly: this policy trusts two
independent RPC history observations; it is not a cryptographic
proof of absence. After a successful expiry settlement, the claim or
swap is marked failed before any later attempt, and the original
signed bytes remain unchanged. The account-proof column the worker's
reservation insert also writes arrives only in the next migration,
0096, so the end-to-end reservation path still needs that migration
after this one.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0095 applied verbatim, in
order, with zero failures, and the foreign-key check came back
empty. At 0094 the expiry tables did not exist and a reservation
insert naming the blockhash-slot column was refused for want of the
column. After 0095 the three expiry tables existed, a reserved
Solana row carrying blockhash slot 100 stored and moved the Solana
lease revision from zero to one, while an insert naming the
account-proof column was still refused, confirming that column
arrives only in 0096. A Solana conversion with a null EVM nonce
flipped the reservation to signed, confirming the 0094 commit still
works at 0095. A proof with no retained scans was refused; a scan
step for an unknown transaction and a step with a skipped revision
were each refused; then scan steps retained coverage for both
providers, including a chained revision advance for the second
operator. A one-provider proof, a same-operator-twice proof, a
proof with disagreeing tip slots, and a proof with the wrong
blockhash slot were each refused. The valid two-provider proof was
accepted and settled the signed row at zero cost with the settlement
day from the observation time and an expiry receipt carrying the
proof digest. Updating or deleting the proof, changing the blockhash
anchor, and changing the settled zero cost were each refused. A
second signed row with retained scans but a proof naming a run with
no lease was refused and stayed unsettled; a third signed row with
no blockhash anchor, again with retained scans and a well-formed
proof, was refused and stayed unsettled. The replay script is kept
with the run's working state and re-runs the whole check from the
public sources.

## Notes

The Solana native gas journal (migration 0094) and the EVM gas
journal (migration 0092) are separate mechanisms from this expiry
recovery, as is the Solana account proof in migration 0096. The
fee-converter README records that live Solana conversion is
conditionally approved but its activation is deferred while owner
vault setup is elsewhere, so this packet verifies the prepared
expiry rules, not a live Solana expiry. Whether any gas row has ever
been released by an expiry proof on a live network cannot be checked
from public sources — the journal lives in the operator's database,
not on chain.
