# Document the Inbox cursor and unread count

Refs #14

## Target

Upstream notifications behavior in [the primary source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/notifications/handler.ts#L173-L265) at commit 7dc83b504627c70eb6d1f0d1950b40aad3006bf8.

## Claim

The Inbox paginates visible notices by event position while counting unread notices across the recipient's visible history.

## Evidence

The listing query binds the signed-in GitHub actor and orders notices by descending source time, with the event key ascending as the tie-breaker. The continuation cursor contains the final returned source time and event key. The next query accepts an older source time or a greater event key at the same time. [Implementation](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/notifications/handler.ts#L173-L265)

The listing fetches one extra row to determine whether to return a continuation cursor. The unread query uses the recipient and visibility filters without the continuation predicate, so changing pages does not change the scope of the unread count. [Supporting source](https://github.com/SlopDotCash/slopdotcash/blob/7dc83b504627c70eb6d1f0d1950b40aad3006bf8/backend/notifications/notifications.test.ts)

## Verification

Compare the cursor predicate against the ORDER BY clause. For three visible notices at the same timestamp with keys A, B and C, a cursor at B leaves C eligible. The separate count still includes any unread A or B. This packet was verified by static source inspection. Upstream tests and live services were outside the verification.
