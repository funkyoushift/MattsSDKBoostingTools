# MSBT Community Folders

A separate moderated library, with no connection to AFK relay credentials or live game actions.

## User workflow

Bookmarks → Community folders lets users search approved folders, open a share link, preview item names/codes, and import a separate local copy. Existing folders are never overwritten. Subfolders, order, duplicate entries, and exact code case are retained. The imported folder is available through the existing AFK bookmark selector.

Submit one of my folders sends only that selected subtree plus the explicitly entered title, creator display name, and description. Submissions are private until a reviewer approves them. My submissions exposes their status and permits withdrawal. Lost responses retry the same saved submission ID. Ownership keys are encrypted with Electron safeStorage and kept outside the installation, alongside the user's other MSBT data. Display names are self-reported, not authenticated identities. Revisions are new submissions and require review again.

The separate Developer portal uses Better Auth email/password accounts in an isolated sandboxed app window, with no Node access or app bridge exposed to hosted content. There is no shared reviewer key. Cookies are HttpOnly and secure on HTTPS, remembered sessions last 30 days and renew during use; users can uncheck Keep me signed in for a browser-session cookie, authentication is rate-limited, and mutating portal requests require the configured origin. New accounts have no team access. Email addresses are self-reported: the owner must confirm the actual account ID with the teammate before assigning access.

Roles: reviewer approves/rejects; editor also edits item names, codes and subfolders; admin also deletes online folders; owner also assigns/revokes roles. Role changes invalidate that user's sessions. The owner cannot demote themselves or create additional owners through the portal. Owner provisioning is an out-of-band database operation after confirming the account ID, never a first-signup-wins flow. Each mutation rechecks current permission in its atomic database batch and records an actor/action/target audit entry. Edits return the folder to pending; stale previews cannot overwrite changed contents. Online deletion removes stored folder contents but leaves the audit event and users' imported copies.

Password changes are supported. Email verification and forgotten-password recovery are not configured yet: an email delivery provider and verified sending domain must be connected before claiming those features or treating emails as verified identities. The service is deployed at https://msbt-community-library.screename53.workers.dev. Hosted acceptance checks passed on 2026-09-28 (see output/community-folders-review/hosted-receipt.json). The desktop integration is not released; owner account provisioning and email recovery setup remain.

## Limits and scope

- Lists are limited by a 16 MiB upload budget, not by the 70-item game delivery setting. Over-limit lists fail explicitly without truncation.
- D1 stores payloads in small chunks in an atomic batch; lists larger than the old 2 MiB bridge ceiling work.
- Codes are format-checked, not proven legitimate or safe to equip. Oversized codes remain visible as not currently deliverable. Reviewers see that count before approval.
- Public reads and writes have separate rate limits. A full pending queue rejects further uploads explicitly.
- Public pages and search return only approved entries. The service ignores supplied URLs and extra metadata. Share pages escape all user text. No CORS wildcard or generic fetch proxy is provided.
- Imported copies do not change when their source is later rejected or withdrawn. User bookmarks are never deleted by catalog moderation.

## Development and deployment

1. `npm ci`; `npm test` runs the real local D1 service and desktop client, including response loss/retry, privacy, moderation, and a >2 MiB list.
2. `npx wrangler deploy --dry-run` checks the worker bundle. `npx wrangler types` generates bindings.
3. Create a dedicated D1 database named `msbt-community-library` and replace the local placeholder database ID in `wrangler.jsonc` with its actual ID.
4. Apply `schema.sql` and generated `auth-schema.sql` to that database. Provision a random 32-byte hexadecimal `AUTH_SECRET` with `wrangler secret put`; never commit it or write it to logs. Set `PUBLIC_ORIGIN` to the exact HTTPS worker origin. Authentication fails closed when these are missing. Do not overwrite an existing auth schema; use migrations for future changes.
5. Deploy the independent worker. Verify the actual workers.dev hostname matches `DEFAULT_URL` in the Electron client before enabling the production UI.
6. Create the owner's account through Developer portal, verify their account ID, then insert that ID with role `owner` in the `team` table using authenticated operator access. Test account creation, role revocation, editing, deletion, and pending → approved → imported → withdrawn with clearly labeled test folders. Never publish a user's private folder as a test.

Desktop local integration uses `MSBT_TEST_COMMUNITY_URL=http://127.0.0.1:8789` only in an unpackaged app. Production builds ignore that override. Do not publish desktop/APK releases without a separate release request.
