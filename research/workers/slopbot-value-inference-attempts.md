# Slopbot value inference attempts — three paid provider tries per source, then refusal (Issue #13)

## Target

The paid-attempt limit on Slopbot value inference in the SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue #13
(Workers — the Slopbot value worker): the schema in migration
`migrations/0104_slopbot_value_inference_attempts.sql`; the admission,
reservation, counting, and refusal routines in
`workers/slopbot/value-budget.ts`; the key, the limit, and the call
flow in `workers/slopbot/value-inference.ts`; the route in
`workers/slopbot/models.ts`; the product requirement in
`docs/slop-product-requirements.md` section 5; and the formal model in
`formal/models/slopbot/bot_inference_reservations.qnt`. The retry
backoff on the delivery count (0103), the terminal states (0105), and
the zero-call reconciliation and attempt-completion tables the
counting rule reads (0118, 0120) are separate mechanisms and are not
covered here, except where the counting rule itself depends on them.

## Claim

One inference key — one installation, one source digest, one prompt,
one schema, one route — may start at most three paid provider
attempts. A retry after a provider failure or an invalid result is a
new paid attempt against the same key, so it is bounded; a changed
source gets a new key and its own three. Admission and the budget
reservation are each decided from a single database snapshot, only
attempts that reserved budget count toward the limit, and a completed
zero-call attempt or a free provider-budget failure does not count
unless a real cost appears. When the limit is reached the refusal
says whether the attempts are truly spent or merely still pending.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema: one table, three columns, nothing else

Migration 0104 holds exactly four statements: it creates one table,
one index, and two triggers. The table has three columns — an attempt
id, an inference key, and a start time — and is strict. The key must
be exactly 64 characters long. The index is on the key, so the
per-key count reads through it. The two triggers refuse any update
and any delete, with the message that value inference attempts are
immutable. Before 0104 the table does not exist; after 0104 it does,
with exactly those three columns. The table holds no cost, amount, or
outcome column — costs live in the provider-cost table, and outcomes
live in the processing table, so this table records only that an
attempt started, for which key, and when.

### 2. The key: seven fields, hashed, one per source

The inference key is the SHA-256 hex of a JSON object with seven
fields: the installation id, the source digest, the prompt's system
text, the prompt's policy text, the output name, the output schema,
and the route. The route is fixed: Surplus Opus 5.5 first, then
GPT-6.1 Sol as fallback. Because the source digest is one of the
seven fields, a changed source produces a different key and therefore
its own three attempts, while an unchanged source reuses the same key
and the same budget. The key is computed before any retained result
is read, so a valid retained result for the key is reused without any
provider call at all — the retry limit only binds work that actually
needs a new call.

Recomputing the hash for the upstream test's own fixture — installation
1, a source digest of 64 a's, the fixture system and policy texts, the
fixture name and schema, and the two-step route — gives the 64-hex key
starting 450a5dde and ending fccf33a3. Changing only the source digest
to 64 b's gives a different key, which is the whole point of keying
on the digest: the same source retries against one budget, a new
source starts fresh.

### 3. The limit is three, and admission is one atomic decision

The limit is a named constant, three paid provider attempts per
inference key. Admission inserts the attempt row only when two
conditions hold in the same statement: the counted attempts for the
key are below three, and no row with this attempt id exists yet. The
insert and the refusal classification run as one batched pair against
a single database snapshot, so the write and the decision cannot
disagree about what the database held. If the row is written, the
attempt is admitted; if zero rows are written, the refusal
classification is the answer. A duplicate attempt id therefore admits
no new call, and two concurrent admissions cannot both take the last
slot, because each insert re-checks the count in its own statement.

### 4. Only attempts that reserved budget count

The count is not a count of rows in the attempts table. It joins
each attempt to its budget reservation, so an attempt row with no
reservation contributes nothing. In the live replay, three reserved
attempts for one key count as three, a fourth attempt row written
without a reservation leaves the count at three, and a changed-source
key counts zero with its first admission succeeding. The reservation
itself is gated the same way: the reservation insert requires that an
attempt row with this id and key already exists and that the counted
attempts for the key are still below the limit. A retry therefore
cannot reuse an earlier reservation as permission for another
provider call — it must admit a fresh attempt and reserve fresh
budget first.

### 5. Two things do not count: a free failure, and a completed zero-call attempt

The count excludes an attempt whose only cost row is a provider
failure marked "provider budget exhausted", unless a non-free cost
row for the same attempt also exists. A provider spending denial is
not a paid attempt, so it does not spend one of the three. In the
replay, adding exactly that failure row to the first of three counted
attempts drops the count from three to two, and a fourth admission
then succeeds.

The count also excludes an attempt that completed with zero calls
and zero recorded cost, provided no cost row was ever observed for
it. Such an attempt made no provider call, so it is not a paid
attempt either. In the replay, completing the second attempt with
zero calls and zero cost drops the count by one more. But the
exclusion is conditional on the absence of observed cost: adding a
late cost row for that same attempt makes it count again, because a
late receipt proves a call did happen after all. The upstream test
checks exactly this case.

### 6. The refusal says spent or merely pending

When admission fails, the refusal is one of two words. It is
"attempts" only when the number of completed, non-free attempts for
the key has reached the limit — that is the hard exhaustion case. In
every other case it is "attempts-pending": the cap may be occupied by
reservations whose outcome is still unknown, but that is not proof
every paid attempt is exhausted. In the replay, a key whose attempts
are all still pending refuses as "attempts-pending", while a key
with three completed attempts each carrying a non-free cost refuses
as "attempts". If the refusal is the hard one, the caller re-reads
the retained result once more before giving up, because a completing
attempt may have retained its result after the first read.

### 7. The boundary: what the database does not enforce

Two details sit outside the migration. First, the table's key check
is length only: a 64-character uppercase key passes the database
check, and it is the code that requires lowercase hex before
reserving budget. A malformed key therefore cannot reach the provider
through the reservation path, but the table alone does not stop it.
Second, the counting rule reads the attempt-completions table, which
only arrives in migration 0120, and the reconciliations table, whose
zero-call form only arrives in migration 0118. The upstream test
loads both later migrations alongside 0104 for exactly this reason,
and the replay here does the same for the counting checks: the table
claims were verified at 0104, the counting claims at 0120. The
formal model records the same dependency, sourcing 0104 together
with 0118 and 0120.

## Verification

Replayed migrations 0001–0104 verbatim in scratch SQLite (128 files
through 0120, 0 failures, foreign-key check empty): no attempts table
at 0103; at 0104 exactly one table, one index, and two triggers, with
the three expected columns under strict typing. A row with the
recomputed fixture key stored; a 3-character key refused by the
length check; a 64-character uppercase key stored at the database
level (length check only); a duplicate attempt id refused by the
primary key; an update and a delete each refused by its trigger with
the immutability message. At the 0120 scope: three reserved attempts
counted as three and a fourth admission wrote zero rows; a duplicate
attempt id wrote zero rows; an attempt without a reservation left the
count at three; a changed-source key counted zero and admitted its
first attempt; a free provider-budget failure dropped the count from
three to two and the fourth admission then wrote one row; a zero-call
completion dropped the count by one more and a late cost row brought
it back; the refusal read "attempts-pending" for the pending key and
"attempts" for a key with three completed non-free attempts.
