# Solana native gas journal — the same atomic lamport journal, keyed by a journal sequence instead of an account nonce (Issue #3)

## Target

The Solana side of the native gas journal in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the schema change in migration
`migrations/0094_fee_solana_native_gas.sql`; the Solana reservation
and commit rules in `workers/fee-converter/native-gas.ts`; the
Solana signed-send check in `workers/fee-converter/store.ts`; and
the Solana tests in `workers/fee-converter/native-gas.test.ts`. The
EVM side of the same journal (migration 0092) is covered in a
separate packet; this packet covers only what 0094 adds for Solana.

## Claim

Solana fee sends reserve exact lamports in the same atomic native
gas journal as EVM sends, with one difference: Solana has no account
nonce, so the journal allocates its own sequence number per wallet
and the signed conversion commits its reservation with a null EVM
nonce, under the same lease, the same decimal-exact ceilings, and
the same immutability rules.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The rebuild admits Solana and preserves every EVM row

Migration 0094 rebuilds the `fee_native_gas` table: it copies every
row into a fresh table, drops the old one, and renames the copy back.
The only schema change is the network check, which gains Solana
alongside Base, Ethereum, and Robinhood Chain. The migration header
states the rule plainly: Solana uses the same atomic native-cost
journal, in lamports, and the legacy wei column names store exact
native base units per network. Nothing else moves: the three
ceilings stay exact decimal text, the state stays one of reserved,
signed, or abandoned, and the table keeps its unique index on one
transaction id per network, its gas-revision triggers on the network
lease, its immutability trigger, and its no-delete trigger. The
repository's own test for this migration plants a finalized EVM row
and an unknown EVM row, applies 0094, and checks the table is
byte-for-byte identical afterwards, then checks the settled row still
refuses a maximum change and a delete.

### 2. Solana has no account nonce, so the journal allocates a sequence

The reservation code has a Solana-only entry point: it refuses any
other network, then takes the next journal sequence — one above the
highest nonce already stored for that wallet — and reserves through
the same path as an EVM send, with the per-transaction ceiling as the
maximum. The sequence starts at zero, so the first four Solana
reservations for a wallet carry nonces zero through three, as the
repository's Solana test checks. A Solana conversion row carries a
null EVM nonce: the conversions table has required that since its
creation in migration 0022, so a Solana conversion naming a nonce is
refused before the gas journal ever sees it. The commit trigger in
0094 gains exactly one branch for this: it accepts a reservation
when the conversion's network is Solana and its EVM nonce is null,
alongside the existing same-nonce match for EVM. The rest of the
commit is unchanged — same network, same fee wallet, same run id,
signed bytes present, and a live network lease at submission time —
and if exactly one row is not updated, the whole conversion insert
aborts and no conversion row exists.

### 3. The signed Solana send is checked against its reserved intent first

Before the commit can happen, the store checks a Solana signed send
against the reservation it names. It decodes the signed bytes, checks
there is exactly one signature, that the fee wallet is the first
static key, that the signature is the transaction id, that the
message hash equals the reserved intent hash, and that the ed25519
signature verifies against the fee wallet. A versioned transaction,
or one that touches the Jupiter program, additionally needs the
retained account evidence recorded with the reservation, and a
Jupiter send needs that evidence to match the recorded swap's route,
wallet, tokens, and amounts. A send whose signature differs from its
reserved intent is refused, so the trigger's atomic commit can only
ever commit the exact bytes the reservation was made for.

### 4. Every 0092 guard carries over unchanged

A Solana row is held to the same shape as an EVM row: the maximum
must be decimal digits only, a row is signed exactly when it carries
a transaction id, an actual cost is present exactly when a settlement
day is present, and the nonce cannot be negative. The daily liability
accounting is the same too — one largest unresolved maximum per
wallet and sequence group — and the repository's Solana test shows
two unresolved Solana sends exhausting a ten-million-lamport daily
budget, a third refused, then each settling at one and a half
million lamports and freeing the budget in turn. Settled evidence
cannot be rewritten, a signed row cannot move state, a reserved row
may still be abandoned, and no row can be deleted.

### 5. The boundary: no replacement path, and two columns arrive later

Solana has no replacement path through this journal. The replacement
table is EVM-only by design — its network check admits only Base,
Ethereum, and Robinhood Chain, its nonce column cannot be null, and
its header describes same-nonce re-signing for EVM fee claims — so
migration 0094 correctly leaves the replacement commit trigger
unchanged: a stuck Solana send cannot be re-signed at a higher fee
through this journal the way a stuck EVM send can. Separately, the
worker's reservation insert also writes two Solana columns, the
blockhash slot and the account proof, which only arrive in
migrations 0095 and 0096. At 0094 the schema admits Solana rows and
the commit works, but the end-to-end reservation path in code needs
those later migrations.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0094 applied verbatim, in
order, with zero failures, and the foreign-key check came back
empty. At 0092 a Solana gas row was refused by the network check. A
finalized and an unknown EVM row were planted, 0094 applied, and the
table was identical afterwards, with the base lease revision
untouched by the rebuild. A valid Solana reserved row stored with
lamport ceilings, and the insert trigger moved the Solana lease
revision from zero to one. A hexadecimal maximum, a fractional
maximum, a signed row without a transaction id, and a negative nonce
were each refused by their own check. A second reservation stored at
sequence one. Inserting a Solana conversion with a null EVM nonce
flipped its reservation to signed with the transaction id and
conversion id. A Solana conversion naming a nonce was refused by
the conversions table check, with no conversion row and the
reservation still reserved. A conversion naming a reservation from
a run with no live lease was refused with the reservation-lost
error, left no conversion row, and left the reservation reserved.
A replacement row with network Solana was refused by the
replacements table's EVM-only check. A second signed row with the
same transaction id on Solana was refused by the unique index.
Setting an actual cost without a settlement day, and a settlement
day without a cost, were each refused; a full settlement stored,
and afterwards the cost could not be changed, the signed row could
not move to abandoned, and the row could not be deleted, while
abandoning a reserved row was allowed. The code-shaped reservation
insert naming the blockhash-slot column was refused with no such
column, confirming that column arrives only in migration 0095. The
replay script is kept with the run's working state and re-runs the
whole check from the public sources.

## Notes

Migrations 0095 (Solana expiry) and 0096 (Solana account proof) add
the two columns named above and are separate mechanisms, not covered
here. The fee-converter README records that live Solana conversion
is conditionally approved but its activation is deferred while owner
vault setup is elsewhere, so this packet verifies the prepared
journal rules, not a live Solana send. Whether any gas row has ever
been reserved on a live network cannot be checked from public
sources — the journal lives in the operator's database, not on
chain. The EVM gas journal (migration 0092), the fee send
replacements (migration 0087), and the approval journal (migration
0088) share the same conversion journal and lease but are separate
mechanisms.
