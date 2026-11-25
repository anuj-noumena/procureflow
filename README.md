# ProcureFlow

ProcureFlow is a multi-tenant procurement workspace for small and medium-sized businesses. A requester can draft a purchase, select a supplier or catalog item, and submit it to an assigned reviewer. The reviewer can approve it or reject it with a reason. Both parties can see the resulting status, totals, and history.

## Run locally

Use Python 3.12 with virtual-environment support, Node.js 22 and npm 10 on x86-64 Linux. SQLite is included with the Python runtime. Install application dependencies once. The app, its fonts, the API reference, and the automated tests run locally. Browser tests also need a compatible local Chromium executable.

From the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
(cd frontend && npm ci --no-audit --no-fund)
./scripts/pf init
./scripts/pf seed
```

Start the two processes in separate terminals:

```sh
./scripts/pf backend
```

```sh
./scripts/pf frontend
```

Open [the workspace](http://127.0.0.1:5173). The Vite server proxies API requests to the backend on port 8000. The generated access key and development password are stored in the repository's private `.env`. The script reads simple `KEY=value` entries as data. An exported environment variable takes precedence.

### Try a complete review

1. Sign in to workspace **northline** as **requester@northline.example**. Use the value of `PF_SEED_PASSWORD` in your local `.env`. The initial setup generates a unique password for this installation.
2. Choose **New requisition**. Enter a description, department and required date. Add a line with quantity `3`, unit price `14.50`, and tax `0`. Save the draft and check the estimated total of **USD 43.50**.
3. Choose **Submit for approval**, select **Casey Morgan**, and confirm.
4. Sign out and sign in as **reviewer@northline.example** with the same development password. Open **Approvals**, open the new request, enter a comment, and confirm the decision. Open the requisition to see its history.

### Development accounts

The two seed workspaces are `northline` (Northline Studio) and `harbor` (Harbor Works). Substitute the workspace slug in the email pattern `<handle>@<slug>.example`. Each has three departments, a branch, four suppliers, three catalog entries, five sample requisitions, and an assigned pending approval.

| Handle | Role | Access |
|---|---|---|
| `admin` | Organization administrator | Profile, branches, departments, memberships, supplier and catalog maintenance, request management and assigned reviews |
| `buyer` | Procurement manager | Supplier and catalog maintenance, request management and assigned reviews |
| `reviewer` | Department manager | Own requests and assigned reviews |
| `requester` | Requester | Read tenant directories and requisitions, create and maintain own requests |
| `finance` | Finance user | Read tenant directories and requisitions |

Seed identifiers, business numbers, dates and sample amounts are deterministic. Password hashes use fresh salts. Re-running the seed preserves an existing seed workspace, including subsequent user edits. Both workspaces are seeded in a single transaction. The seed command requires explicit development mode and a development password. Keep these accounts confined to development data.

## Architecture and source layout

The FastAPI backend is a modular monolith. Each context owns its HTTP schemas and persistence models. Requisitions and approvals have standalone domain rules, and a small application service coordinates operations that change both aggregates. SQLAlchemy 2 manages persistence, Pydantic 2 validates the API, and Alembic versions the schema. PostgreSQL 16 is the production database target.

| Path | Contents |
|---|---|
| `backend/app/modules/organizations` | Tenant profiles, departments, branches, default currency and status |
| `backend/app/modules/identity` | Accounts, memberships, password hashing, JWTs, role policy and enrollment |
| `backend/app/modules/suppliers` | Supplier directory, contacts, addresses, categories, tax identifiers and status |
| `backend/app/modules/catalog` | Products and services with standard descriptions, units and reference prices |
| `backend/app/modules/requisitions` | Requisition rules, estimates, line ownership, versioned persistence and history |
| `backend/app/modules/approvals` | Assigned review, decision rules, inbox and persisted decision data |
| `backend/app/workflows/review.py` | Atomic submission, cancellation and decision across both aggregates |
| `backend/app/core` | Sessions, tenant dependencies, shared schema types, API errors and configuration |
| `backend/migrations`, `backend/tests` | Explicit migrations and Pytest domain, HTTPX-backed API and database tests |
| `frontend/src/pages`, `components` | Vue 3 Composition API screens, PrimeVue dialogs and shared controls |
| `frontend/src/lib`, `router.ts` | Axios API boundary, Pinia session, request types, permissions and navigation |
| `frontend/e2e`, `scripts` | Playwright browser journeys and local development commands |

See [the architecture and workflow notes](docs/architecture.md) for aggregate boundaries, database relationships, transaction semantics and design trade-offs. [The verification record](docs/verification.md) gives checks, failures encountered and final results.

## Configuration and migrations

| Variable | Purpose |
|---|---|
| `PF_ENV` | Set to `development` for the development seed. Set to `production` for production. |
| `PF_DATABASE_URL` | SQLAlchemy URL. The default `sqlite:///./procureflow.db` resolves inside `backend/` with the launcher. |
| `PF_JWT_SECRET` | Required signing secret of at least 32 bytes. Generate a random secret per environment. |
| `PF_CORS_ORIGINS` | Comma-separated exact origins for browser requests. Local initialization permits localhost and 127.0.0.1 on port 5173. |
| `PF_SEED_PASSWORD` | Development-only login password, 12–128 characters. |
| `PF_TEST_POSTGRES_URL` | Optional disposable test database for running the backend suite on PostgreSQL. |
| `PF_CHROMIUM` | Optional path to an installed browser binary for Playwright. |

