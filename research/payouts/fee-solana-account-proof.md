# Solana account proof — a versioned fee send keeps its finalized lookup mapping, reviewed before signing (Issue #3)

## Target

The Solana account proof retained on the native gas journal in the
SLOPCASH codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue
#3 (Payouts & bounties): the schema change in migration
`migrations/0096_fee_solana_accounts.sql`; the proof type and its
builder and verifier in `workers/fee-converter/solana-accounts.ts`;
the reservation path in `workers/fee-converter/native-gas.ts`; the
signed-commit gate in `workers/fee-converter/store.ts`; the signing,
recovery, and receipt call sites in `workers/fee-converter/solana.ts`;
the Jupiter route review in `workers/fee-converter/jupiter-route.ts`
and `workers/fee-converter/solana-route-accounts.ts`; the formal
model in `formal/models/fees/solana_route.qnt`; and the tests in
`workers/fee-converter/native-gas.test.ts` and
`workers/fee-converter/solana-route-prepare.test.ts`. The Solana gas
journal itself, its blockhash anchor, and its expiry recovery are
covered in separate packets (migrations 0092, 0094, and 0095); this
packet covers only what 0096 adds for the account proof.

## Claim

A versioned (v0) Solana fee send can only be signed and committed
when its gas-journal reservation retains a JSON account proof — the
finalized address-lookup-table mapping reviewed before signing — and
that proof is immutable once stored; a legacy transaction needs no
proof, and a reservation made before this migration carries none.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The column: one JSON document, Solana-only, immutable

Migration 0096 adds a single column to the gas journal, the Solana
account proof, as text. A check constraint allows it to be null, or
else requires the row to be a Solana row holding valid JSON. A
before-update trigger refuses any change to the stored value, so a
retained proof can never be rewritten or cleared. The migration
header states the intent: preserve the finalized lookup mapping
reviewed before a versioned signature, while legacy attempts retain
null and reconcile using their signed static keys.

### 2. What the proof is: the resolved lookup mapping, bound to the message

A Solana versioned transaction does not list every account it
touches: it names address lookup tables and indexes into them, so
the accounts a signature actually authorizes depend on what those
tables contain at signing time. The proof is the retained record of
that resolution. It carries the hash of the signed message, the full
resolved key list in order, the loaded writable and readonly
addresses, and one entry per lookup table used: the table address,
the finalized slot the table was read at, the SHA-256 of the table
bytes, the slot the table was last extended, and the writable and
readonly indexes with the addresses they resolve to. When the send
is a Jupiter route, the proof additionally carries the reviewed
route: the expected program, wallet, input and output mints and
programs, amounts, slippage bound, and one observed account record
per resolved key, each with its slot, owner, lamports, and data hash.

The builder reads each lookup table with a finalized account lookup,
refuses a table whose owner is not the lookup-table program or whose
layout is not a valid table, and refuses a table that is not warmed
up — its last extension must predate the finalized read slot. It
resolves every index the message names into an address, assembles
the proof, and then runs the verifier on its own output before
returning it, so a proof is never stored unverified. The header
comment states the rule behind this: finalized active tables have
append-only indexes, so a quote's address map is never trusted —
only the finalized table read counts.

### 3. The verifier: the proof must match the signed bytes exactly

The verifier re-derives the message hash from the raw signed bytes
and refuses a proof whose hash differs, whose table count differs
from the message's lookup count, or whose table addresses and
indexes differ from the message's descriptors. It checks that each
table's data hash is a 64-hex digest, that its last-extension slot
predates its read slot, and that the resolved writable and readonly
addresses, in order, rebuild exactly the proof's key list, with no
duplicates and at most 256 keys. When a route review is present it
checks every expected key is a valid public key, that the expected
wallet is the first resolved key, that the slippage bound lies
between zero and ten thousand basis points, that all three amounts
are positive decimal strings, that the observed accounts cover every
resolved key, and that each observation's slot, data length, and
data hash are well formed. Any mismatch throws, and the caller
refuses the send.

### 4. Review before signing: no versioned signature without a proof

