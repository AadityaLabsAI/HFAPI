# HFAPI Production Readiness Checklist

This checklist is the release gate for deploying HFAPI as a Telegram-first Hugging Face assistant with the shared web control center.

## Before every release

- [ ] `python -m pip check` passes in a clean Python 3.12 environment.
- [ ] `python -m compileall -q bot tests *.py` passes.
- [ ] The tracked pytest suite passes without network or real credentials.
- [ ] No secrets, tokens, cookies, database URLs, or local state files are present in the diff.
- [ ] The Telegram bot and web control center use the same process and platform-assigned `PORT`.
- [ ] `/health` and `/health/json` return successfully after startup.
- [ ] `/api/status` exposes only non-sensitive operational metadata.
- [ ] Failure paths have user-safe messages and redact sensitive details from logs.
- [ ] Long Telegram responses are split safely and malformed markup can fall back to plain text.
- [ ] Background tasks are cancellable and do not create unbounded chat-message growth.

## Required runtime configuration

Configure secrets only in the deployment platform's secret store or environment settings:

- `TELEGRAM_BOT_TOKEN`
- `HF_TOKEN`
- `ENCRYPTION_SEED`
- `OWNER_ID` (when admin capabilities are enabled)
- Persistent storage configuration required by the selected provider

Never put these values in README files, screenshots, test fixtures, issues, logs, or the web UI.

## Deployment smoke test

1. Start the service with the platform-provided `PORT`.
2. Confirm the process stays alive and binds exactly to that port.
3. Open the root control-center page.
4. Verify the live status indicator changes from loading to healthy.
5. Request `/health/json` and confirm the response is valid JSON.
6. Send `/start`, `/status`, and a small text prompt in Telegram.
7. Exercise one failure path (for example, an unavailable provider) and confirm the bot returns a readable message without leaking implementation details.
8. Confirm logs contain no secret material.

## Operational rollback

- Roll back to the last commit that passed the Quality Gate.
- Preserve the deployment's secret configuration while reverting application code.
- Re-check `/health`, `/health/json`, and `/api/status` after rollback.
- Record the failure mode and add a deterministic regression test before re-deploying.

## Current engineering backlog

1. Replace remaining direct dynamic `reply_text(..., parse_mode=...)` calls with the shared safe transport helper.
2. Review progress-update tasks for message spam and cancellation races.
3. Extend safe transport coverage to edit/callback message paths.
4. Expand provider and storage failure-isolation tests.
5. Keep dependency and deployment guidance synchronized with the actual runtime.
