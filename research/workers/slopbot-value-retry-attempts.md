# Slopbot value retry attempts — a blocked delivery backs off instead of retrying hourly (Issue #13)

## Target

The retry-attempt count on the Slopbot value queue in the SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue #13
(Workers — the Slopbot value worker): the schema change in migration
`migrations/0103_slopbot_value_retry_attempts.sql`, which adds the
count to the processing table created in migration
`migrations/0052_slopbot_value_processing.sql` and rebuilt in
`migrations/0097_slopbot_value_historical.sql`; the retry-time and
finish routines in `workers/slopbot/value-processing.ts`; the consumer
wiring in `workers/slopbot/value-consumer.ts`; the product requirement
in `docs/slop-product-requirements.md` section 5; and the formal model
in `formal/models/slopbot/value_schema_upgrade.qnt`. The queue
indexes (0098), the historical outcome (0097), the inference-attempt
limit behind the attempts-exhausted outcome (0104), and the terminal
states (0105) are separate mechanisms and are not covered here.

## Claim

Migration 0103 gives each value delivery its own retry-attempt count,
starting at zero, advanced only by the claimed row and only when a
blocked outcome finishes — and the next retry time then backs off from
that count, one hour doubled per earlier attempt and capped at one
day, so a delivery blocked by a condition that never clears stops
costing an hourly run without ever becoming a final zero.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema: one column, nothing else

Migration 0103 holds exactly one statement: it adds an attempts
column to the value processing table, an integer that must always be
present and defaults to zero. No table is created or rebuilt, no
other column changes, and no index or trigger is added. Before 0103
the processing table has seven columns and no attempts column; after
0103 it has eight. Because the column is added with a zero default,
every row recorded before the migration keeps its place and starts at
zero. The later terminal-states rebuild in migration 0105 carries the
column forward explicitly, listing it among the columns copied into
the rebuilt table, so the count survives that rebuild unchanged.

### 2. The problem it answers: 414 deliveries retrying every hour

The migration header states the reason. A delivery whose outcome
stays retryable — source-incomplete, authority, budget, or retry — is
re-claimed whenever its retry time passes, and until this change every
such finish scheduled the next attempt at a flat hour. A delivery
blocked by a condition that never clears was therefore re-run every
hour for as long as the condition lasted, and 414 such rows were
waiting in production on 27 October. The count exists so the retry
time can grow with the number of attempts already spent instead of
staying flat.

### 3. The backoff: one hour, doubled per attempt, capped at a day

The delay function takes the attempt number, with the first attempt
counted as one, and returns the base hour doubled once per earlier
attempt, capped at one day. Read against the count a delivery
already carries, the next retry lands one hour out after zero
attempts, two hours after one, four after two, eight after three,
sixteen after four, and one day after five or more — the cap binds
from the sixth attempt onward. A block that persists therefore stops
costing an hourly run, while the outcome itself is never turned into
a final zero by the wait alone.

The retry-time routine applies that delay only to blocked outcomes.
For a transient retry outcome — a thrown failure, a source-lease
contention, or a provider outage — it returns the plain one-hour
cadence without reading the count at all. For any other outcome it
reads the delivery's own stored count, adds one, and feeds that
attempt number to the delay function, so the wait grows from the
delivery's own history and nothing else.

### 4. Only a blocked finish on the claimed row advances the count

The finish routine decides whether the count moves before it writes
anything. A finish advances the count only when the outcome is
blocked: not terminal, not parked, and not the transient retry. A
transient retry carries a retry time but does not advance the count,
because counting it would let a provider outage push a later,
unrelated block straight to the day cap. Parking is not an attempt,
so it does not advance the count either. A terminal outcome —
published, current, open, or historical at this migration — carries
no retry time and keeps the count it reached.

The advance itself is guarded to the claimed row. The finish is one
statement that settles not only the claimed delivery but every
waiting sibling delivery of the same pull request received by the
claim time, so that the outcome's inputs are all the same. The
count update applies only where the row being written is the claimed
delivery and the outcome is blocked; every sibling keeps the count
it already had. The code's own comment on that predicate says why it
is load-bearing: without it, siblings would be credited with
attempts they never made and their count would drift upward. A
sibling settled for the first time is inserted with a count of zero,
matching the migration header's rule that a delivery settled for the
first time starts at zero.

### 5. The consumer wires the count into every finish

The consumer's finish helper computes the retry time from the
delivery's own count for every non-terminal, non-parked finish, and
passes no retry time for a terminal outcome or a parked request. A
blocked outcome therefore always waits according to its own attempt
count, a transient retry always waits one hour, and a parked request
waits with no retry time until its project is active again. The
product requirement behind this is the section 5 rule to retain
immutable attempts, actual or unknown costs, duplicate refusal, and
queue limits for ongoing value scoring.

### 6. The boundary: the count is not the exhaustion rule

The column carries no bound of its own — there is no check
constraint limiting its value, and no trigger on it. The only cap is
the one-day ceiling inside the delay function. The rule that three
completed non-free attempts permit the terminal attempts-exhausted
outcome lives in the inference-attempt layer, not here: it is the
subject of migration 0104 and the terminal-states rebuild in 0105,
and the outcome code itself is not yet writable at 0103, since the
processing table's outcome check at this point admits only the eight
codes in force since 0097. This packet covers only the count and the
backoff it drives.

## Verification

Replayed the schema locally in a scratch SQLite database, using the
project's own replay harness
(`~/workspace/goals/slop-source-pr-contributions-100-prs/hidden_files/replay-0103.py`).
The 128 migration files numbered 0001 through 0102 applied verbatim,
in order, with zero failures, and the foreign-key check came back
empty. At 0102 the processing table had seven columns and no attempts
column. The 0103 file was confirmed to hold exactly one statement,
the single column addition. After applying it the column existed as
an integer, always present, defaulting to zero.

A processing row seeded before 0103 backfilled to zero, and a new
row inserted without naming the column stored zero. Then the claim
and finish statements from the worker were run against three
deliveries — a claimed delivery, a sibling of the same pull request
received before the claim, and a control delivery under a different
pull request — through four finishes in sequence. A blocked budget
finish moved the claimed delivery's count from zero to one and
settled the sibling at zero, while the control delivery gained no
processing row. A transient retry finish left the count at one. A
blocked authority finish moved it from one to two with the retry two
hours out. A terminal published finish left it at two, completed,
with no retry time. The sibling's count stayed zero through all four
finishes even as its outcome followed the latest finish, and the
delay table from the count read one, two, four, eight, sixteen, and
twenty-four hours for zero through five prior attempts, capped at
one day from the sixth onward. The foreign-key check stayed empty
throughout.

## Notes

- The replay ran the finish statement with the column set that
  exists at 0103: the incomplete-since column the current worker
  also writes only arrives in migration 0115, so it was left out and
  the attempts update itself is verbatim from the worker.
- The 414 waiting rows figure is the migration header's own
  production observation from 27 October; it was not independently
  re-measured here.
- The other file numbered 0103, the vetting template replacements
  migration, is a separate mechanism and is not covered here.
- Related work: the `historical` outcome (0097) and the queue
  indexes (0098) are documented in separate packets; the workers
  overviews (#29, #44, #103) inventory the workers without covering
  this count.