The signing path resolves the proof — either the one reviewed during
route preparation or a freshly built one — and verifies it against
the raw bytes before any signature is produced. A Jupiter send
without a route review in its proof is refused outright. The
reservation path takes the proof alongside the blockhash slot: the
journal sequence is allocated, and the reserve call refuses a proof
whose message hash differs from the reservation's intent hash, so a
proof cannot be attached to a different transaction than the one it
was reviewed for. The proof is written into the reservation row in
the same insert that creates the reservation, under the live network
lease.

### 5. The commit gate: the store re-verifies the retained proof

When the signed send is committed, the conversion store reads the
reservation row and applies the gate. A legacy Solana transaction
passes without a proof, because its accounts are all static keys in
the signed message. A versioned transaction without a retained proof
is refused with the error that versioned Solana signing lacks
retained account evidence. With a proof, the store parses it and
runs the same verifier over the raw signed bytes before accepting
the commit; for a Jupiter send it additionally requires the proof's
route review and checks the expected program, wallet, input mint,
and output mint against the reservation's fee wallet and the
conversion's tokens. A proof that was tampered with after review —
even a single changed lookup index — fails verification and the
commit is refused, leaving the reservation reserved rather than
signed.

### 6. Where the retained proof is re-used: recovery and receipts

The proof is read back in two later places. During recovery, when a
signed Solana send has no finalized receipt yet, the worker
re-verifies the retained proof against the signed bytes before
computing rent accounts, and a versioned recovery without a retained
proof is refused. At receipt finalization, a retained route review
is used to compute the finalized route credit from the on-chain
receipt, so the amount credited is checked against the same reviewed
expectation the send was signed under.

### 7. The boundary: the database checks the envelope, the code checks the content

The schema enforces only the envelope: the value must be valid JSON,
must sit on a Solana row, and must never change. It does not check
that the JSON is a well-formed proof — that the message hash binds
to a real message, that the table hashes are real, or that the route
expectation matches the tokens. Those checks live in the verifier
and run at reserve time, at commit time, and again at recovery, so a
row can hold JSON that is not a valid proof, but such a row can
never produce a signed commit. A legacy row with a null proof is
accepted by the schema and by the commit gate, because its accounts
are all static and the signature itself covers them. There is no
dedicated formal model for the account proof; the route model states
the same ordering in miniature, that route account, read, and lookup
proofs precede signing and the receipt independently proves the
output, with a negative test showing a signing attempt with an
unresolved lookup fails.

## Verification

Replayed the schema locally in a scratch SQLite database: the 128
migration files numbered 0001 through 0096 applied verbatim, in
order, with zero failures, and the foreign-key check came back
empty. At 0095 the account-proof column did not exist and a
reservation insert naming it was refused for want of the column.
After 0096 the column existed: a reserved Solana row carrying a
JSON account proof stored, the stored document round-tripped
verbatim, and the Solana lease revision moved from zero to one. A
non-JSON proof was refused, a proof on an EVM row was refused, and
a Solana row with a null proof stored, confirming the legacy
allowance. Rewriting the retained proof to a different value and
clearing it to null were each refused as immutable, and the stored
document was unchanged afterwards; re-stating the identical value
was allowed, and deleting the row was refused as permanent. The
code-level gate is exercised by the project's own tests: a versioned
send with no retained proof is refused at commit, a proof with one
changed lookup index is refused, and a valid proof is retained on
the signed row and matches the reviewed proof exactly. The replay
script is kept with the run's working state and re-runs the whole
check from the public sources.

## Notes

The Solana native gas journal (migration 0094), its blockhash anchor
and expiry recovery (migration 0095) are separate mechanisms from
this account proof, as is the EVM gas journal (migration 0092). The
fee-converter README records that live Solana conversion is
conditionally approved but its activation is deferred while owner
vault setup is elsewhere, so this packet verifies the prepared
account-proof rules, not a live Solana versioned send. Whether any
gas row has ever carried a retained account proof on a live network
cannot be checked from public sources — the journal lives in the
operator's database, not on chain.
