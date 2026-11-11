# Fee approval journal — a bounded ERC-20 approval is a separate immutable send (Issue #3)

## Target

The fee approval journal in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the journal shape created by migration
`migrations/0088_fee_approval_journal.sql`; the approval rules
documented in `workers/fee-converter/README.md` (the approval-before-swap
section and the pre-signing checks); the approval preparation and
receipt checks in `workers/fee-converter/evm.ts` (the bounded-approval
check, the approval signing call site, the finalized-approval check,
and the replacement function); the journal insert and the legacy-hash
handling in `workers/fee-converter/core.ts` (the one-row-per-intent
insert, the reconcile path for hash-only rows, and the nonce floor);
and the open-row query in `workers/fee-converter/store.ts`.

## Claim

A bounded ERC-20 approval is a separate immutable send in the fee
journal — an exact finite amount granted to the pinned router, never
unlimited — that never counts as a conversion or a fee receipt and
never consumes the conversion value caps, while sharing the
pending-token guard and the bounded same-nonce replacement path with
swaps and carrying no swap deadline; older rows that hold only an
approval hash are retained unchanged.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema keeps approvals as their own kind of journal row

Migration 0088 rebuilds the `fee_conversions` table and adds a third
kind, `approval`, beside `conversion` and `claim`. An approval row is
pinned down by three checks: its approval transaction id must equal
its own transaction id, its route must be KyberSwap, and its output
amount must be null or zero — an approval moves no funds, so it can
never record a received amount. Approvals are EVM-only: a Solana row
cannot be an approval, because Solana has no ERC-20 approval step.
A submitted, unknown, or finalized row must carry its transaction id,
its signed bytes, and its submission time; an approval is exempt from
the two fields a swap needs, the router deadline and the signed
minimum output, because an approval has neither. The table is rebuilt
by copying every existing row into the new shape and then dropping the
old table, and the migration header states the intent plainly: retain
every older row, including unresolved legacy approval hashes. The
same triggers that guard conversions guard approvals: a settled row
cannot be updated, identity fields cannot change, and no row can be
deleted.

### 2. An approval is prepared only when the allowance is short, and only for the exact amount

Before a swap is signed, the worker reads the fee wallet's on-chain
allowance for the token at the pinned router. If the allowance already
covers the order amount, no approval is signed at all; ETH needs no
approval either. Only when the allowance falls short does the worker
sign an approval, and the calldata grants exactly the order amount to
the pinned router — never an unlimited allowance. The worker verifies
its own bytes with a bounded-approval check: zero value, the approve
function, the pinned router as spender, and the amount exactly equal
to the recorded order amount. The prepared send records the approval
kind, the transaction hash as both its own id and its approval id, the
signed bytes, the nonce, no deadline, and a zero minimum output. The
key signs only this exact approval, the checked swap, the fee claim,
and same-nonce replacements of those sends.

### 3. The approval is journaled before broadcast and never consumes the value caps

The core module inserts one row per signed intent: an approval gets
its own row with kind `approval` in the submitted state, and its
signed minimum output is stored as null, because an approval promises
no output. Approval bytes are never overwritten by a later swap. The
insert skips the conversion value-cap accounting for approvals — the
cap is committed only for non-approval rows — so an approval does not
consume any of the budget the later swap must fit inside. The
pending-token guard is shared: at most one unresolved send per wallet
token, so while an approval is submitted or unknown, no second intent
for that token can be journaled. A restart reuses the journaled
approval bytes instead of signing another approval.

### 4. Only a canonical finalized receipt closes an approval, and the allowance must match exactly

Reconciliation treats an approval like any other send until the
receipt arrives: the receipt must be canonical and finalized, and the
transaction must be from the fee wallet, to the token contract, at the
recorded nonce, in the exact recorded block, and its calldata must
pass the bounded-approval check. A reverted approval closes as failed
with an approval-specific reason. On success the worker reads the
allowance again at the receipt block, and it must equal the recorded
order amount exactly — a finalized approval with a different allowance
is an error, not a success. A finalized approval closes with an output
amount of zero. Only then may a later run prepare a fresh swap, and
the swap still has to pass its own value caps. The fee-converter test
suite covers both halves of this: an approval is journaled before an
ambiguous broadcast and excluded from conversion totals, and a
canonical approval permits a fresh later swap without counting the
approval value.

### 5. Approvals share the replacement path, but have no deadline

Approvals share the bounded same-nonce replacement path created by
migration 0087: if an approval stays unmined, a replacement re-signs
the same approval at the same nonce with higher fees in bounded
steps, journaled before broadcast. The replacement function sends the
approval back to the token contract (not the router), re-checks the
bounded-approval condition on the original bytes, and skips the
router-deadline margin that would block a swap replacement — an
approval has no deadline to run past. The nonce floor counts every
open journaled send, including legacy approval hashes, so a new send
never takes a nonce at or below an open approval's nonce.

### 6. Legacy approval hashes are retained and never worked around

Older versions of the worker kept only the approval hash on a row,
without the signed bytes. Those rows are kept with their original
state and history: the store's open-row query returns them alongside
live sends, the nonce floor reserves their recorded nonce, and
reconciliation treats a hash-only row as an approval with no deadline
and asks the chain for its status. Missing bytes or an uncertain
receipt never authorize a new approval or a replacement, and no raw
bytes are fabricated for those rows — the row holds the token and
nonce until the exact approval can be verified.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0088 applied verbatim, in order,
with zero failures, and the foreign-key check came back empty. Two
legacy rows were planted before applying migration 0088 — a finalized
conversion carrying an approval hash beside its own swap, and a
failed hash-only row — and both survived the rebuild with their
approval hashes intact. A valid approval row (approval id equal to
transaction id, KyberSwap route, zero output, no deadline, no minimum
output) stored exactly one row; an approval with a nonzero output
amount, one whose approval id differed from its transaction id, one
on the Jupiter route, and one on Solana were each refused by their
own check. While the approval was open, a second intent for the same
network and token was refused by the pending-token unique index,
while an approval for a different token stored fine. Updating an
approval's amount or kind was refused as immutable, and deleting it
as permanent. Finalizing the approval with a zero output succeeded,
and afterwards a new send for the same token stored fine, because
the guard covers only submitted and unknown rows. The replay script
is kept with the run's working state and re-runs the whole check
from the public sources.

## Notes

Migration 0089 adds a read-only referral claim cache, a separate
mechanism not covered here. Whether any approval has ever been
journaled on a live network cannot be checked from public sources —
the journal lives in the operator's database, not on chain — so this
packet verifies the rules and the guards, not a live approval. The
fee-claim journal (migration 0082) and the replacement journal
(migration 0087) share this same journal and replacement path but are
separate mechanisms.
