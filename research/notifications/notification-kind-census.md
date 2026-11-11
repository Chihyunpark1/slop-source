# Notification kinds — the complete census at the current tip

## Target

The notification kind system of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`: every migration that
defines the `notifications` table's `kind` CHECK
(`migrations/0024_notifications.sql` and its successors), the writer
functions in `backend/notifications/events.ts`, every other
production statement that inserts a notification row, the inbox read
path in `backend/notifications/handler.ts`, and the presentation
registry in `src/lib/notifications.ts`. This packet extends the
packet in open PR #38, which documented the state named in Issue #14
(migrations 0024/0029/0030, fifteen kinds) and explicitly left the
later kind widenings unenumerated; enumerating them, and the
producers of every kind, is the whole of this packet. The checker is
`scripts/notification-kind-census.py`; tests are
`tests/test_notification_kind_census.py`.

## Claim

The inbox kind set did not stop at the fifteen kinds of migration
0029: at the pinned commit the schema admits 21 stored kinds, 19 of
them have a production producer (seventeen writer functions in
`events.ts` plus five direct inserts elsewhere), the two admission
kinds are legacy rows with no producer left, a twenty-second kind
(`slopbot_appeal_resolved`) exists only as a read-time derivation in
the inbox query and can never be stored, and the security outbox has
enqueued two kinds — not one — since migration 0063.

## Evidence

All references are to `SlopDotCash/slopdotcash` at the pinned commit
above. Every count below is the output of the census script, which
parses the files mechanically; the script's full output is
reproducible with the commands in Verification.

### 1. The widening chain: 7 → 15 → 19 → 20 → 21 stored kinds

Each widening migration rebuilds the `notifications` table with a
longer `kind` CHECK list. The census verifies the chain is strictly
increasing (no kind was ever dropped):

| Migration | Stored kinds | Added |
| --- | --- | --- |
| 0024_notifications.sql | 7 | application_approved, application_rejected, project_revision, award_reserved, payment_paid, payout_held, wallet_changed |
| 0029_notification_event_kinds.sql | 15 | payout_exception, project_banned, project_quarantined, project_reinstated, reinstatement_denied, reinstatement_requested, reinstatement_review, security_case |
| 0063_account_closure_notification_events.sql | 19 | project_installation_lost, project_ready, project_scan_failed, security_report_received |
| 0065_slopbot_appeal_notifications.sql | 20 | slopbot_appeal_review |
| 0079_slopbot_scam_review_notifications.sql | 21 | slopbot_scam_review |

### 2. Producer census: who can write each kind

`backend/notifications/events.ts` holds seventeen `notify…` writer
functions sharing one INSERT template and one
`ON CONFLICT (event_key, recipient_github_id) DO NOTHING` clause
(events.ts:29–35). Two writers choose their kind with a SQL CASE
(`notifyProjectRevision`: `project_ready` when the revision makes
the project active from a non-active state, else `project_revision`;
`notifyProjectEnforcement`: five kinds from the enforcement action).
Five production statements insert rows directly, outside `events.ts`.
The census counted at least one production call site for every
writer (25 production call sites in total):

| Kind | Since | Producer(s) |
| --- | --- | --- |
| application_approved | 0024 | none at this commit (see §3) |
| application_rejected | 0024 | none at this commit (see §3) |
| project_revision | 0024 | notifyProjectRevision (CASE) |
| award_reserved | 0024 | notifyAwardReserved |
| payment_paid | 0024 | notifyPaymentPaid |
| payout_held | 0024 | notifyPayoutHeld |
| wallet_changed | 0024 | notifyWalletChanged |
| project_quarantined | 0029 | notifyProjectEnforcement (CASE); direct insert `backend/vetting/flags.ts:294` |
| project_banned | 0029 | notifyProjectEnforcement (CASE); notifyVettingBanAudience |
| reinstatement_requested | 0029 | notifyProjectEnforcement (CASE) |
| project_reinstated | 0029 | notifyProjectEnforcement (CASE) |
| reinstatement_denied | 0029 | notifyProjectEnforcement (CASE) |
| reinstatement_review | 0029 | notifyReinstatementReviewers |
| payout_exception | 0029 | notifyPayoutException; notifyMonthlyUnderfunded |
| security_case | 0029 | notifySecurityCase; direct inserts `backend/security/report-intake.ts:507`, `backend/security/report-intake.ts:1170`, `backend/security/payments.ts:18`, `workers/notify/security.ts:348` |
| project_ready | 0063 | notifyProjectRevision (CASE) |
| project_scan_failed | 0063 | notifyProjectScanFailed |
| project_installation_lost | 0063 | notifySlopbotInstallationLost |
| security_report_received | 0063 | notifySecurityReportReceived |
| slopbot_appeal_review | 0065 | notifySlopbotAppeal; notifyPointsDispute |
| slopbot_scam_review | 0079 | notifySlopbotScamReview |

Semantics the table alone does not show, each from the writer's own
code and comments in `events.ts`:

- `payout_exception` has two writers with different keys and
  audiences: `notifyPayoutException` fires per held payout to the
  project's steward; `notifyMonthlyUnderfunded` fires once per
  project-month for an underfunded frozen month (its key carries no
  time, so coordinator retries cannot duplicate it).
- `slopbot_appeal_review` is also the stored kind for points-dispute
  notices: `notifyPointsDispute` writes the intake receipt and the
  final decision as two separate unread rows (the decision's event
  key carries a `:resolved` suffix), and `notifySlopbotAppeal` reads
  either the `slopbot_appeals` or the `points_disputes` table.
  There is no separate dispute kind.
- The `flags.ts` direct insert is the contributor-flag pause path:
  it writes `project_quarantined` to moderators with the `/admin`
  action path, reusing the `project-enforcement:` event-key prefix
  of the enforcement writer, so the two producers share one
  idempotency key space.
- The `workers/notify/security.ts:348` insert is the notify Worker's
  escalation notice: when a primary security notice was never
  acknowledged and its delivery failed or its acknowledgment
  deadline passed, the Worker inserts a fresh `security_case` row
  keyed `security-escalation:<outbox id>`.

### 3. Two stored kinds have no producer left

No production code at the pinned commit writes
`application_approved` or `application_rejected`: no writer in
`events.ts`, no direct insert, and the literals appear in production
code only in the presentation registry. The registry's own header
comment (`src/lib/notifications.ts:9–12`) says the two kinds "came
from the removed admin admission path and stay readable as history"
— they remain in the schema CHECK and in the title/action switches
so old rows still render, and test fixtures still insert them, but
nothing new can produce them.

### 4. A twenty-second kind that is never stored

`src/lib/notifications.ts` lists 22 kinds; the census diff against
the schema set is exactly one entry: `slopbot_appeal_resolved` is
listed but not storable, and every storable kind is listed. It is
derived in the inbox list query (`backend/notifications/handler.ts`,
the SELECT at line 197): a stored `slopbot_appeal_review` row is
presented as `slopbot_appeal_resolved` when a `slopbot_appeals` row
with the matching `slopbot-<appeal_key>` event key, or a
`points_disputes` row matching the key or its `:resolved` form, has
`resolved_at` set. The string appears in production code only in
that CASE expression and in the registry's list and switches.

### 5. The security outbox covers two kinds since 0063

PR #38 documented migration 0030's enqueue trigger as
security-case-only. The recreated trigger's WHEN clause, read by
the census from each migration that defines it:

| Migration | Trigger WHEN |
| --- | --- |
| 0030_security_notification_outbox.sql | `NEW.kind = 'security_case'` |
| 0063_account_closure_notification_events.sql | `NEW.kind IN ('security_case', 'security_report_received')` |
| 0065_slopbot_appeal_notifications.sql | `NEW.kind IN ('security_case', 'security_report_received')` |
| 0079_slopbot_scam_review_notifications.sql | `NEW.kind IN ('security_case', 'security_report_received')` |

Migration 0063's trigger body picks the template by kind —
`security-receipt-v1` for `security_report_received`,
`security-inbox-v1` otherwise — and its comment states the receipt
is informational and never waits for an acknowledgment, while the
case notice uses the acknowledged template with escalation. The
same migration's activity-mail trigger excludes both security kinds
from ordinary activity mail.

## Verification

- Census (needs a checkout of the public codebase at the pinned
  commit):
  `git clone https://github.com/SlopDotCash/slopdotcash && git checkout ced75d782d5836f60d84f46d50604f75a5852438`,
  then `python3 scripts/notification-kind-census.py <checkout>` from
  this repository. Observed: the chain table of §1 (final stored
  set 21), 17 writers, the five production direct inserts of §2, 25
  production call sites with at least one per writer, the registry
  diff of §4 (22 listed, `slopbot_appeal_resolved` listed but not
  storable, nothing storable unlisted), the two producer-less kinds
  of §3, and a final `CENSUS PASSED`.
