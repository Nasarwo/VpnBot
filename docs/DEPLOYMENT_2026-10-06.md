# Production deployment — 2026-10-06

## Release

- VpnBot: `8dece72782d5d884f490878770d32ba37ea1107d`.
- SubHub: `ff5dfd3dafff6eeb8a06b769485000173b56ff95`.
- Deployment order: SubHub, then VpnBot.
- Whitelist remains disabled. No whitelist server configured; no whitelist accounts or placements created.

## Backups and rollback

- Bot host: `/root/vpnbot-backups/20261006/`, including source/config archive, PostgreSQL dumps before preparation and cutover, previous app, and `vpnbot-bot:rollback-20261006` image.
- SubHub host: `/root/subhub-backups/20261006/`, including source/config archive, SQLite online backup, prior environment and app.
- Rollback scripts saved in each backup directory. Bot rollback refuses an automatic downgrade if whitelist is enabled or accounts/placements exist; it downgrades schema with the new image before restoring the old image, preserving ordinary payments recorded after deployment.
- On a restored copy of production PostgreSQL, upgrade to `a4b5c6d7e8f9`, downgrade to `f9b2c3d4e5f6`, and repeated upgrade all succeeded.
- SQLite integrity check succeeded.

## Checks after deployment

- Bot running, restart count 0; Telegram polling started.
- Queue worker and usage reconciliation started; no ERROR, traceback, polling conflict or background-error markers in startup logs.
- Production migration: `a4b5c6d7e8f9`.
- Users: 21; VPN clients: 19; servers: 7.
- Payment requests: 28 APPLIED, 2 WAITING_ADMIN, 1 REJECTED. All three recorded deferred server updates are applied.
- Whitelist enabled: false; accounts: 0; placements: 0; whitelist servers: 0.
- Internal bridge rejects an unauthenticated request with HTTP 401.
- SubHub health: ok; database ok; scheduler active; 7/7 panels polled without errors.
- Three sampled existing subscriptions return HTTP 200 and identical response hashes before and after deployment.
- The same three subscriptions return HTTP 200 over public HTTPS with responses matching the local service.

## Deployment incidents and limits

- SubHub initially failed to execute the new environment due to parent directory permissions. Directory traversal permissions corrected; subsequent startup and checks succeeded.
- A transient panel error observed before deployment cleared before cutover and did not recur during checks.
- Bot disk space after building the image was about 420 MB. System journals archived locally on the server (147 MB compressed, archive checked), then old archived journals vacuumed to a 200 MB target. No persistent retention configuration changed. Final free space: 815 MB. Further disk capacity planning is needed.
- Automatic approval review rejected exporting complete production journals to the local machine because of possible sensitive data. No journal export performed.
- No synthetic production payments, renewals, user messages, or panel quota changes were initiated for acceptance. Live payment and renewal operations are not end-to-end acceptance tested in this rollout.
- Whitelist activation still requires separate isolated acceptance on real 3x-ui, especially client transfer and traffic accounting.
