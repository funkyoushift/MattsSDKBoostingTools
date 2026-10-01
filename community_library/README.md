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
- Public pages and search return only approved entries. The service ignores supplied URLs and extra metadata. Share pages escape all user text. The public v1 read API allows anonymous browser access from any origin; private routes have no wildcard CORS. No generic fetch proxy is provided.
- Imported copies do not change when their source is later rejected or withdrawn. User bookmarks are never deleted by catalog moderation.

## Development and deployment

1. `npm ci`; `npm test` runs the real local D1 service and desktop client, including response loss/retry, privacy, moderation, and a >2 MiB list.
2. `npx wrangler deploy --dry-run` checks the worker bundle. `npx wrangler types` generates bindings.
3. Create a dedicated D1 database named `msbt-community-library` and replace the local placeholder database ID in `wrangler.jsonc` with its actual ID.
4. Apply `schema.sql` and generated `auth-schema.sql` to that database. Provision a random 32-byte hexadecimal `AUTH_SECRET` with `wrangler secret put`; never commit it or write it to logs. Set `PUBLIC_ORIGIN` to the exact HTTPS worker origin. Authentication fails closed when these are missing. Do not overwrite an existing auth schema; use migrations for future changes.
5. Deploy the independent worker. Verify the actual workers.dev hostname matches `DEFAULT_URL` in the Electron client before enabling the production UI.
6. Create the owner's account through Developer portal, verify their account ID, then insert that ID with role `owner` in the `team` table using authenticated operator access. Test account creation, role revocation, editing, deletion, and pending → approved → imported → withdrawn with clearly labeled test folders. Never publish a user's private folder as a test.

Desktop local integration uses `MSBT_TEST_COMMUNITY_URL=http://127.0.0.1:8789` only in an unpackaged app. Production builds ignore that override. Do not publish desktop/APK releases without a separate release request.

## Website access

The website's `/community/` page uses anonymous GET requests to `/folders` and
`/folders/:id`. Only `https://www.funkyoushift.com`, `https://funkyoushift.com`,
and `https://funkyoushift.github.io` receive public-read CORS headers. No cookies,
submission writes, private ownership routes, or moderation routes are exposed
cross-origin. Deploy this service update before publishing the website page.
The page verifies each folder digest before enabling copy/download actions.

## Public integration API

`GET /api/v1/folders?q=...&offset=0` and `GET /api/v1/folders/:id` expose the
same approved data as the legacy public routes. These two versioned routes have
anonymous wildcard CORS, no credential sharing, and no write operations.
`GET /api/v1/openapi.json` documents the contract. OPTIONS supports public GET
preflight only. Existing SDK/desktop URLs remain supported. Admin authentication,
role assignment, submissions and moderation are not part of this public API.

Website documentation at `/community/api.html` includes a downloadable integration
kit and dependency-free JavaScript/Python clients. No npm or PyPI publication is
required. The clients verify folder digests and preserve serial case/duplicates.

## Screenshots and GZO titles

Apply `image-schema.sql` once to an existing database before deploying this update (new databases use `schema.sql`). Item screenshots are separate from canonical folder JSON and its digest. Uploads are JPEG, at most 512 KiB and 2000 pixels per side, up to 20 per loadout. The website accepts PNG/JPEG/WebP and resizes them. Images remain private until approval; replacing/removing an image returns the loadout to pending. Review requests include `media_revision` so an old preview cannot approve new images.

`GET /folders/:id` and `/api/v1/folders/:id` return `images` and `item_details`, keyed by SHA-256 of the complete case-sensitive UTF-8 serial. Details include available GZO title, creator/source, and screenshot URL. Uploaded screenshots take priority. These fields do not change the folder digest. Desktop imports preserve the saved label as `source_name` and bind images to `image_serial_hash`; changed codes cannot retain an unrelated picture.

`POST /submissions/:id/images` accepts the same private ownership bearer key (or an editor's same-origin portal session), JSON `{digest, media_revision, images:[{id,serial,data}], remove:[]}`. Each `id` is UUIDv4; `data` is base64 JPEG without a data-URL prefix. Reuse IDs and payloads when retrying. Fetch current submission status for its revision. `GET /images/:id` serves approved images publicly, otherwise only the owner/reviewer. Do not put ownership keys in image URLs.

Refresh the GZO snapshot with `node refresh_gzo_images.mjs [website-index-path]`. Exact full-code hashes only; conflicting titles and images are omitted independently. GZO supplies presentation metadata, not proof of native game item-card behavior. Missing matches retain saved names. Screenshot links in imported copies remain online references and can become unavailable if the source is withdrawn.
