# Model Autopsy — zero-cost encrypted PostgreSQL application backup

This workflow is separate from the unmerged production hardening PR #7. It does **not**
alter Supabase data, perform migrations, deploy anything or provision paid resources.

## What it backs up

- The 8 application tables: datasets, model_adapters, experiments, experiment_runs,
  experiment_results, failed_samples, artifact_manifests and artifact_references
- The `public.alembic_version` migration revision

It creates a PostgreSQL **custom-format logical dump**, restores it into a temporary
PostgreSQL 17 database on the GitHub runner, compares counts for all eight application
tables, encrypts the verified dump using AES-256 with PBKDF2, and uploads **only encrypted
files** to an Actions artifact retained for **7 days**.

It does **not** back up Cloudflare R2 objects, the `auth` schema, Supabase platform
configuration or other schemas. Currently the Supabase project has no Auth users, but
user identity data should be separately backed up after accounts are created.

## One-time configuration (GitHub repository owner only)

GitHub repository → **Settings → Secrets and variables → Actions → New repository secret**.

1. `SUPABASE_DATABASE_URL`: standard PostgreSQL URL from the existing Supabase
   dashboard → **Connect**, preferably its IPv4-compatible **Session Pooler**.
   Must start with `postgresql://` or `postgres://`, NOT `postgresql+asyncpg://`.
   Use credentials authorized for all nine application tables. Do not copy the value
   into a chat or issue and do not commit it.
2. `MODEL_AUTOPSY_BACKUP_PASSPHRASE`: a unique randomly generated passphrase
   (at least 24 characters). Save it in a secure password manager; losing it means
   the encrypted backup cannot be decrypted. **Never paste this passphrase into chat.**

The assistant cannot read, create or recover these GitHub repository secrets using
the currently connected GitHub permissions. These two settings are the remaining
unavoidable user account actions.

## Run

On GitHub go to **Actions → Secure Supabase application backup (on demand) →
Run workflow**. Select the `main` branch (the workflow is installed on `main`).
Wait for the `encrypted-backup-and-restore-check` job to turn green. Its success
requires a complete dump, successful scratch restoration, matching row counts,
encryption and a decrypt/cmp check.

Download the artifact **model-autopsy-supabase-encrypted-backup** from the job
before the 7-day retention ends. Keep it in private offline storage. Verify its
ciphertext hash using `sha256sum -c model-autopsy.dump.enc.sha256` in the
artifact's directory.

To decrypt locally, install OpenSSL and set `BACKUP_PASSPHRASE` securely as an
environment variable, then run:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 -iter 300000 \
  -in model-autopsy.dump.enc -out model-autopsy.dump \
  -pass env:BACKUP_PASSPHRASE
pg_restore --list model-autopsy.dump
```

Never publish the plaintext dump. Prefer storing both the encrypted dump and a
securely kept, separate recovery password. The GitHub Actions artifact is *not*
permanent backup storage.

## Before migration 002–004

1. Workflow **green** and encrypted artifact securely downloaded.
2. Existing R2 objects separately inventoried and backed up. A database backup
   alone cannot restore uploaded datasets and artifact file content.
3. Production Supabase RLS policies and current revision checked against the PR.
4. A dry run of migrations against isolated PostgreSQL 17 must pass (GitHub CI).
5. Verify the Supabase project signing uses the asymmetric JWT algorithms supported
   by the FastAPI backend, and confirm the actual existing R2 bucket configuration.
6. Only then consider applying migration with a controlled rollback plan. Do not
   merge PR #7 or trigger Render auto-deploy until the database has the required
   schema and service environment variables.

This workflow intentionally uses GitHub-hosted runner resources and a temporary
Docker container, not a Render paid worker or paid Supabase branching. Usage remains
subject to your GitHub plan's included Actions minutes and artifact quotas.
