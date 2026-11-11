# Slopbot automatic closure — the eligibility gate

## Target

The Slopbot worker in the public SLOPCASH codebase
(`SlopDotCash/slopdotcash`, MIT), pinned at commit
`5330c937c4a896b576648512cb2bd053454a4b20`:

- `workers/slopbot/closure-eligibility.ts` — the per-item authority gate
  for automatic closure.
- `workers/slopbot/review.ts` — the caller (`closureEligibilityFor`),
  around lines 843–868 and 1207 at the pinned commit.

Area: Workers (Issue #13). This packet documents one mechanism only:
who Slopbot is allowed to close automatically. It does not document
Slopbot's review content, its value assessment, or the penalty amounts.

## Claim

Slopbot can automatically close a pull request only when every check in
one ordered gate passes: the author is known to be a non-maintainer, the
item is a pull request (never an issue), the author is a verified
slop.cash member, and the author's own authenticated Slop run recorded a
`pull_request_opened` event naming that exact pull request — and the
"Made via @slopdotcash" marker in the PR body is never an input to the
decision.

## Evidence

1. **The gate is a single function with five ordered checks.**
   `closureEligibility(evidence)` in
   `workers/slopbot/closure-eligibility.ts` returns on the first failing
   check, in this order:

   | # | Check that must hold | Reason returned when it fails |
   |---|---|---|
   | 1 | Author is not maintainer-exempt | maintainers are never closed by Slopbot |
   | 2 | Maintainer status is known (not unresolved) | maintainer status unknown |
   | 3 | Item kind is `pull_request` | only Slop-skill pull requests can be closed |
   | 4 | Author is a verified slop.cash member | author is not a verified slop.cash member |
   | 5 | A recorded Slop run exists for this pull request | no recorded Slop run for this pull request |

   When all five hold, the function returns eligible with the reason
   "verified member with a recorded Slop run for this pull request".

2. **Membership is a database fact about an immutable ID.**
   `isMember(db, githubId)` in the same file checks for a row in the
   `points_members` table matched by the author's GitHub ID — not by
   login, and not by anything written in the PR.

3. **A "recorded run" is the author's own session naming the exact PR.**
   `hasRecordedSkillRun(db, item)` joins `trace_runs` with
   `run_progress_events` and requires an event of kind
   `pull_request_opened` whose `github_object_id` equals the pull
   request's node ID, whose run belongs to the same GitHub user and the
   same project, and whose repository matches the project's registered
   repository ID, one of its aliases, or its current path (so a
   repository rename or transfer still matches). Because the record is
   created through the author's own authenticated Slop session, a
   copied footer, marker, or receipt cannot produce it for someone
   else. The same file states the design rule in its own comment: the
   "Made via @slopdotcash" marker is never an input, because anyone can
   paste it.

4. **The caller re-checks from fresh state, twice.**
   `closureEligibilityFor` in `workers/slopbot/review.ts` first runs the
   structural checks (1–3) with the database facts provisionally set to
   true, then looks up membership, and only if the author is a member
   looks up the recorded run, then runs the gate again on the full
   evidence. The function's own comment states it is run at routing and
   again immediately before every closure, from fresh GitHub and D1
   state. At routing (line ~1207 at the pinned commit) the gate is only
   consulted for contributor-scope registrations; a security-review
   scope is passed an always-ineligible result instead.

5. **Upstream tests exercise the recorded-run matching.**
   `workers/slopbot/closure-eligibility.test.ts` at the pinned commit
   contains two tests: one shows a recorded run still matches across a
   repository rename or transfer; the other shows sibling repositories
   are isolated and that a mismatched author or pull-request node ID is
   rejected.

6. **Independent cross-check.** The public Slop contributor skill
   (`https://slop.cash/SKILL.md`, section "How Slopbot reviews, labels
   and closes") states the same substantive conditions in prose: the
   author is a slop.cash member and not a project maintainer, and the
   author's own Slop session recorded `pull_request_opened` for that
   exact PR; "a copied footer never qualifies."

## Verification

Everything below was run on 2026-11-11 against the pinned commit.

1. Independent re-implementation check:
   `python3 scripts/closure_gate.py --verify-source`
   downloads `closure-eligibility.ts` at the pinned commit from the
   public repository, and confirms that all six decision reasons of the
   gate appear in it in the gate's branch order, and that the
   `points_members` lookup, the `pull_request_opened` event kind, and
   both database helper names are present. Observed: all checks passed.
2. Truth-table tests of the re-implementation:
   `python3 -m pytest tests/test_closure_gate.py` — 8 tests covering
   each single failing check, the all-pass case, and branch precedence
   (an exempt author fails on check 1 even when every later check would
   also fail; unresolved maintainer status fails on check 2 before
   membership is consulted). Observed: 8 passed.
3. Full test suite: `python3 -m pytest tests/` — the pre-existing
   `tests/test_verify_selector.py` still passes alongside the new
   tests. Observed: 12 passed.
4. Manual re-read: the gate, both database helpers, the caller, and
   both upstream tests were read in full at the pinned commit; every
   statement in the Evidence section traces to one of those files or to
   the cited skill section.

## Notes

- **Outer enablement is a separate switch.** Whether automatic closure
  is active at all, and whether a project enabled it in its settings,
  is decided outside this per-item gate (see the skill section cited in
  Evidence 6). This packet claims nothing about those switches; a PR
  can pass every check here and still never be closed if closure is not
  enabled for its project.
- **Advisory review is broader than closure.** The file's header
  describes closure eligibility as an authority boundary separate from
  the review itself: Slopbot can review items it could never close.
  This packet documents the closure boundary only.
- **Penalty amounts are out of scope here.** What happens after an
  eligible closure (labels, point debits by category) is a separate
  mechanism and is not claimed by this packet.
