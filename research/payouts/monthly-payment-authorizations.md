# Monthly payment authorizations — the signed execution input is public, immutable, and the first one is permanent (Issue #3)

## Target

The monthly payment-authorization mechanism in the SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), as named in Issue #3 (Payouts &
bounties): the authorization table and the execution-cursor table
created by migration `migrations/0073_monthly_authorizations.sql`; the
publisher that signs and stores authorizations
(`backend/payments/monthly-publication.ts`, the publication function,
with the attestation types in `backend/payments/monthly-attestation-types.ts`);
the executor scheduler that consumes them
(`workers/payments/index.ts`, the monthly-commitment run); the public
read route documented in `backend/payments/README.md` (the
authorization and execution section); the formal model of the commit
cursor (`formal/models/rewards/monthly_commit_cursor.qnt`); and the
product rule in `docs/slop-product-requirements.md` (PRD section 6,
monthly payments).

## Claim

A funded month's signed execution input is published once as a public,
immutable authorization row, and only inside the month's admission
window: the attester signs the frozen allocation, the publisher checks
that the signed plan matches the frozen month exactly before storing
it, and the stored row can never be updated or deleted — while a
separate internal cursor, not the authorization, tracks which months
the executor has retried and which are complete.

## Evidence

All code references are to `SlopDotCash/slopdotcash` at the
`development` branch, commit `6db280ea`.

### 1. The authorization table holds one final signed input per month and network

Migration 0073 creates `monthly_payment_authorizations` with one row
per project, period, and network: the frozen snapshot's hash, the
authorization as JSON, and the publication time. A foreign key binds
the row to the frozen monthly run it belongs to, so an authorization
cannot name a month that was never frozen. The authorization must be
valid JSON. The row itself is final: an update is refused as
immutable and a delete as permanent. The migration's own header says
the point plainly: final ordinary monthly authorizations are public
execution inputs, not payment evidence.

### 2. Only a funded month, inside its window, with automatic payment on, gets published

The publisher revisits every frozen month whose obligations were
already created and that has at least one obligation, where no
authorization exists yet — or, for legacy EVM months, where the stored
plan is an EVM plan, so a reviewed upgrade can make an old all-at-once
allocation executable through V2 while the original row stays fixed.
Each candidate is then gated four ways: its network must be one the
deployment serves; the project must still have automatic monthly
payment switched on (the latest settings row, defaulting to on when
the owner never set one); and the current time must fall inside the
month's window — at or after the cutoff for that period, and before
the cutoff of the following period. A month outside its window, an
unfunded month, or a project whose owner turned automatic payment off
simply gets no authorization.

### 3. The signed plan must match the frozen month exactly

The attester signs the allocation and returns a plan plus a signature.
The publisher does not store it blindly: it checks that every field
of the requested month — project, period, network, snapshot hash —
appears unchanged in the signed plan's request, and rejects the result
as another month's allocation if any field differs. For an EVM V2
attempt it checks further: the reservation must be version 2, its
allocation digest must be the frozen snapshot hash with a `0x`
prefix, its whole gross must equal the plan's total gross, and its
source sequence must be a plain decimal string of at most 78 digits.
Any failure there rejects the attempt as invalid. When a legacy EVM
month gains a V2 attempt, the new authorization also carries the
original plan and signature alongside, so an uncertain legacy
transaction can still be reconciled if it wins admission.

### 4. The insert is atomic, idempotent, and the owner can still veto it at the last moment

The authorization is written by a single insert that selects from the
frozen run only when the run still has obligations and the automatic
setting is still on, with a conflict clause that does nothing if the
row already exists. The documentation notes why the check sits in the
statement rather than earlier: the owner may turn automatic payment
off after the attester's last check, so only the atomic insert can
decide whether the month publishes. Publishing the identical
authorization twice is a no-op — the publisher reads back the stored
row first and skips the write when it matches. If the stored row
differs after the insert and automatic payment is still on, the
publisher reports a publication conflict instead of silently keeping
a wrong row. And if the chain already admitted the month, the
publisher keeps the latest published attempt and moves on, so a
permissionless caller can resume from it.