`./scripts/pf init` creates a private `.env` if needed and applies migrations. Supply production settings through the environment. To target an existing PostgreSQL 16 database, set `PF_DATABASE_URL` to a URL of the form `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE`. The database and migration user must already exist. Run `./scripts/pf migrate` before starting the service. The schema is never auto-created at application startup.

For Alembic inspection, run commands from `backend/` with `PF_DATABASE_URL` exported, for example `../.venv/bin/alembic current`, `../.venv/bin/alembic history` or `../.venv/bin/alembic check`. Downgrade testing uses a fresh test database or schema. Downgrading to `base` removes the application tables.

## Tests and frontend build

```sh
./scripts/pf test-backend
./scripts/pf test-frontend
./scripts/pf build
./scripts/pf e2e
```

The default backend suite creates a migrated SQLite file per integration test. With `PF_TEST_POSTGRES_URL` set, each integration test creates and drops its own randomly named schema. Use a disposable PostgreSQL database with schema creation privileges. Both modes run the same assertions, including persisted-state and racing-request checks.

Vitest and Vue Test Utils exercise forms, API errors and confirmed actions. Playwright starts isolated test servers on ports 5187 and 8187, seeds a temporary SQLite database and uses a per-run password. It blocks external browser requests. Either set `PF_CHROMIUM` to an available Chromium executable or provision the Playwright browser once during dependency setup with `(cd frontend && ./node_modules/.bin/playwright install chromium)`. Browser installation is separate from test execution.

The frontend build runs TypeScript checks and emits `frontend/dist/`. Serve that directory with SPA history fallback and proxy `/api/v1` to FastAPI for a single-origin deployment. Development uses the Vite server.

**Offline setup.** The source archive contains the Python constraints and npm lockfile. For a machine that also requires offline installation, pre-stage platform-compatible wheels with `pip download --only-binary=:all: -r backend/requirements.txt -d wheels` and a populated npm cache. Install with `pip install --no-index --find-links wheels -r backend/requirements.txt` and `npm ci --offline --no-audit --no-fund` in the frontend directory. A locally provisioned browser completes the browser-test prerequisites.

## API

The offline [API reference](http://127.0.0.1:8000/docs) and [OpenAPI contract](http://127.0.0.1:8000/openapi.json) are served by FastAPI. Routes use the `/api/v1` prefix.

| Operation | Route |
|---|---|
| Register organization and first administrator atomically | `POST /auth/register` |
| Sign in to a workspace, inspect session | `POST /auth/login`, `GET /auth/me` |
| Read or change organization profile | `GET /organization`, `PUT /organization` |
| Add department or branch | `POST /organization/departments`, `POST /organization/branches` |
| Create account with membership, enroll existing account, change role or activation | `POST /members`, `POST /members/enroll`, `PUT /members/{id}` |
| Read or maintain supplier and catalog directories | `GET/POST /suppliers`, `GET/PUT /suppliers/{id}`, corresponding `/catalog` routes |
| Create, edit and inspect requisitions | `GET/POST /requisitions`, `GET/PUT /requisitions/{id}` |
| Select reviewer, submit or cancel | `GET /approvers`, `POST /requisitions/{id}/submit`, `POST /requisitions/{id}/cancel` |
| Read assigned approvals, record a decision | `GET /approvals`, `GET /approvals/{id}`, `POST /approvals/{id}/decision` |

Login takes `organization` (slug), `email` and `password`. Use the returned token in `Authorization: Bearer <token>`. Registration additionally takes `name` and `organization_name`. The tenant is resolved on the server from the token's user and active membership.

Searchable lists accept `page` (starting at 1), `size` (1–100), `q`, and `sort` (`newest` or `oldest`). Use `status` on suppliers, requisitions and approvals, and `kind` on catalog items. The approval inbox defaults to pending. Page responses contain `items` and `total`. Validation and business errors use `{"error":{"message":"..."}}`.

## Initial release boundaries

Each requisition has one independent approval step. A rejection or cancellation closes that requisition. A new request starts a new review. Directory and requisition reads are organization-wide, with writes controlled by the role and request owner. Finance has read access. The organization API manages activation per membership, so suspending a user in one tenant preserves their access to other tenants.

Currencies use three-letter uppercase codes and amounts have two decimal places. Reference prices are suggestions. There is no exchange-rate conversion. Approval delegation, policy-designed workflows, purchase orders, receiving, invoice matching, payments and consolidated spend reporting are future work. This release also leaves SSO, password recovery, MFA, and login rate limiting for deployment work. See the architecture notes for concurrency and database-specific limits.
