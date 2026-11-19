# WasteConnect - Agent & Developer Rules

This document outlines mandatory architecture principles, coding standards, and operational guidelines for WasteConnect. All contributors and AI agents must strictly follow these rules.

---

## 1. Security & Operational Rules

- **Never touch `.env`:** Never open, read, print, output, or log the `.env` file or any secret values (passwords, tokens, secret keys, connection strings).
- **No Git Commit/Push:** AI agents must never run `git commit` or `git push`. The user reviews and commits all changes.
- **Plan before coding:** Always formulate and propose a clear plan with file lists and implementation details before modifying or creating code.
- **Write and run tests:** Every feature, bugfix, or state transition must be accompanied by comprehensive tests, and all tests and linters must pass before completing work.

---

## 2. Architecture & Layering

- **Layering Principle:** `router -> service -> models`
  - **Routers (`router`):** Only parse input, validate requests, invoke appropriate service functions, and return structured responses. Routers contain zero business logic and zero direct database queries.
  - **Services (`service`):** Contain business logic, transactions, state machines, and interactions with models/repositories.
  - **Models (`models`):** Define database entities, columns, relationships, and constraints.
- **Modular Boundaries:**
  - A module must **never directly query, insert, update, or join another module's tables**.
  - Cross-module interactions must occur strictly through designated public service APIs or shared interfaces.
- **Permissions:**
  - Permissions are implemented as FastAPI dependencies in `app/core/permissions/`.
  - Permissions are strictly enforced in the backend for every protected endpoint, never deferred to the frontend.

---

## 3. Database & Data Conventions

- **Primary Keys:** Always use UUID primary keys (`UUIDPrimaryKeyMixin`).
- **Timestamps:** Every table must include timezone-aware `created_at` and `updated_at` timestamps (`TimestampMixin`).
- **Numbers & Decimals:**
  - **Money:** Always use `Numeric(12, 2)`. Never use `float`.
  - **Weight & Quantity:** Always use `Numeric(12, 3)`. Never use `float`.
- **Enums:** Store enums as `VARCHAR`/`Text` with database `CHECK` constraints, rather than native database enum types (which complicate migrations).
- **Categories as Data:** Waste categories are dynamic configuration data in database tables, not hard-coded enums or Python code.
- **Naming Conventions:** All database constraints (indexes, unique constraints, foreign keys, check constraints, primary keys) must follow SQLAlchemy's explicit naming convention:
  - Indexes: `ix_%(column_0_label)s`
  - Unique: `uq_%(table_name)s_%(column_0_name)s`
  - Checks: `ck_%(table_name)s_%(constraint_name)s`
  - Foreign Keys: `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`
  - Primary Keys: `pk_%(table_name)s`

---

## 4. API Design Standards

- **API-First & Clean Contracts:** Endpoints must return standardized error codes and structured payload data (`{"code": "...", "data": ...}` or `{"code": "...", "detail": "..."}`), rather than hard-coded English sentences. This enables localization and client-controlled error rendering.
- **Validation:** All inputs and outputs must be strongly typed with Pydantic v2 schemas.
- **Error Handling:** Never leak sensitive database tracebacks, internal paths, connection strings, or query details in HTTP error responses.
