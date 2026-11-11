# Fee send replacements — a stuck EVM fee send is re-signed at the same nonce with a bounded higher fee (Issue #3)

## Target

The same-nonce fee replacement mechanism for EVM fee sends in the
SLOPCASH codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue
#3 (Payouts & bounties): the replacement journal created by migration
`migrations/0087_fee_send_replacements.sql`; the replacement policy and
its worked rules documented in `workers/fee-converter/README.md` (the
same-nonce fee replacement section); the signing gate in
`workers/fee-converter/core.ts` (the replacement function and the
three-minute wait constant); the fee step and cap in
`workers/fee-converter/evm.ts` (the replacement policy comment and the
replacement call site); the shared step function in
`workers/verified-fee-replacement.ts`; the journal append in
`workers/fee-converter/store.ts` (the replacement insert); and the
formal model in `formal/lemmascript/workers/verified-fee-replacement.dfy`.

## Claim

When a signed EVM fee send stays unmined because the network fee rose
above its signed maximum, the fee-converter worker re-signs it with the
same nonce, recipient, calldata, and value and a higher fee in bounded
steps — at most five replacements, each raising both fee fields by 25
percent and never above three times the original — and journals each
replacement in a permanent table before broadcasting it, so exactly one
attempt can ever land and the original send is never altered.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. Each replacement is a permanent journal row beside the unchanged original

Migration 0087 creates `fee_send_replacements` with one row per
replacement: the fee conversion it belongs to, the network, the attempt
number, the nonce, the transaction hash, the signed bytes, and both fee
fields as exact decimal wei strings. Attempt 1 is the first
replacement; the original send is attempt 0 and lives in
`fee_conversions`, which the migration does not touch except to add a
`landed_tx_id` column recording which transaction — the original or one
of its replacements — finally landed. There is deliberately no foreign
key from a replacement to its conversion: later migrations rebuild
`fee_conversions` by dropping it, which a foreign key would refuse once
rows exist. Uniqueness is enforced twice: one replacement per
conversion and attempt number, and one transaction hash per network.
An update of a stored replacement is refused as permanent and a delete
as permanent. The network is restricted to the three EVM networks
(base, ethereum, robinhood); Solana has no same-nonce replacement,
because its sends expire by blockhash instead. The attempt number is
bounded between 1 and 32 in the schema, but the fee arithmetic below
caps a send at five replacements in practice.

### 2. A replacement is signed only when every gate passes

The replacement policy is an owner decision of 25 October 2026, and
the worker signs a replacement only when all of these are true. The
mode must be live and the network must hold a fee-wallet key; a dry run
reconciles but signs nothing. The send must not be mined — a mined send
waiting for finality is not replaced. The latest attempt, the original
or the last replacement, must have been journaled at least three
minutes ago; the wait constant in the core module is three times sixty
thousand milliseconds. The latest block base fee must be above the
signed maximum fee per gas of the latest attempt, so a clipped or lower
suggested priority fee alone never triggers a replacement. The new fees
must fit the step and the cap: each step raises the maximum fee per gas
and the maximum priority fee per gas by 25 percent, rounded up, neither
field may go above three times the original send's value, and every
step must raise both fields by at least 10 percent — the minimum nodes
accept for an EIP-1559 replacement. When the cap does not allow a
10-percent raise, the cap is reached and the send waits. With a 25
percent step against a three-times cap, a send can have at most five
replacements: the fifth step reaches the cap, and a sixth cannot raise
either field by 10 percent inside it. The worst-case fee — the original
gas limit at the new maximum fee, plus on Base the L1 data fee of the
replacement bytes from the GasPriceOracle — priced in USDC and
multiplied by the configured gas multiple, must not exceed the recorded
USDC value of the send, the same approved gas-cost threshold the
original send passed. A claim row recorded before this change has no
value, so it is not replaced. A claim also has its reviewed deployment
verified again, as for a rebroadcast; an approval must match its token,
pinned router, and finite original amount; and a swap must have its
router deadline more than two minutes away. If any gate fails, the send
waits, the run logs a waiting event with the reason — for example the
replacement cap being reached — and the row stays submitted or unknown
with the token blocked until the send is reconciled.

### 3. Only the two fee fields change