### 5. The public read route serves the latest attempt without calling a signer

The read route for a project's month and network returns the latest
signed execution attempt and its publication time, without calling a
signer or any RPC. It exposes no private adjustment history. The read
goes through a view defined by the later attempts migration, which
returns the newest signed attempt when one exists and otherwise the
first authorization — so the public surface always shows the current
executable input, while the original authorization stays stored
underneath it.

### 6. The execution cursor is internal: fair retries and completion, not payment state

The same migration creates `monthly_payment_execution`, one row per
project, period, and network, holding the last attempt time and a
completion flag, keyed to the authorization it belongs to. The
scheduler's monthly-commitment run selects at most 50 incomplete
rows, least recently attempted first, ordered by last attempt, period,
and project. A row is a candidate when its period is the active one,
or when its plan is Solana or EVM V2 — a legacy EVM row is only a
candidate while its period is active. The run also pulls in any
current-period V2 roots that share a vault with an older selected V2
row, up to 50 extra, and sends the newest period first, because only
the newest month can be admitting and a leaf mined first would advance
the source sequence and invalidate the signed reservation. Each item's
attempt time is stamped before any work happens, so a failure still
counts as an attempt and the next pass tries the stalest row first.
The row is marked complete only on the executor's word: a completion
flag of true for a V2 month, or an already-committed result for a
legacy root. The documentation draws the line explicitly: the cursor
tracks fair retries and completed execution, not public payment state
— paid and reserved state still comes from finalized chain indexing.
The formal model of the commit cursor states the same rules: each
pass takes the K least recently attempted incomplete rows, stamps the
attempt before working, collects failures and still runs the next
item, and writes completion only on the executor's completion
evidence.

### 7. Publication is not a reservation or a payment

The documentation is explicit that publishing an authorization
reserves nothing and pays nobody. A project-operated or permissionless
executor must still submit the bounded commitment through its commit
service and reconcile the finalized results. Legacy EVM reserves its
awards in one transaction; EVM V2 reserves the remaining total and
then commits bounded proven leaves; Solana admits the total and then
commits or releases up to 16 proven leaves per invocation. An admitted
month stays resumable after opt-out or after its admission window
closes; only finalized completion retires it.

## Verification

Replayed the schema locally in a scratch SQLite database: all 128
migration files applied verbatim, in order, with zero failures, and
the foreign-key check came back empty. On a frozen month with one
obligation and automatic payment on, running the publisher's insert
statement verbatim stored exactly one authorization row; running it a
second time wrote nothing. An update of the stored row was refused as
immutable and a delete as permanent; an authorization naming an
unknown run was refused by the foreign key, and a non-JSON
authorization was refused by the validity check. The same insert
against a run whose obligations were never created wrote zero rows,
and against a project whose latest setting turned automatic payment
off wrote zero rows — the two guards the documentation attributes to
the atomic insert. The execution cursor accepted one row per month,
an upsert of a later attempt time kept a single row with the new
time, marking it complete flipped only the flag, and a cursor row
naming an unknown authorization was refused by its foreign key. The
public read view returned the published authorization and its
publication time. The payment test suite exercises the same table in
its monthly tests, seeding authorizations in fixtures and asserting
zero rows in the guard cases.

## Notes

The replacement-attempt table of migration 0083 — a new signed
attempt when source consumption invalidates an unadmitted EVM V2
signature — is a separate mechanism and is not covered here, beyond
the read view it defines. The chain-specific signing details (the
Solana v3 message and its frozen slot, the EVM executor's root and
leaf admission) are separate mechanisms as well. The packet covers
the shared publication and cursor rules; whether a published
authorization is ever surfaced to contributors through any channel
other than the documented read route was not found in the sources
checked.