- Tests: `python3 -m pytest tests/` — the three new tests in
  `tests/test_notification_kind_census.py` run the census over a
  synthetic fixture tree (chain growth, a shrinking chain rejected,
  a non-checkout argument rejected) and pass, and the existing
  selector tests still pass. In this environment pytest was not
  installed; the test functions were executed directly and all
  passed, with output preserved by the author.
- Manual cross-reads behind the script's output: `events.ts` read
  in full (the CASE writers, the shared INSERT/ONCE constants, the
  per-writer audience comments); the inbox SELECT in
  `backend/notifications/handler.ts` (the read-time derivation and
  the outbox subqueries); the header comment and kind list of
  `src/lib/notifications.ts`; the trigger bodies of migrations
  0030, 0063, 0065, and 0079.

## Notes

- Relation to other packets: PR #38 remains the reference for the
  0024–0030 era — transactional writes, consent-based activity
  email, and the SEC-16 delivery state machine; this packet cites
  it rather than repeating it, and adds only what it declared out
  of scope. PR #34 covers the inbox cursor and unread count, which
  are not touched here. The notify Worker's own scheduling and
  configuration are covered by PR #44 (Issue #13); this packet
  touches the Worker only where it produces notification rows.
- Limits: this is a static census of one pinned commit. The inbox
  is session-only data, so no live observation was possible or
  attempted, and no individual user's notifications were read.
  Call-site counts are textual occurrences of each writer's name in
  the production tree at the pin; a writer with a call site proves
  reachability in source, not a runtime execution count.
- The events.ts header frames the writers as "PRD NOT-01" inbox
  event statements (migrations 0024 and 0063); the PRD text itself
  was not re-quoted here.
