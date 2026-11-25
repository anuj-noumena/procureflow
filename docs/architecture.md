# Domain model and transaction design

## Ownership and module boundaries

An organization is the tenant root. Each tenant-owned table has an `organization_id` foreign key. Users are global accounts, while roles and activation are attached to an organization membership. A signed token identifies both user and membership. Every authenticated request reloads that membership, checks the user and organization status, and resolves the effective tenant. The organization slug supplied at login selects an existing membership.

| Aggregate | Tables | Integrity boundary |
|---|---|---|
| Organization | `organizations`, `departments`, `branches` | Unique organization slug. Unit names are unique within a tenant. Profile holds status and default currency. |
| User and membership | `users`, `memberships` | Unique normalized account email and one membership per user and organization. Adding an existing account preserves its password. |
| Supplier | `suppliers` | Unique normalized legal name and non-null tax ID per organization. Contacts and addresses are validated value collections owned by the profile. |
| Catalog item | `catalog_items` | Tenant-unique item code. Each item records type, category, description, unit, reference price and currency. |
| Purchase requisition | `requisitions`, `requisition_lines`, `requisition_history` | One owner, currency, department and optional supplier. Ordered lines and events belong to the root. The root carries an optimistic version. |
| Approval request | `approvals` | Unique organization and requisition pair. The row records assigned membership, review status, comment, decision time and version. An inbox index covers tenant, reviewer and status. |

Parent tables referenced across module boundaries expose a unique `(organization_id, id)` key. Composite foreign keys protect each requisition's department, supplier and requester, each line's catalog item and parent, and each approval's requisition and reviewer. Tenant-scoped lookup makes an unknown or foreign ID return 404. All public mutations accept named input models that forbid extra fields.

The API layer parses and serializes Pydantic models. Application services load tenant-scoped records, invoke domain rules and flush a single session. The `Estimate`, `Requisition`, `ApprovalRequest` and role-policy types are independent of the framework and ORM. Domain logic covers financial ranges, rounding, lifecycle transitions, independent review and ownership. Straightforward directory use cases use concrete services. The requisition repository centralizes scoped aggregate loading, version comparison and list filters.

A request-scoped unit of work opens the transaction and commits on success. A raised error rolls it back. Application services can flush to obtain IDs and catch constraint conflicts while the transaction is still open. The identity context handles initial registration across the organization and membership boundaries. The review workflow owns changes that span approvals and requisitions. The audit table stores ordered business events in the same transaction, giving future integrations durable source records. External delivery and consumer checkpoints are outside this release.

## Requisition lifecycle

| Current state | Command | Result |
|---|---|---|
| Draft | Save draft | Replace the editable lines, recalculate the estimate, advance the version and record an edit |
| Draft with lines | Submit to eligible reviewer | Append submitted and pending-approval events, enter pending approval, create one pending review |
| Draft | Cancel | Enter cancelled state and append cancellation event |
| Pending approval | Cancel | Close both request and review as cancelled |
| Pending approval | Assigned reviewer approves | Close both as approved with UTC decision timestamp and optional comment |
| Pending approval | Assigned reviewer rejects | Close both as rejected with UTC decision timestamp and required reason |

Approved, rejected and cancelled are terminal. Submission is a recorded event within the transition to pending approval. Publishing a separate intermediate submitted state would permit a request to appear submitted before its reviewer exists. Each command therefore completes both parts in one transaction.

The requester or an authorized procurement manager or administrator can edit, submit and cancel. The assigned reviewer must hold decision permission and be distinct from both the requester and the person submitting on their behalf. Authentication and authorization are checked again at decision time. A pending assignment to a deactivated reviewer can be closed via cancellation by an authorized request owner or manager.

Draft edits, submission, cancellation and approval decisions require the version last read by the client. SQLAlchemy checks aggregate versions again at flush. Unique constraints protect the single approval and event sequence. A duplicate command receives a conflict. The client can refresh before retrying. Seeded examples begin with version 1, reflecting an initial fixture snapshot. Versions are opaque concurrency tokens.

## Monetary model

The browser transmits fractional inputs as decimal strings. The backend accepts quantity through three decimal places, price through two, and tax from zero through 100 with two decimal places. Each requisition supports up to 100 lines. The line amount equals quantity times unit price times one plus the tax rate, rounded half-up to two decimal places. The request total is the sum of those rounded amounts. An aggregate or line total above 999,999,999,999.99 is rejected before persistence.

Catalog selections copy the description, unit and a matching-currency price into the line. These snapshots preserve a request when catalog details change. Draft saves and submission check the selected supplier's active status. Deactivation preserves the supplier row, historical references and completed requisitions. Drafts may be empty. Submission requires at least one line.

## Database behavior and trade-offs

- **PostgreSQL 16** stores amounts in fixed-scale `NUMERIC` columns. Composite foreign keys, versioned writes and unique constraints protect concurrent commands. Test runs isolate data in a random schema and exercise real concurrent sessions.
- **SQLite** enables foreign keys on every connection. Numeric affinity can store a value using a binary representation. Application arithmetic uses Python `Decimal` before persistence, and the supported precision bounds keep values within the tested scale. SQLite serializes writers and can report database contention. A temporarily unavailable database returns 503.
- **Timestamps** are generated as timezone-aware UTC. SQLite does not preserve the offset in its timestamp representation, so the SQLAlchemy adapter restores UTC on load. PostgreSQL uses timezone-aware timestamps.
- **Tenant isolation** uses application scoping and relational constraints in a shared schema. The database user can see multiple tenants. An independent SQL reader would need explicit tenant scoping or a separate PostgreSQL row-security design.
- **Directories** use tenant-scoped identifiers and uniqueness constraints. Concurrent directory edits use ordinary database update semantics. Requisition and approval commands additionally enforce optimistic versions.
- **Supplier contact and address collections** use JSON inside the supplier aggregate. Contacts and addresses are retrieved with their supplier. Categories and units are validated labels in this initial model. A governed taxonomy can later promote them to first-class records.
- **Approval extensibility** starts with a single assigned step. Future multi-level workflows can add a step sequence and routing policy behind the review service. The current unique constraint intentionally limits each requisition to one approval.
- **Authentication** uses salted, versioned scrypt hashes and one-hour HS256 bearer tokens. Session tokens live in browser session storage. Logout clears the local token. Membership deactivation takes effect on subsequent requests. Production deployment must supply its own signing secret and TLS configuration.
