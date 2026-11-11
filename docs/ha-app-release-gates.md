# Home Assistant app release and deployment gates

Updated: 2026-11-11

## Code-review policy

The combined staging PR is **never** the deployment PR. Each application
change retains its individual PR, documentation, and live acceptance criteria.

This repository distributes a password manager, a Git service, a CI runner and
network access gateways. A green Docker build verifies only the image; it does
**not** certify state migration, authentication or production operation.

## Always-running required check

The workflow `.github/workflows/release-gate.yaml` is deliberately **not**
path-filtered. It checks version-pin/manifest consistency and runs lightweight
security tests for every PR, even a docs-only PR. This matters because GitHub
can keep path-filtered required checks in a pending state when their path
filters do not match.

After the CI workflow is verified on `main`, configure GitHub repository
Rulesets/Branch protection to require:

- Pull request before merge and at least one independent approval.
- The **`ha-apps-release-gate`** status check, with branch up to date
  before merge, as appropriate for the selected merge strategy.
- No force push/deletion on `main`; no routine admin bypass.
- Apply the rules to the default branch and require reviews after the last
  modification.

**Important:** Branch protection is a GitHub repository setting. This PR
cannot activate it merely by adding workflow files.

Existing, path-filtered workflows still run as **additional application-specific
checks** when they are relevant:

| Change | Additional check |
|---|---|
| Vaultwarden | `Vaultwarden image`: multi-arch build, snapshot-version consistency and SQLite backup test |
| Gitea MCP | `Home Assistant app build smoke tests`: protocol bridge tests and AMD64/ARM64 image builds |
| Gitea Runner | `Home Assistant app build smoke tests`: cleaned environment, CLI flags and both images |
| Cloudflared Origin Auth | `Home Assistant app build smoke tests`: imported upstream setup, auth guards, Nginx HTTP tests and both images |
| Local EMS | `Local EMS tests` and `Local EMS integration validation` |
| Gitea Server | Restore rehearsal and explicit migration approval, **not** just CI |

A reviewer should verify the applicable additional workflow **has completed
successfully at the head SHA** before merging. Do not treat the always-running
gate alone as sufficient for a runtime change.

## Planned controlled merge order

0. **#43** this always-running gate and release runbook, after review.
   Then **#44**: activate the required `ha-apps-release-gate` check and
   independent PR approvals on `main`. Verify the ruleset with a small
   PR before merging further runtime changes.
1. **#34** Runner CI trigger fix (no app runtime changes), after review.
2. **#38** Gitea migration plan (documentation only), after review.
   Then **#45** (Vaultwarden manual GHCR publishing) must be merged before #33:
   otherwise merging #33 would immediately publish the new image and
   overwrite the `:latest` tag. Configure required reviewers for
   the `vaultwarden-release` GitHub Environment separately.
3. **#33** Vaultwarden security update, only after a complete recoverable backup
   and test install (login, 2FA, attachments, organizations and rollback).
4. **#35** Cloudflared runtime update, validate each protected host and tunnel
   reconnect. Then **#42** security fail-closed follow-up; its branch is based
   on #35 and must be rebased/retargeted once #35 has merged.
5. **#36** Gitea Runner runtime update after running jobs finish, with one
   trusted live Actions checkout job and verified environment isolation.
6. **#37** Gitea MCP upgrade with tool refresh, read-only behavior, chunked
   file reads and a controlled binary upload test.
7. Gitea server **1.27 → 28** only after the isolated DB/data restore rehearsal
   and the acceptance gates in `docs/gitea-28-migration-plan.md`.

The exact order of independent apps may change if operational constraints
require it. **Do not merge PR #40**: it exists solely to validate the combined
candidate.

## Minimum operator evidence per app upgrade

Record the following for each production deployment:

- Date/time, responsible approver, target app version, image tag/digest, and
  the Git commit being deployed.
- Backup method, location, scope (including external database/storage), result
  of an actual restoration or integrity verification, and rollback version.
- Target HA installation and app configuration scope, without storing secrets
  or private URLs in this repository.
- Application-specific checklist, test outcomes, logs with sensitive values
  removed, and incident/rollback status.
- Confirmation that service was operational after restart (not just the
  container in "running" state).

Vaultwarden and Gitea are data-bearing services: reversing an image tag is
**not** a valid rollback after a schema migration without restoring the
matching state snapshot.

## Version consistency script

Run locally or in CI:

```sh
python3 scripts/verify_ha_app_versions.py
```

The script uses only the Python standard library and intentionally refuses
to guess unknown upstream Gitea image tags or the cloudflared executable
version from its separately versioned HA app.
