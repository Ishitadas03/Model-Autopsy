# Release verification — 2026-11-16

## Status

The production-hardening branch is still staged in PR #7. These changes do not
apply migrations, change live secrets, merge to main, or create paid resources.
The ₹0 architecture is suitable for small demonstration workloads; sleeping
Render web instances cannot provide continuous ML processing.

## Defects fixed in this verification pass

- Uploaded CSV baseline and generic execution called nonexistent `get_object`.
  Both now read the registered storage key through a shared loader, preserve
  case-sensitive dataset IDs, and verify the recorded SHA-256. The queue carries
  the registered key and checksum; it does not select unrelated local CSVs.
- Baseline training now runs outside the ASGI event loop, so it does not block
  worker heartbeats. A mismatched task or target is rejected.
- Cancelling a child task no longer cancels the queue poller. Timeout and worker
  shutdown produce FAILED states, including per-seed runs. Expired/foreign
  leases cannot commit results or overwrite another worker's status. User
  cancellation commits before subprocess termination to avoid a failure race.
- Dynamic artifact downloads now resolve committed manifests, enforce tenant
  access, verify size/SHA-256, and return private, non-cacheable bytes. No
  process-local output is substituted for required R2 content. Missing or
  corrupted durable artifacts fail with 503. Historical E003 benchmark routes
  remain separate from user experiment downloads.
- R2-required storage reads/deletes/listing cannot silently fall back to local
  files. Object listing paginates beyond 1,000 keys. Local paths reject traversal,
  ambiguous keys, and symlink escapes; concurrent downloads use unique temp files.
- JWT verification tests exercise real ES256/RS256 signatures, invalid signature,
  issuer/audience/role/subject, missing claims, expiry and HMAC rejection.
  JWKS connectivity failure returns 503 rather than invalidating a valid session.

## Local evidence

- Backend: **129 tests passed** (Python 3.12).
- ML engine: **116 tests passed**; seven existing numerical warnings in the
  research tests, including constant inputs and tiny-sample statistics.
- New integration coverage: upload an 80-row CSV through HTTP, baseline training,
  queue claim, real ML subprocess, completed results, four artifact downloads,
  SHA-256 checks, simulated remote retrieval after deleting local outputs,
  corrupted/missing artifact rejection, and second-user access rejection.
  Both classification and regression run through this path.
- Storage provider calls are simulated in remote-recovery tests. Those tests do
  **not** establish that the real R2 bucket/credentials are healthy.
- JWT signatures are real, but signing keys are local fixtures. These tests do
  **not** establish compatibility with the live Supabase project's signer.
- SQLite tests cover worker lifecycle. PostgreSQL locking/RLS/migrations and
  frontend build/typecheck/unit tests must pass on the latest GitHub Actions SHA.

## Outstanding release gates

1. **Owner credential setup:** configure `SUPABASE_DATABASE_URL` and
   `MODEL_AUTOPSY_BACKUP_PASSPHRASE` directly in GitHub Actions secrets. Do not put
   either in chat, Git, issues, logs or PR descriptions. Run the installed
   `backup-supabase.yml` workflow from main and download the encrypted artifact
   before its seven-day expiry. Keep the passphrase separately.
2. **Backup scope:** that workflow backs up nine named application/migration
   tables and verifies their restoration in disposable PostgreSQL. It is not a
   full Supabase project backup: auth users, other schemas, provider settings,
   and R2 object bytes are not included. Preserve those separately as applicable.
3. **Actual restored-data rehearsal:** the previous CI test migrates synthetic
   representative rows, not a restored production backup. Rehearse revisions
   002–004 against the independently restored actual application data. Preserve
   row counts and keep unclaimed legacy owner IDs NULL.
4. **R2 recovery:** independently back up the existing bucket and verify object
   checksums/restoration. Retain object references from the database backup.
5. **Live environment:** verify Supabase asymmetric signing, direct PostgREST
   RLS isolation, actual Render/Vercel variables, `/api/ready`, and two real user
   sessions. Use staging data for classification/regression and cancel/restart
   checks. Confirm downloads still work after process-local artifacts disappear.
6. **Release:** only after those gates pass, apply the reviewed migration and
   deploy the matching code/configuration. Verify deployment SHAs, service logs,
   small concurrent-load behavior and free-tier quotas.

No backup success or live deployment is claimed by this document.
