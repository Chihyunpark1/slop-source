# Native gas journal — EVM fee sends reserve exact wei under the network lease (Issue #3)

## Target

The native gas journal in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the journal shape created by migration
`migrations/0092_fee_native_gas.sql`; the reservation, commit,
settlement, and recovery rules in
`workers/fee-converter/native-gas.ts`; the exact daily-liability
accounting in `workers/fee-converter/verified-native-liability.ts`;
and the gas rules documented in `workers/fee-converter/README.md`
(the native-gas section). The migration header states the rule
plainly: gas liabilities are separate from token conversion limits.

## Claim

Native gas is journaled separately from token conversion value:
before a fee send is signed the worker reserves an exact wei ceiling
under the network lease, and the signed send's own insert atomically
commits that reservation, so no broadcast can happen without a
reserved gas budget and no reservation can be double-spent, silently
rewritten, or released without a receipt.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema keeps gas liabilities in their own table

Migration 0092 creates a `fee_native_gas` table that is EVM-only:
its network check admits Base, Ethereum, and Robinhood Chain, and a
Solana row is refused. Each row pins one reservation to a wallet, a
nonce, an intent hash, and a run id, with three wei ceilings stored
as exact decimal text — the maximum for this send, the
per-transaction limit, and the per-day limit — so amounts stay exact
past JavaScript's safe integer range and no float or SQL sum of wei
ever enters the accounting. The row's state is one of reserved,
signed, or abandoned. Three checks hold the shape together: a row is
signed exactly when it carries a transaction id, an actual cost is
present exactly when a settlement day is present, and every wei
field must be decimal digits only. One transaction id is allowed
per network. The migration also adds a `gas_revision` counter to the
network lease row, which ticks up on every insert and update of a
gas row, and adds a `native_gas_id` column to both the conversion
journal and the replacement journal, so each signed send can point
at the reservation it committed. The same permanence rules guard
every row: identity and binding fields can never change, a signed
row cannot move state, settled cost and receipt evidence cannot be
rewritten once set, and no row can be deleted.

### 2. A reservation is made under a live lease and a revision fence

Before signing, the worker reserves gas through the journal's
reserve step. The reservation is inserted only under a live network
lease, and only if the lease row's revision still equals the value
read at the start of the reservation — a concurrent reservation
that moved the revision first makes this one fail, so two runs
cannot overspend the same budget. The reserved maximum must be
above zero and within the per-transaction limit, and the daily
budget must cover one positive transaction limit plus its
additional fees, or the limits themselves are rejected at
construction. The daily liability is computed exactly: today's
settled costs, plus one largest unresolved maximum per wallet and
nonce group. A failed swap's group, a replacement's group, and an
unknown send's group each count once at their largest ceiling,
never once per attempt. If the computed liability would pass the
per-day limit, the reservation is refused and unknown sends stay
reserved. A reservation that loses its lease or its revision
fails outright and is retried on a later run, never forced through.

### 3. Same-nonce sends share one liability, and failed swaps keep theirs

A replacement does not get a fresh budget: its reservation is
allowed only when the same nonce already holds a signed, unresolved
send for that transaction, and no other row at that nonce is still
reserved or already settled. A swap that closes as failed while its
nonce is still unused — for example one dropped after its router
deadline — keeps its reserve, and the next send takes that nonce
and joins the same group, so the nonce still reserves its largest
maximum once until a receipt settles it. Unknown sends carry their
liability across UTC midnight, and committed attempts are never
released merely because a swap expired, an RPC failed, or a
business row says failed. A legacy approval hash without signed
bytes still holds its nonce. If a nonce advanced and another send
consumed it, but no receipt proves which send won, the reserve
remains: no release path is implemented for that case.

### 4. The signed send's insert commits its reservation atomically

Inserting a conversion row that names a gas reservation flips the
matching reserved row to signed, stamps it with the transaction id
and the conversion id, and does it in the same statement as the
journal insert. The flip happens only when every binding matches —
same network, same fee wallet, same nonce, same run id, signed
bytes present — and only while the network lease is still live at
the submission time; if exactly one row is not updated, the whole
insert aborts and no conversion row exists. The same rule governs
replacements: inserting a replacement row that names a gas
reservation commits it only when the nonce and network match, the
lease for that reservation's run is live at the replacement's
creation time, and a conversion with the same fee wallet exists.
Broadcast happens only after this commit and a fresh lease check,
so a send can never reach the chain without a committed gas
reservation behind it, and a stale holder can never commit a
reservation that no longer belongs to its run.

### 5. Settlement records the exact cost on the day finality was observed

When a receipt arrives, the settlement step writes the exact
execution cost, the UTC day on which finality was observed, and the
receipt's block hash onto the signed row. The cost is the exact
execution cost plus Base data and operator fees, and a late receipt
does not erase today's liability — the settled day is the day
finality was observed, not the day the transaction was sent. A
finalized cost above the reserved maximum holds further signing.
Missing cost evidence keeps the reserve. When a receipt settles one
send at a nonce, sibling signed rows at the same nonce settle at
zero in the same update, because only one transaction can consume
a nonce. The settlement update itself requires a live lease and a
matching signed row, and fails outright if either is missing. The
only way a reservation leaves the journal without a receipt is
abandonment, and only a successor run may retire an uncommitted
reservation from a different run — because such a reservation
cannot have reached broadcast — while a signed row can never be
abandoned.

### 6. Historical sends are imported as liabilities too

Sends journaled before this table existed are not forgotten. The
worker scans for live conversions, replacements, and approval
hashes that have no gas row, and imports each one as a signed row
under a live lease, with its recorded nonce and a supplied maximum.
A historical approval hash without bytes still counts, because its
nonce is still held. This is why the journal can claim to bound
gas at all: every signed byte the worker ever produced is either
covered by a reservation or imported as a liability, and the daily
accounting folds those imports into the same per-wallet, per-nonce
groups as fresh reservations.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0092 applied verbatim, in
order, with zero failures, and the foreign-key check came back
empty. A network lease was planted with its revision at zero. A
valid reserved row stored, and the insert trigger moved the
revision to one. A signed row without a transaction id, a maximum
of ten point five wei, a hexadecimal maximum, a Solana row, and a
negative nonce were each refused by their own check. Inserting a
conversion that named the reserved row flipped it to signed with
the transaction id and conversion id, and the revision moved again.
A conversion naming a reservation from a run with no live lease
was refused with the reservation-lost error, left no conversion
row, and left the reservation reserved. A replacement naming a
reserved row committed it to signed with the conversion id, while
a replacement naming the wrong nonce was refused the same way.
A second signed row with the same transaction id on the same
network was refused by the unique index. Setting an actual cost
without a settlement day, and a settlement day without a cost,
were each refused; a full settlement stored, and afterwards the
cost and the receipt block hash could not be changed. Settling
one of two signed rows at the same nonce wrote the receipt cost
to the matching row and zero to its sibling. Changing a signed
row's maximum, moving a signed row to abandoned, and deleting a
signed row were each refused as immutable or permanent, while
abandoning a reserved row was allowed. The replay script is kept
with the run's working state and re-runs the whole check from the
public sources.

## Notes

Migration 0094 adds Solana columns to this same table, a separate
mechanism not covered here. Whether any gas row has ever been
reserved on a live network cannot be checked from public sources —
the journal lives in the operator's database, not on chain — so
this packet verifies the rules and the guards, not a live
reservation. The replacement journal (migration 0087) and the
approval journal (migration 0088) share the same conversion
journal and lease but are separate mechanisms.
