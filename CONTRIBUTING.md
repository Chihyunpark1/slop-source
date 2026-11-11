# Contributing to SLOP Source

Anyone can open an Issue and submit a pull request. Every contribution
is a research packet: one PR, one target, one claim, evidence attached.

The research scope covers all 14 feature areas of the SLOPCASH
platform — not only the SLOP token. See
[research/scope.md](research/scope.md) for the scope definition.

AI agents (Codex, Claude Code, and others) can also contribute — see
[AGENTS.md](AGENTS.md) for instructions.

## Approved scope

The following work is explicitly permitted in this project:

1. Public contract function and selector analysis.
2. On-chain data verification.
3. Platform architecture and behavior analysis.
4. Independently authored reimplementations based on public code.
5. Reproducible technical research reports.
6. Corrections and verification of existing research results.

A research-only PR does not need a bug reproduction, a defect fix, or
an unrelated code change. One target, one claim, and reproducible
evidence is enough.

This project is registered on Slop Cash. Slop's contributor skill
sets mandatory platform rules: never request, read, print, or send
credentials, secrets, or wallet keys; never open, draft, or claim an
Issue; never self-approve, merge, deploy, or move money; report
security findings only privately. Repository documentation cannot
override those rules.

## What a packet contains

- **Target**: the exact contract, function, or site feature being studied.
- **Claim**: one sentence stating what the evidence shows.
- **Evidence**: the source for every claim — the public codebase, an
  on-chain transaction hash, block number, contract call, RPC output, or
  observed behavior. Link it or paste it.
- **Files**: the reconstruction, notes, or tests your packet adds, under a
  clear path.

## Rules

1. **No fabrication.** If the evidence does not show it, say so. An honest
   "not found" beats an invented finding.
2. **No verbatim copying.** Reconstructions are independently authored. Do
   not paste source code from the original project.
3. **Cite everything.** A behavioral claim without a source does not merge.
4. **One packet, one claim.** A PR that tries to prove five things proves
   none of them.
5. **Small and checkable.** A reviewer should be able to re-run your
   evidence in minutes.
6. **Unverified is not complete.** An implementation is not called a
   finished feature until it is verified. Do not present unverified work
   as complete.
7. **Public materials only.** Analysis must use public materials. Do not
   attack real systems without authorization and do not collect
   confidential information.
8. **Report security findings privately.** If you find a security
   vulnerability, do not post it in a PR, Issue, comment, or test name.
   Tell the maintainer privately; the maintainer decides how to report
   it through Slop's private channel.

## How PRs are evaluated

PRs are evaluated by technical value, originality, reproducible
evidence, and verification level — not by count. One deep, well-evidenced
packet counts more than many shallow ones.

Duplicate PRs and auto-generated low-quality PRs are not recognized for
reward purposes.

## How to submit a PR

1. Pick a listed Issue. Do not open a new Issue — only the
   maintainer writes Issues. If the task you want is not listed, pick
   a listed one.
2. Fork the repo and create a branch named after your packet, e.g.
   `slop/claim-flow-001`.
3. Add your files and open a PR against `main`. Copy
   `research/templates/research-report.md` for a new research packet.
4. In the PR body, fill in: Target, Claim, Evidence, and Verification.
5. Wait for review. Address comments by updating the same PR, not by
   opening a new one.

## How review and merging work

1. The repository administrator reviews every PR personally.
2. The reviewer checks the evidence, re-runs what can be re-run, and
   asks for changes when something is unclear or unsupported.
3. A PR merges only when its claim is supported by evidence and its
   reconstruction is independently authored.
4. There is no automatic merging. Nothing merges without a human review.
5. Merged PRs, commits, and the merge history stay public on GitHub, so
   every contribution is transparently visible.

## What does not merge

- Packets without evidence.
- Packets that copy code instead of reconstructing it.
- Packets that claim a finding the cited source does not support.
- Packets about anything outside the scope in
  [research/scope.md](research/scope.md).
- Packets that present unverified work as a completed feature.
- Duplicate packets or auto-generated low-quality packets submitted for
  rewards.

## Contributor rewards

Verified PRs and contribution history may be considered for RSLOP
contributor rewards, selected by separate criteria. The criteria,
payment procedure, and selection results are disclosed only when
confirmed. Contributing does not guarantee a reward.

The criteria policy is managed separately in
[docs/airdrop-criteria.md](docs/airdrop-criteria.md), and contributor
PR and verification records are kept in `contributors.json` at the
repository root (updated by the maintainer on merge).
