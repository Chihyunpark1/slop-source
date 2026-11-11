# Notify worker has no public route — it only answers https://notify.internal

## Target

The `notify` background worker (`slop-notify`) in the public SLOPCASH
codebase (`SlopDotCash/slopdotcash`, MIT): `workers/notify/`
(`index.ts`, `handler.ts`, `contracts.ts`, `wrangler.toml`, `README.md`)
and the service binding in the repo-root `wrangler.toml`. This packet
covers the worker's reachability only — what can call it and what it
answers — not what its emails say.

## Claim

The notify worker has no public route: it is reachable only through
the `SLOP_NOTIFY` service binding at `https://notify.internal`, and
every request to any other host or path is answered 404.

## Evidence

1. **The deployment config publishes nothing.** In
   `workers/notify/wrangler.toml` the worker is named `slop-notify`
   with `main = "index.ts"`, `workers_dev = false`,
   `preview_urls = false`, and no routes section (the file comments
   that the Pages app reaches it only through the `SLOP_NOTIFY`
   service binding). Its only outbound mail binding is
   `[[send_email]]` named `ADMIN_EMAIL`, and `[triggers]` sets
   `crons = []`, so the default profile has no schedule either.

2. **The only caller is the Pages service binding.** The repo-root
   `wrangler.toml` declares a `[[services]]` entry with
   `binding = "SLOP_NOTIFY"` and `service = "slop-notify"`, and
   `workers/notify/README.md` states the worker "has no public route
   and `workers_dev` is off" and that the caller is that service
   binding on the production Pages app.

3. **Every fetch route is gated on the internal origin.** In
   `workers/notify/index.ts` the three route groups are each guarded
   by `url.origin === "https://notify.internal"`: the email
   capability/verification/unsubscribe routes, the
   security-notifications dispatch/reconcile routes, and the
   activity-notifications eligibility/dispatch/reconcile routes.
   Anything that does not match falls through to
   `handleNotifyRequest`.

4. **Anything else is 404.** In `workers/notify/handler.ts`,
   `handleNotifyRequest` returns 404 unless the request is `https:`,
   its host is `NOTIFY_INTERNAL_HOST`, its path is one of the three
   notice paths, and it has no query string; a non-POST request to a
   valid path returns 405. The constants live in
   `workers/notify/contracts.ts`: `NOTIFY_INTERNAL_HOST =
   "notify.internal"` and the paths `/v1/project-applications`,
   `/v1/slopbot-spend`, and `/v1/slopbot-failure`.

## Verification

To re-check this claim:

1. Read `workers/notify/wrangler.toml`: confirm `workers_dev = false`,
   `preview_urls = false`, no routes section, and `crons = []`.
2. Search the worker for its origin gate:
   `grep -n 'notify.internal' workers/notify/index.ts` — expect three
   matches, one per route group.
3. Read `handleNotifyRequest` in `workers/notify/handler.ts`: confirm
   a request whose host is not `NOTIFY_INTERNAL_HOST` returns 404,
   and confirm the three accepted paths in
   `workers/notify/contracts.ts`.
4. Confirm the caller in the repo-root `wrangler.toml`:
   `grep -A1 'SLOP_NOTIFY' wrangler.toml` — expect
   `service = "slop-notify"`.

## Notes

- This packet says nothing about whether the worker is deployed, or
  whether any email is ever delivered: a 202 from the project
  application route means Cloudflare accepted the messages, not that
  an inbox received them (per the worker README).
- The default profile has no cron schedule; the five-minute drain
  schedule exists only for an explicitly selected mail pilot, applied
  by the protected release workflow — not covered here.
- This packet covers the `notify` worker only. The other 12 workers
  are not covered here.
