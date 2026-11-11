# Slopbot value — a pre-start closed PR ends as `historical`, never assessed by the API route (Issue #13)

## Target

The `historical` outcome in the Slopbot value pipeline in the SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue #13
(Workers — the Slopbot value worker): the schema change in migration
`migrations/0097_slopbot_value_historical.sql`, which adds the outcome
to the processing table created in migration
`migrations/0052_slopbot_value_processing.sql`; the decision in
`workers/slopbot/value-consumer.ts`; the start date and the mirrored
intake rule in `workers/slopbot/value-settings.ts`; the terminal
recording in `workers/slopbot/value-processing.ts`; the subscription
import gate in `workers/slopbot/value-import.ts`; the incomplete-
assessment reader in `backend/notifications/incomplete-assessments.ts`;
the formal model in `formal/models/slopbot/value_schema_upgrade.qnt`;
and the tests in `workers/slopbot/value-settings.test.ts`,
`workers/slopbot/value-live-registry.test.ts`, and
`workers/slopbot/value-migration.test.ts`. The later extensions of the
same table — queue indexes (0098), the attempts column (0103), and the
parked terminal state (0105) — are separate mechanisms and are not
covered here.

## Claim

A value request for a pull request closed before the paid API
assessment start ends as terminal `historical`: the row is completed
with no retry time and no paid assessment is ever made, and that work
can only be scored through the subscription intake, which accepts
only pre-start work against the same cutoff.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema: one new outcome code, added by a rebuild

Migration 0052 creates the operational claim state for value
requests, `slopbot_value_processing`, keyed by delivery id against
`slopbot_value_requests`, with a state of running, waiting, or
completed and an outcome drawn from seven codes: published, current,
open, source-incomplete, authority, budget, and retry. Migration
0097 rebuilds the table — copy the rows into a new table, drop the
old one, rename — with exactly one change: `historical` joins the
outcome list, making eight codes. The migration header states the
rule behind it: ongoing API assessment starts on 1 November 2026,
September and October go through the subscription intake, and a
request for a PR closed before the start ends as `historical`
instead of waiting forever. The rebuild preserves every existing row;
nothing else in the table changes.

### 2. The start: a fixed date, never earlier, and a refused config stops inference

The fixed start is 1 November 2026 at midnight UTC, recorded as an
owner decision dated 25 October 2026 in the settings module: ongoing
API assessment starts in November, and September and October use the
subscription assessment and import path only. The consumer reads its
configured start from settings, which take an explicit start from the
environment or fall back to the fixed date in alerts-only mode. A
configured start earlier than the fixed date is refused, as is a
malformed one, and a refused configuration yields no settings at
all — the consumer then ends the request as `budget` rather than
assessing anything. Selecting alerts-only is explicit; the date
itself never enables a call. The product requirements state the same
boundary: paid API assessment begins on 1 November 2026 UTC, and
September and October assessments use ChatGPT subscription
subagents, imported through the standard assessment journal with
exact attribution.

### 3. The consumer decision: merge time, else close time, against the start

The value consumer claims one durable delivery, then works through
its gates in order: the project must be registered and active (a
paused, retired, or unregistered project parks the request with no
retry time), the installation and the configured settings must check
out, and the repository must be the registered one under its current
name. It then reads the pull request from GitHub. A 404 — GitHub
has no such pull request — ends as `missing`, terminal. A PR that is
not closed ends as `open`, terminal. Otherwise the consumer takes
the merge time, falling back to the close time when the PR was
closed unmerged, and an unparseable date ends as
`source-incomplete`, which stays retryable. Only then comes the
historical rule: when that time falls before the configured start,
the request finishes as `historical`, terminal. The code comment
states the routing plainly — historical work is handled by the
subscription intake, never this API route — and a later reopen or
close sends a new delivery with its own request, so a PR that is
reopened and closed again after the start is judged on its new
close time.

### 4. The recording: terminal means completed, no retry, no attempt counted

