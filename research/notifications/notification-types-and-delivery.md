# Notifications — types, delivery, inbox

## Target

The notification features of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #14:
`migrations/0024_notifications.sql`,
`migrations/0029_notification_event_kinds.sql`,
`migrations/0030_security_notification_outbox.sql`,
`backend/notifications/`, `workers/notify/`, `src/Inbox.tsx`, and
`src/InboxEmail.tsx`.

## Claim

Every notification is first an inbox row written in the same D1
batch as the change that caused it; email is a separate,
consent-based layer on top — generic activity mail for users who
opted in, and a dedicated outbox with delivery evidence for
security-case notices only.

## Evidence

All references are to `SlopDotCash/slopdotcash` at the `development`
branch.

### 1. The inbox event kinds

Migration 0024 created the inbox with seven kinds; migration 0029
rebuilt the table and widened the `kind` CHECK to fifteen, adding
the project-enforcement path, private security cases, and the
maintainer payout exception:

| Group | Kinds |
| --- | --- |
| Project applications | `application_approved`, `application_rejected`, `project_revision` |
| Money | `award_reserved`, `payment_paid`, `payout_held`, `payout_exception` |
| Account | `wallet_changed` |
| Enforcement | `project_quarantined`, `project_banned`, `reinstatement_requested`, `project_reinstated`, `reinstatement_denied`, `reinstatement_review` |
| Security | `security_case` |

Writers are the `notify…` functions in
`backend/notifications/events.ts` (for example `notifyAwardReserved`,
`notifyPaymentPaid`, `notifyPayoutHeld`, `notifyWalletChanged`,
`notifyPayoutException`, `notifyProjectEnforcement`,
`notifySecurityCase`). Per the notify Worker's README, one source
transition produces one event per recipient, and notices report
outcomes and exceptions, not routine admissions.

### 2. How the inbox works

- **Transactional write.** Each writer inserts the notification row
  in the same D1 batch as its source change, so an event is never
  lost and never written for a change that did not commit
  (migration 0024's header comment explains why writers do this
  instead of an AFTER trigger).
- **Idempotent.** The primary key is `(event_key, recipient_github_id)`,
  so a replay of the same source event is a no-op.
- **Permanent and read-once.** A trigger forbids DELETE
  ("notifications are permanent") and a second trigger allows only
  the unread → read transition; every other column is immutable
  once written.
- **Minimal content.** A row carries kind, subject (≤ 80 chars),
  optional detail (≤ 1000 chars), an in-site `action_path`, and
  timestamps. Per migration 0024, no row carries a wallet address,
  a secret, or a private identity fact; the action path opens the
  page with the details. `src/Inbox.tsx` renders this inbox and its
  read state.

### 3. Delivery channel: email (optional activity mail)

- **Opt-in only, per verified destination.** `GET /api/v1/notifications/email`
  shows the signed-in user their verified address;
  `POST` with `enabled: true` and the current `destinationVersion`
  records explicit consent to that exact destination
  (`src/InboxEmail.tsx`, `backend/notifications/email.ts`,
  workers/notify README, "Optional activity email").
  Withdrawing consent suppresses queued activity mail, and no old
  inbox history is mailed after opt-in.
- **Queued atomically, re-checked before dispatch.** Migration 0033
  queues each new ordinary event only for an enabled preference.
  Before sending, the Worker re-checks the saved preference, the
  destination version, and that the recipient still belongs to the
  notice's audience (for example, a payout exception mails only the
  project's current steward; a reinstatement review only a current
  moderator). Mail to someone who left the audience is suppressed;
  the inbox row stays.
- **Generic content.** Activity messages contain no wallet address,
  amount, project, event identifier, or case data; they link to
  `/inbox`.
- **Exception.** Wallet-change account-security notices use a
  separate essential flag: they require a verified destination but
  do not use the optional activity preference.
- A separate route of the same Worker emails new project
  applications to operator admins: the recipients are the
  `ADMIN_EMAILS` Worker secret (1–10 addresses, never in the
  repository), the handler builds the RFC 5322 message itself, and
  callers cannot supply a recipient (workers/notify README,
  "Project-application route").

### 4. The security-notification outbox (SEC-16)

Migration 0030 adds `security_notification_outbox`, used only for
`kind = 'security_case'`:

- An AFTER INSERT trigger on `notifications` enqueues the outbox
  row in the same transaction as the inbox insert, keyed
  `UNIQUE(event_key, recipient_github_id, template_version)`
  (template `security-inbox-v1`), so a notification failure cannot
  lose or change the case receipt.
- Delivery is a state machine:
  `queued → retrying → sending → provider-accepted → delivered`,
  with `bounced`, `suppressed`, `exhausted`, and `ambiguous` as
  failure-side states; `attempts` and `next_attempt_at` drive the
  retries.
- Privacy: the destination is stored only as `destination_digest`,
  never as a raw address. Every state change is recorded in
  `security_notification_delivery_events`, an append-only evidence
  log (update and delete triggers both abort).
- Only `security_case` notices ask for an acknowledgment and
  escalate when one is missed (workers/notify README). Existing
  inbox notices are deliberately not mailed retrospectively
  (migration 0030, final comment).

### 5. Public data vs server-only data

- **In the repository / public:** the schema, the kind list, the
  writer functions, and the delivery rules above.
- **Server-only:** recipients' email addresses (held as private
  Worker configuration; only a digest reaches D1, and only for the
  security outbox), the `ADMIN_EMAILS` secret, and the contents of
  security cases — an inbox row for a case carries only the case id
  as its subject, not case details.

## Verification

- Read the three migrations in order (0024 → 0029 → 0030): the kind
  list, the permanence/read-once triggers, and the outbox schema
  and enqueue trigger are all stated there directly.
- Match the writer names in `backend/notifications/events.ts`
  against the kinds in section 1.
- Read the notify Worker README sections "Inbox events (NOT-01)",
  "Optional activity email (NOT-01)", and "Restricted private
  bounty pilot (SEC-16)" for the consent, re-check, and
  acknowledgment rules.
- Backend behaviour is covered by `backend/notifications/notifications.test.ts`
  and `backend/notifications/email.test.ts` in the same repository.

## Notes

- **Telegram: not found.** Issue #14 names Telegram as a channel to
  check. Searching the named sources (`backend/notifications/`,
  `workers/notify/`, `src/Inbox.tsx`, `src/InboxEmail.tsx`, and the
  notification migrations) finds no Telegram delivery; the only
  Telegram reference nearby is `migrations/0056_points_telegram.sql`,
  a points feature, not notification delivery. On the evidence
  named in the issue, the delivery channels are the in-app inbox
  and email.
- **Later migrations exist.** The kind CHECK was widened again
  after 0029 (for example migration 0063, account-closure events).
  This packet documents the state named in Issue #14 (0024/0029/
  0030) and does not enumerate the later additions.
- Amounts, wallet addresses, and case contents never appear in
  notification rows or activity mail by design; the inbox is a
  pointer to the page that holds the details.
