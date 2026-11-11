# Slopbot value — the queue indexes that keep the running-claim and per-PR settlement reads off full scans (Issue #13)

## Target

The two queue indexes in the Slopbot value pipeline in the SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT), as named in Issue #13
(Workers — the Slopbot value worker): the schema change in migration
`migrations/0098_slopbot_value_queue_indexes.sql`, which indexes the
request and processing tables created in migrations
`migrations/0050_slopbot_value_requests.sql` and
`migrations/0052_slopbot_value_processing.sql`; the scheduler's
next-due read and the claim routine in
`workers/slopbot/value-consumer.ts` and
`workers/slopbot/value-processing.ts`; and the settlement join in
`workers/slopbot/value-processing.ts` that closes every waiting
sibling delivery of one pull request. The later extensions of the
same tables — the attempts column (0103), the terminal-state rebuild
(0105), and the parked-checks table (0106) — are separate mechanisms
and are not covered here.

## Claim

Migration 0098 adds exactly two indexes and nothing else: one on the
processing table keyed by state then lease expiry, which serves the
running-claim checks of the scheduler and the claim routine, and one
on the requests table keyed by repository id then pull request
number, which serves settlement's read of only the deliveries of one
pull request. Neither index changes a stored row or any behavior; each
turns a full scan in a hot read into an index search.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The schema: two tables, two indexes, no other change

Migration 0050 creates the durable request table
`slopbot_value_requests`: one row per received delivery, keyed by
delivery id, carrying the installation id, the repository id, the
owner and repository name, the pull request number, and the time
received. Its triggers refuse every update, delete, and re-insert,
so a request row is immutable once stored. Migration 0052 creates
the operational claim state, `slopbot_value_processing`: one row per
delivery, keyed by the same delivery id, carrying a claim token, a
lease expiry, a state of running, waiting, or completed, an outcome
code, a retry time, and an update time. Migration 0098 touches
neither table's rows or columns. Its file holds exactly two index
creations and its header states the reason for each: settlement
gives every read value request a processing row, the running-claim
checks of the scheduler and the claim read only running rows, and
settlement reads only the deliveries of one pull request, not the
whole request history.

### 2. The running index: state, then lease expiry

The first index, `slopbot_value_processing_running`, covers the
processing table on state first and lease expiry second. That order
matches the two running-claim checks exactly. The scheduler's
next-due read picks the earliest due request whose processing row is
absent, or waiting past its retry time, or running past its lease
expiry, and it refuses any request whose pull request already has a
busy row — a processing row in state running whose lease has not yet
expired. The claim routine inserts a running row for a delivery only
when no other running row for the same pull request holds a live
lease, and its conflict update reclaims a row only when that row is
running past its lease or waiting past its retry time. Both checks
predicate on state together with the lease expiry, which is exactly
what the index stores, so the running half of each check is served
from the index rather than scanned. The waiting half — state waiting
with a retry time reached — uses only the state prefix of the same
index, since the index's second column is the lease expiry, not the
retry time.

### 3. The per-PR index: repository id, then pull request number

The second index, `slopbot_value_requests_pull`, covers the requests
table on repository id first and pull request number second. That
order matches the way settlement finds a pull request's deliveries.
When a claimed delivery finishes, the finish routine settles not
only that delivery but every waiting sibling delivery naming the
same installation, repository, and pull request and received by the
claim time, so the outcome's inputs are all the same. Its join
matches sibling request rows to the claimed row on repository id and
pull request number, with the installation, owner, and repository
name as further equalities — the per-PR lookup the index exists
for. The same repository-and-PR pair also appears in the busy checks
of the scheduler and the claim routine, which join other requests to
a busy processing row; there the planner reaches the other request
through its delivery-id primary key and applies the repository and
pull request equalities as filters, so the pull index is not what
serves that join — the settlement join and direct per-PR pulls are
its readers.

### 4. The boundary: indexes only

Because 0098 adds indexes and nothing else, no outcome, state, or
retry rule changes with it. A request that was running stays
running, a settled row stays settled, and the set of rows any query
returns is identical before and after — only the path the database
takes to reach them changes. The verification below confirms that
directly: the same predicates return the same rows at 0097 and at
0098, while the query plans change from scans to index searches.

## Verification

Replayed the schema locally in a scratch SQLite database, using the
project's own replay harness
(`~/workspace/goals/slop-source-pr-contributions-100-prs/hidden_files/replay-0098.py`).
The 128 migration files numbered 0001 through 0097 applied verbatim,
in order, with zero failures, and the foreign-key check came back
empty. At 0097 neither index existed, and the 0098 file was confirmed
to hold exactly two index creations and no other statement. After
applying 0098 both indexes existed with exactly the indexed columns
recorded above.

With 300 seeded requests spread over 30 repositories and 10 pull
requests each, plus one processing row per delivery in mixed states,
the query plans changed as claimed: at 0097 the running predicate
(state running with lease expired) and the per-PR pull (one
repository id and pull request number) each scanned their table, and
the settlement join scanned the sibling side; at 0098 the running
predicate searched through the running index on state and lease
expiry, the per-PR pull searched through the pull index on
repository id and pull request number, and the settlement join
searched the sibling side through the pull index. The stored rows
were preserved verbatim by 0098 — 300 requests and 300 processing
rows before and after — and the predicates returned the same rows at
both stages: 50 expired running rows and exactly 1 row for one pull
request.

## Notes

- The replay used SQLite's query planner on a 300-row seed; on the
  production D1 database the same index shapes serve the same
  predicates, but absolute timings were not measured here and no
  timing claim is made.
- Migration 0098 does not index the outcome or retry-time columns,
  so waiting-retry reads are served only by the state prefix of the
  running index, as noted in the evidence.
- Related work: the `historical` outcome (0097) and the attempts
  column (0103) are documented in separate packets; the workers
  overviews (#29, #44, #103) inventory the workers without covering
  these indexes.