The outcome type lists `historical` among the final, recorded
outcomes, alongside published, current, open, missing, and
attempts-exhausted. The finish routine treats every terminal outcome
the same way: the row moves to state `completed` with a null retry
time, and the attempt count does not advance — only a blocked,
non-terminal outcome advances it, and a transient retry does not
either, so a provider outage cannot push a later unrelated block
toward the day cap. Finishing also settles every waiting sibling
delivery that names the same installation, repository, and PR and
was received by the claim time, because every input of the outcome
is the same for them; a later delivery, or one under another
installation or repository name, keeps its own request. A terminal
outcome with a retry time attached, or a non-terminal outcome
without one, is refused outright, so a `historical` row can never
carry a retry time.

### 5. The other side: the subscription intake accepts only pre-start work

The intake mirrors the consumer rule in a single shared helper: a
closed pull whose merge time, else close time, falls before the
start counts as a historical subscription source, and nothing else
does — not an open PR, not an undated one, not one closed at or
after the start. The subscription import path collects the PR's
evidence from GitHub and refuses any selection that fails that
check, with the error that the subscription intake covers only work
accepted before the API start. The intake is an admin-only endpoint
that publishes through the standard assessment journal, so a
subscription declaration on its own is not an API receipt or
billing proof. The cutoff follows the consumer's configured start,
and when settings refuse inference it falls back to the fixed
start, so a delayed API start never leaves work owned by neither
route: work closed before the delayed start still belongs to the
intake, and work closed after it belongs to the API route.

### 6. Downstream readers treat `historical` as done

The incomplete-assessment reader lists `historical` among the
completed outcomes that clear the incomplete marker: once any
delivery for the same repository and PR number is completed with a
published, current, open, historical, or missing outcome at or
after the marker time, the assessment no longer counts as
incomplete. The formal model for the value schema upgrade lists
`historical` among the eight outcomes a migration must preserve
verbatim across the table rebuild, with state, token, retry time,
and attempt count unchanged. The terminal-state upgrade test plants
one row per outcome, including a completed `historical` row, applies
the later rebuild, and requires every row to come back identical.

### 7. The boundary: `historical` is a routing record, not a value judgment

Like `missing` and `attempts-exhausted`, `historical` records that
no assessment happened; it is not an assessment and implies no low
value. No model call, no paid attempt, and no publication follows
from it — the PRD's historical publication hold in section 7
governs what of the September and October work is published, and
that is a separate rule from this routing outcome. The consumer
reaches the historical check only after the project, installation,
settings, repository, and identity gates pass, so a request that
fails an earlier gate ends as parked, budget, authority, or retry
instead, and the date is never consulted for those. The check reads
the PR's merge or close time from GitHub at claim time, so the
outcome reflects the PR's state when the worker read it, not when
the delivery was received.

## Verification

Replayed the schema locally in a scratch SQLite database: the 102
migration files numbered 0001 through 0096 applied verbatim, in
order, with zero failures, and the foreign-key check came back
empty. At 0096 a `historical` outcome insert was refused by the
table check, which then listed only the original seven codes. After
applying 0097 the rebuild preserved the planted rows verbatim, a
completed `historical` row stored with a null retry time, and a
bogus outcome was still refused by the check, which now lists all
eight codes including `historical`. The schema read-back confirms
the code is in the check list.

The code-level behavior is exercised by the project's own tests.
The settings tests accept work merged or closed before the start
(31 October 23:59:59, and a September close with no merge time),
refuse work closed exactly at the start and work closed on 2
November, and refuse open, reopened, and undated work. The live
registry test drives the consumer end to end: September and October
changes end as `historical` with state `completed`, and one read
settles every waiting delivery for a PR closed before the start,
with two or three deliveries each recorded historical. The replay
script is kept with the run's working state and re-runs the whole
check from the public sources.

## Notes

The queue indexes on the same table (migration 0098), the attempts
column (0103), and the parked outcome with its terminal-state
rebuild (0105) are later, separate mechanisms on
`slopbot_value_processing` and are not covered by this packet, nor
is the review-budget rounding that caps paid attempts. The value
pipeline's other terminal outcomes — published, current, open,
missing, attempts-exhausted — each have their own decision rule in
the consumer and are separate packets. Whether any particular
September or October pull request was actually scored through the
subscription intake cannot be checked from public sources — the
assessment journal lives in the operator's database, not on chain —
so this packet verifies the routing rules, not any individual
assessment.