A replacement copies the recipient, calldata, value, gas limit, access
list, and nonce from the original signed bytes; only the maximum fee per
gas and the maximum priority fee per gas change. The worker does not
quote a swap again under the same nonce, so the replacement keeps the
signed calldata and therefore the router deadline of twenty minutes
after signing. After that deadline a same-nonce replacement would
revert, and the code has no zero-value self-cancel transaction: a swap
within two minutes of its deadline is not replaced but waits, and if it
is mined later it reverts and the row closes as failed, or if the node
drops it after the deadline the row also closes as failed, after which a
later run quotes and signs a new swap for the token. The token balance
stays in the fee wallet during the wait.

### 4. The replacement is journaled before it is broadcast, under a live lease

The core module signs one replacement at a time and journals it before
broadcasting: after a restart the next run finds the journaled attempt
and rebroadcasts its bytes instead of signing another one. The store's
insert is a single guarded statement that writes the row only when the
run still holds a live lease for the network, the original conversion
is still open in live mode in the submitted or unknown state with the
same network and nonce, and the attempt number is exactly one more than
the highest stored attempt for that conversion. A lost lease stops the
run, and bytes already journaled remain available to its successor. A
restart tries those bytes first even when the three-minute wait has
elapsed; only if the node explicitly refuses them because their maximum
fee is below its base fee may the run sign the next bounded step, and a
transport error or any other uncertain response keeps the same bytes
and leaves the row unknown. The wait, the step, and the cap all come
from the journal, so repeated runs cannot pass the cap. Claims,
approvals, swaps, and replacements all recheck the current network
lease before signing and broadcast, and the durable insert requires
that same live lease.

### 5. Reconciliation decides one outcome, and the nonce floor stops rival sends

The original and every replacement share one nonce, so at most one can
be included. Reconciliation checks the receipt of each hash, and the
included transaction decides the one outcome of the row, with the same
claim and swap receipt checks as before; `landed_tx_id` records which
transaction landed, and a claim or conversion is counted once,
whichever attempt lands. A final outcome requires the requested
transaction hash in its exact canonical block position, at or below the
finalized block; missing or mismatched block evidence leaves the send
open, including reverted attempts. A new claim, approval, or swap never
takes a nonce at or below the nonce of an open journaled send on that
network, and a legacy approval hash also reserves its recorded nonce:
without this floor, a node that drops a stuck send and reports its
nonce as free could let a new send for another token take that nonce,
and the two sends would outbid each other through their replacements.
The new send is refused before it is signed, the refused conversion
closes as failed with the reason, and a later run tries again. The
formal model states the same fee bounds as the code: the shared step
function returns fees no higher than three times the original, no lower
than 110 percent of the latest attempt, and below 125 percent of the
latest attempt.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0087 applied verbatim, in order,
with zero failures, and the foreign-key check came back empty. On a
live submitted base conversion at nonce 7 with a live lease, running
the store's replacement-insert statement verbatim stored exactly one
replacement at attempt 1 with fees raised 25 percent; offering attempt
1 again wrote zero rows, and attempt 2 stored a second row. A direct
insert repeating attempt 2 was refused by the unique constraint on
conversion and attempt; attempts 0 and 33 were refused by the attempt
check; a 65-character transaction hash was refused by the length
check; a Solana replacement was refused by the network check; and a
non-decimal fee string was refused by the decimal check. An update of a
stored replacement was refused as permanent and a delete as permanent.
Setting `landed_tx_id` on the conversion to the second replacement's
hash succeeded, and a 31-character value was refused by its length
check. The store insert with a lease for a different run wrote zero
rows, and against a finalized conversion it also wrote zero rows. The
fee-converter test suite covers the same behavior in its replacement
tests: a slow reconciliation cannot replace after a lease takeover,
replacement work that outlives its lease keeps the original pending,
and the replacement append refuses a successor lease taken during the
database wait. The replay script is kept with the run's working state
and re-runs the whole check from the public sources.

## Notes

Migration 0092 later adds a native-gas column to both the replacement
table and the conversion table, linking a replacement to its gas
reservation; this packet covers only the 0087 journal and the
replacement policy itself. The fee-claim journal (migration 0082) and
the approval journal (migration 0088) share this same replacement path
but are separate mechanisms. Whether any replacement has ever been
journaled on a live network cannot be checked from public sources —
the journal lives in the operator's database, not on chain — so the
packet verifies the rules and the guards, not a live replacement.
