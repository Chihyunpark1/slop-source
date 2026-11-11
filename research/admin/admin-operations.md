# Admin & operations — how vetting, moderation, and cycle operations actually run

## Target

Issue #6 — the operator side of the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT) at development commit
`ced75d782d5836f60d84f46d50604f75a5852438`: the vetting pipeline
(`backend/vetting/`, `workers/vetting/`, `src/AdminVetting.tsx`,
`src/VettingEvidence.tsx`), the moderation and enforcement decision
path (`src/AdminProjectEnforcement.tsx`, `backend/projects/`), pending
project applications (`src/PendingProjectApplications.tsx`), the admin
shell (`src/Admin.tsx`), and the monthly cycle operations
(`.github/workflows/monthly-rewards.yml`, `backend/payments/`).

This packet covers operator actions. The cycle pages, standings, and
snapshots themselves are Issue #9 (the closed-cycle evidence gate for
reward proposals is already covered by the open packet on
`src/lib/reward-cycle.ts`), and the registry and the project-side
representation of restrictions are covered by the Projects packet
(Issue #1).

## Claim

Every operator action that can clear, restrict, or pay a project runs
through the same gate shape — a named human role or a signed machine
result, a written reason with an evidence reference, a server-computed
preview or an exact content pin, and an append-only record — and the
public footprint of the vetting gate, read live on 2026-11-11, shows
all 18 skill-publishing projects cleared (8 by a retained admission
scan, 7 by the existing-project exemption, 3 by an owner-approved
exemption) with zero projects under a public restriction.

## Evidence

### 1. Vetting: application, scan, decision

- A project enters the pipeline by self-service creation, not by an
  admin decision: `POST /api/v1/projects` "creates a paused project at
  once … queues its first scan and returns the setup status"
  (`backend/projects/README.md`, routes table). Setup then derives one
  status per project from the installation, authority, and scan checks;
  a project activates only after complete setup, Slopbot installation,
  current GitHub authority, and a clean security scan (same file,
  "Self-service setup").
- The backend half (`backend/vetting/`) stores the scanner's signed
  results, queues scans, records contributor flags, and enforces the
  gate; it fails closed when the service is absent
  (`backend/vetting/README.md`, introduction). Assessments are one scan
  of one exact project revision at one exact integration-branch commit
  and skill-template digest, with states `pending`, `incomplete`,
  `clean`, `malicious`, exactly one allowed update (pending → result),
  and no deletes (same file, "Tables"; migration
  `0025_community_security_vetting.sql`). Quarantined artifacts are
  immutable rows and are `released` only with a clean analysis.
- Clearance is a seven-state gate (`unscanned`, `unverified`, `stale`,
  `queued`, `quarantined`, `cleared`, `banned`); only `cleared` allows
  skills, discovery, and activation, subject to registry restrictions
  (`backend/vetting/README.md:27`, "Clearance"). One successful
  admission scan persists for routine later changes to the same
  immutable repository; the public clearance names its basis
  `admission` and the originally assessed revision, and does not claim
  later content was scanned. Explicit investigations still control:
  pending or incomplete results block, confirmed malice requires the
  independent decision below.
- The scanner is an external signed service (`workers/vetting/`). One
  queued assessment flows through six steps (`workers/vetting/README.md:81`):
  acquire the exact queued commit and template inputs without execution;
  sort files into six surfaces (`source`, `manifests`, `dependencies`,
  `installScripts`, `downloads`, `agentInstructions`) and run the
  deterministic checks for five threats (`wallet-drainer`,
  `credential-theft`, `secret-exfiltration`, `unsafe-execution`,
  `prompt-injection`); run the primary model review; run a specialist
  review only when the result is ambiguous or high risk; compose the
  disposition; retain the private evidence and publish the result once.
  A pass runs automatically: it calls the signed
  `POST /api/v1/vetting/refresh` (which queues initial admission and
  required flag recovery), reads the signed queue, and processes each
  pending assessment in queue order (same file, "Scan service",
  line 132). The operator runs it on a private host with an Ed25519
  signing key; results are accepted only with a valid signature over
  method, path, timestamp, and body hash
  (`backend/vetting/README.md`, "Service signature"). A model label
  alone never confirms malice: `malicious` requires a confirmation
  with basis `reproducible-behavior` or `verified-source-evidence`, a
  rule id, and evidence references (same file, "Result contract").
- The admin view of all this is the project's security section
  (`src/AdminVetting.tsx:3-10`): it shows each project's admission
  clearance, the restricted scan results and quarantine records, and
  active contributor flags. Queueing a scan by hand requires a written
  reason (the form refuses an empty one) and posts to
  `admin/vetting/assessments` with the project id, revision, and reason
  (same file, lines 395-451); `GET /api/v1/admin/vetting` returns the
  service state, every project's clearance, and full results
  (`backend/vetting/README.md:125-126`). When the scanner service is
  not configured, the view says so and offers no scan control.
- Two human overrides exist beside the scan. An administrator may
  record an explicit owner-approved admission exemption through
  `POST /api/v1/admin/vetting/exemptions` with the current project id,
  revision, reason, decision reference, and `confirmation: true`; it
  is a separate audited record, never a fabricated assessment, cannot
  move to another repository or steward, and its revocation needs a
  fresh human confirmation (`backend/vetting/README.md`, "Explicit
  owner-approved admission exemptions"; the form is
  `src/AdminVetting.tsx`, `AdmissionExemptionForm`). The older
  migration-0075 existing-project exemption is permanent and separate,
  and is never displayed as a passed scan (`src/AdminVetting.tsx:106`).

### 2. Moderation and enforcement decisions

- Contributor flags are the one restriction that needs no moderator:
  a member files one active flag per project with a category and
  20–4,000 characters of evidence, after a standing check read from
  GitHub at filing time (account at least 30 days old, at least one
  accepted contribution, not the steward or a repository insider). In
  the same transaction as the second distinct active reporter's flag,
  the platform appends a `quarantine` enforcement record issued by
  `contributor-flags`, notifies the administrators, moderators,
  applicant, and steward, purges cached skills and discovery, and
  queues a fresh scan. A database trigger refuses a flag pause without
  two distinct active reporters, and a single flag changes nothing
  (`backend/vetting/README.md:222`, "Two-contributor flags"). A clean
  fresh scan requested after the pause reinstates a flag-only pause
  automatically; the flags it was queued with are the ones it resolves.
- Every other restriction is a moderator decision made in two steps.
  `POST /api/v1/admin/projects/:id/enforcement-preview` (moderator)
  "plans an enforcement action and writes nothing";
  `POST /api/v1/admin/projects/:id/enforcement` records the previewed
  action with its reason, evidence reference, expected revision, and
  expected sequence (`backend/projects/README.md:62-63`). The panel
  (`src/AdminProjectEnforcement.tsx:1-8`) offers Quarantine, Ban
  project, Request reinstatement, Reinstate after review, Reinstate
  selected accounts, and Deny reinstatement (lines 38-45); every action
  needs a reason (≤1,000 characters) and an evidence link or case ID,
  and the preview shows the exact before → after restriction state,
  revision, status and listing tier, and any maintainer account bans
  before the moderator confirms. Any change to the request invalidates
  the preview and forces a new one. Records land in the append-only
  `project_enforcements` table with the audit fields (actor, role,
  reason, evidence reference, before/after revision, decision source,
  result); triggers refuse updates, deletes, and sequence gaps
  (`backend/projects/README.md`, "Tables").
- Independence is enforced, not conventional: the panel lists the
  actors who placed a restriction under "Restricted by · cannot decide
  appeal", and reinstatement "needs an open reinstatement request and
  a moderator who did not place the restriction", with a clean scan of
  the current restricted revision at the live branch head and current
  template required at both preview and confirmation, or the request
  fails with `vetting_required` (`backend/projects/README.md`,
  enforcement passage). A confirmed malicious signed result records a
  Ban by itself, naming the signing-key digest as issuer — never a
  fabricated GitHub account — and then waits: a moderator either
  reinstates through the appeal path or chooses "Ban project and
  maintainer", selecting the responsible accoun
...[truncated 6372 chars]