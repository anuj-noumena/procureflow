# Implementation and verification record

Verification date: 25 November 2026. The runs used x86-64 Linux, Python 3.12.14, Node 22.16.0, npm 10.9.2 and PostgreSQL 16.14. The execution host ran Debian 13. Ubuntu 24.04 is the requested compatibility target; an Ubuntu-specific run and a resource-capped 4-core/16-GB run remain unverified.

## Final checks

| Check | Observed result | Failed | Skipped |
|---|---|---:|---:|
| Backend, SQLite in clean source tree | `35 passed in 15.20s` | 0 | 0 |
| Same backend suite, PostgreSQL 16.14 | `35 passed in 18.82s` | 0 | 0 |
| Vitest, clean source tree | `Test Files 2 passed (2)`, `Tests 8 passed (8)` | 0 | 0 |
| Playwright, local Chromium, clean source tree | `3 passed (11.9s)` | 0 | 0 |
| Vue type check and Vite production build | `built in 2.43s` | 0 | — |
| Alembic upgrade, drift check, downgrade to base, upgrade and drift check | Passed on SQLite and PostgreSQL as part of Pytest | 0 | 0 |
| Development seed on both databases | First run seeded 2 workspaces. Second run seeded 0. | 0 | 0 |
| Backend health, offline API reference, Vite root, Vite-proxied API health | HTTP 200 for all four URLs | 0 | — |

The 35 backend cases are the same suite executed against each database engine. Assertions include independent database-session reads, rollback after SQL has flushed, database rejection of a cross-tenant foreign key, membership revocation, single-winner concurrent commands and final event history.

For the clean-install check, the tracked source was exported into an empty directory. Python installed the locked dependencies from a local wheel directory using `--no-index`. npm installed from its populated cache with `npm ci --offline`. The clean tree was initialized, seeded twice, built, started and tested. Runtime dependencies, caches, generated credentials and databases are installation-local. The source archive includes the lockfiles and setup instructions.

The three browser journeys used real backend endpoints and database writes. They covered a requester submitting and a different reviewer approving, supplier creation and deactivation, and mobile navigation with catalog creation. The browser blocked external requests in all three tests.

## Stage record

| Stage | Files introduced or changed | Decision, executed check and next work |
|---|---|---|
| 1 · Foundation | `backend/app/core`, `app/main.py`, Alembic environment and baseline; frontend manifest, Vite config and initial Vue entry | One request-scoped SQLAlchemy transaction. SQLite upgraded to the baseline, the ASGI app returned `{"status":"ok"}`, Vite served its root and the initial production build reported `built in 602ms`. Identity followed. |
| 2 · Organization and identity | `modules/organizations`, `modules/identity`, dependencies, migration 0002 and identity tests | Global accounts with tenant-specific active memberships and roles. `2 passed, 2 warnings`. Login scope and revocation were exercised. Directory modules followed. |
| 3 · Supplier and catalog | `modules/suppliers`, `modules/catalog`, migration 0003, directory tests, Vue login, session and directory screens | Normalized tenant uniqueness and status-based deactivation preserve supplier references. `4 passed, 3 warnings`. Node 22 production build completed in 2.00s. Requisition drafting followed. |
| 4 · Requisitions | `modules/requisitions`, migration 0004, domain and integration tests, Vue list/editor/detail and reference lookup | Domain calculates rounded decimal totals. Draft commands validate versions and related records. `11 passed, 4 warnings`. Frontend build completed in 2.32s. Approval integration followed. |
| 5 · Approvals | `modules/approvals`, `app/workflows/review.py`, migration 0005, decision and race tests, approval inbox and detail screens | Submission and reviewer decisions change both aggregates atomically. `16 passed, 8 warnings`, including opposing decisions on the same record. Frontend build completed in 2.33s. Cross-database and browser checks followed. |
| 6 · Integration and hardening | `app/seed.py`, development launcher, offline API reference, dashboard and administration screens, persistence and race tests, Vitest and Playwright suites, lockfiles and documentation | Tested exact input precision, tenant scope below the API, duplicate submission, cancellation racing a decision, migration reversibility and repeatable seeds. Final results are above. |

## Failures encountered and resolved

- The first PostgreSQL suite had **9 passed and 15 setup errors**. The initial server could not bind a Unix-domain socket, and a later standalone process was unavailable to the test shell. A local TCP server and its test suite were run in one managed process lifetime. Both the complete PostgreSQL suite and seeding then passed.
- The first Vitest run collected four passing tests and failed to collect one component suite because two hoisted mocks shared a declaration. Separate declarations restored collection. All eight tests passed.
- The first Playwright run had **three launch failures** because the system Chromium wrapper referred to a missing executable. A locally provisioned Chromium 140 binary was used. Subsequent browser runs exposed missing font setup, an invalid font import during integration, and two select controls that needed explicit accessible names. The application now bundles Inter locally, and the controls have stable labels. All three journeys passed from a clean installation.
- Early Pytest runs emitted deprecation warnings for Alembic path parsing and the Starlette/AnyIO test-client combination. The Alembic configuration now specifies its path separator and the dependency lock pins the tested AnyIO version. Final Pytest runs emitted no warnings.
- npm installation reported upstream deprecation notices for `lucide-vue-next`, `glob` and `whatwg-encoding`. Browser runner output also included a Node terminal-color environment warning. These did not affect the build or tests.

The tested release covers the initial six contexts. Deployment-scale load, production operations and Ubuntu-specific acceptance remain outside this verification record.
