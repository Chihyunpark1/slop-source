# Monthly payment replacement attempts — a source change appends a new signed attempt beside the permanent first authorization (Issue #3)

## Target

The monthly payment replacement-attempt mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the attempt table and the current-authorization view created
by migration `migrations/0083_monthly_execution_attempts.sql`; the
publisher that signs and appends attempts
(`backend/payments/monthly-publication.ts`, the publication function);
the executor scheduler that consumes them
(`workers/payments/index.ts`, the monthly-commitment run); the reserve
release path that retains every attempt
(`backend/payments/monthly-reserve-release.ts`, the retained-allocation
reader); the public read route and its rules documented in
`backend/payments/README.md` (the authorization and execution section);
and the product rule in `docs/slop-product-requirements.md` (PRD section
6, monthly payments).

## Claim

When a source change invalidates an unadmitted EVM V2 signature, the
publisher appends a new signed attempt keyed by the new source sequence
beside the permanent first authorization: attempts are immutable and
permanent, only a strictly newer sequence is ever stored, and the public
read, the executor, and the reserve-release path all see every attempt
while the first authorization stays fixed.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The attempts table keeps each replacement beside the first authorization

Migration 0083 creates `monthly_payment_authorization_attempts` with one
row per project, period, network, and source sequence: the signed
authorization as JSON and its publication time. A foreign key binds
every attempt to the first authorization it belongs to, so an attempt
cannot name a month that was never published. The source sequence is a
plain decimal string of 1 to 78 digits, with no leading zero unless the
value is exactly zero — the 78-digit bound is the decimal width of a
uint256. The authorization must be valid JSON. An update of a stored
attempt is refused as immutable and a delete as permanent. The
migration's own header states the reason: source consumption can
invalidate an unadmitted EVM V2 signature, so each replacement attempt
is retained beside the permanent first authorization.

### 2. Only a valid, strictly newer attempt is appended

The publisher signs a replacement only for an EVM V2 plan, and only
after the same checks that gate the first authorization: the reservation
must be version 2, its allocation digest must be the frozen snapshot
hash with a `0x` prefix, its whole gross must equal the plan's total
gross, and its source sequence must be a plain decimal string of at
most 78 digits. Any failure rejects the attempt as invalid before
anything is stored.

The append itself is a single insert that selects from the first
authorization only when the snapshot hash still matches and automatic
monthly payment is still on (the latest settings row, defaulting to
on). Its guard admits only a sequence strictly newer than every stored
attempt, compared in canonical decimal order — longer first, then
lexicographic — and a conflict does nothing. So re-offering an older
signed attempt writes zero rows, and the newest attempt is always the
one with the greatest sequence. After the insert the publisher reads
back through the current-authorization view and, if the stored input
differs while automatic payment is still on, reports a publication
conflict instead of silently keeping a wrong row. If the chain already
admitted the month, the publisher keeps the latest published attempt
and moves on, so a permissionless caller can resume from it.

### 3. A source consumed between attempts shrinks the allocation, not the snapshot

The attester signs the remaining sources at one finalized block. A
source consumed during signing leaves its intent behind but publishes
nothing — the signing itself fails and no attempt row is written. When
a source is consumed between two successful signings, the second plan
covers fewer recipients and a smaller remaining gross against the same
frozen month: the payment test suite's case has the first attempt at
sequence 9 covering the full allocation, and the second at sequence 10
covering only the remaining recipient with a smaller remaining gross
and a different allocation root, while the request fields and the
original authorization row are unchanged. The snapshot, the whole
allocation amount, and every prior signature stay fixed; only the
remaining-sources plan is re-signed.

### 4. Ordering is decimal text, never an int64 cast

Source sequences are uint256 values, which can exceed SQLite's int64
range. The current-authorization view therefore picks the latest
attempt by ordering on the sequence's length first and its text second,
never by casting to a number — a 20-digit sequence sorts after every
shorter one regardless of its numeric size. The payment test suite
exercises exactly this: an attempt at two to the power of sixty-four
becomes the current authorization, while the earlier attempts stay
stored underneath it.

### 5. The public read, the executor, and the release path all see every attempt

The view returns the newest signed attempt when one exists and
otherwise the first authorization, so the public surface always shows
the current executable input while the original stays stored
underneath. The read route for a project's month and network returns
that latest attempt and its publication time without calling a signer
or any RPC, and exposes no private adjustment history. The executor's
monthly-commitment run reads through the same view, so it always
submits the latest signed input — and it sends the newest period's
roots first, because a leaf mined first would advance the source
sequence and invalidate the signed reservation. The reserve-release
reader takes the union of the first authorization and every attempt,
because a prior signed attempt can still win admission. Once the chain
admits a root, no new attempt is signed; legacy EVM and Solana keep
their original intent. A reviewed EVM upgrade can add a V2 attempt to
a legacy publication, and the public response also retains the original
signature, so an uncertain legacy transaction can be reconciled if it
wins admission.

## Verification

Replayed the schema locally in a scratch SQLite database: the 87
migration files numbered 0001 through 0083 applied verbatim, in order,
with zero failures, and the foreign-key check came back empty. On a
frozen month with one obligation, automatic payment on, and a first
authorization stored, running the publisher's attempt-insert statement
verbatim stored exactly one attempt at sequence 9; a second insert at
sequence 10 stored a second row and the current-authorization view
returned the sequence-10 input; re-offering sequence 9 wrote zero rows
and the view stayed on sequence 10; an attempt at two to the power of
sixty-four stored a third row and the view returned it. An update of a
stored attempt was refused as immutable and a delete as permanent; a
direct insert naming an unknown authorization was refused by the
foreign key; a non-decimal sequence and a leading-zero sequence were
both refused by the sequence check, and a non-JSON authorization by
the validity check. With the latest settings row turning automatic
payment off, a new attempt wrote zero rows. On a second project with
no attempts, the view returned the first authorization. The
reserve-release union query returned all three signed inputs — the
first authorization plus both attempts. The payment test suite
exercises the same behavior in its monthly tests: attempt counts of
one, then two, then three; an older signature cannot replace the newer
public input; a source consumed during signing publishes nothing; the
two-to-the-sixty-fourth sequence orders correctly; and update and
delete of attempts throw. The EVM monthly-reserve integration test
asserts two attempt rows beside the permanent first authorization.

## Notes

The first authorization and the execution cursor are covered by the
earlier packet on monthly payment authorizations; this packet covers
only the replacement attempts and the current-authorization view. The
chain-side admission check that rejects a stale root, and the
attester's own signing of the reservation at a finalized block, are
separate mechanisms. Whether a superseded attempt is ever surfaced to
contributors through any channel other than the documented read route
was not found in the sources checked.
