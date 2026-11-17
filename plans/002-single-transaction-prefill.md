# Plan 002: Suggest a category when creating a single-transaction event

Planned at: `974b2c0`, 2026-11-15. Priority: P1. Effort: S–M. Risk: LOW. Status: BLOCKED (pre-existing full client suite failure; implementation complete). Dependencies: none.

## Executor instructions

Read `CLAUDE.md` and this entire plan. Use SQLAlchemy/Flask and the existing TanStack Query hooks in `client/src/hooks/useApi.ts`; reuse shadcn controls and toast helpers. Categories/hints/suggestions are user-owned, while line items and raw transactions currently use the shared account model. Preserve raw descriptions, merchant-confidence behavior, and event amount semantics. Require explicit user confirmation before creating or changing an event. No installs that upgrade lockfiles, deployment, live Stripe refresh, push, or PR creation are part of this task.

The repository was inspected at `974b2c0`. Before implementation run `git diff --stat 974b2c0..HEAD -- server client`; prerequisite plans intentionally change these files, so compare their delivered contracts with this plan rather than treating all drift as failure. Unrelated incompatible drift is a stop condition. Each slice is an end-to-end release, not permission to implement later slices. Update only your row in `plans/README.md` after verification.

## Shippable outcome

Users get the first working Stripe category suggestion inside the existing event modal, with an explanation and normal editable fields. This requires no new database tables, backfill command, or inline-review redesign.

## Current state and prerequisite contract

`server/resources/event_hint.py`, `evaluate_event_hints`, currently returns null if there are no hints and queries only description/amount/party/payment method. The load-bearing branch is `if not hints: return jsonify({"data": {"suggestion": None}}), 200`. `utils/cel_evaluator.py:evaluate_hints` returns the first active match with `name`, nullable `category`, and hint IDs. `client/src/components/CreateEventModal.tsx:computeInitialValues` takes this result or defaults to a cleaned description and blank category. It already has editable category/title controls. `useEvaluateEventHints` is the sole modal request hook.

`Transaction.source_data` retains the full Stripe JSON; `LineItem.transaction` accesses it. Raw classifications have only a money-movement fixture in `server/tests/test_stripe.py:462`. The user supplied all 19 personal-finance primaries/128 detailed labels; the exact mapping inventory is `plans/stripe-personal-finance-mapping.json` (50 mapped, 78 skipped, utilities included in Rent).

## Delivered contract

The delivered read-only helper returns null or `{name, category, category_id, source, source_metadata, matched_hint_id, matched_hint_name}`. `source` identifies category evidence (`event_hint` or `stripe_personal_finance`); metadata can identify a separate name hint. Initial source fields are optional on clients. No migration; existing multi-item behavior unchanged.

## File scope

Modify `server/resources/event_hint.py`, `server/tests/test_event_hints.py`, `client/src/hooks/useApi.ts`, `client/src/components/CreateEventModal.tsx`, `client/src/components/__tests__/CreateEventModal.test.tsx`, and `client/src/hooks/__tests__/useApi.test.tsx`. Create `server/utils/stripe_category_mapping.py`, `server/utils/category_suggestions.py`, `server/tests/test_stripe_category_mapping.py`, and sanitized fixtures under `server/tests/fixtures/stripe_personal_finance*.json`. No model/migration/generator changes.

Only implement this release. New tests/fixtures and the migration named above are allowed; source outside this scope needs a plan amendment. Update the index status after verification.

## Steps and gates

### 1. Capture evidence and add the mapper

Confirm the nested `personal_finance` label/confidence fields from one sanitized stored local response or entitled Stripe schema, without refreshing Stripe or printing raw transactions/secrets. Parse only classification type `personal_finance`; independently require high/very-high classification confidence. Copy the 128-pair inventory into a test fixture; runtime code must not read `plans/`. Build a pure mapper using the exact initial crosswalk and its five primary-only fallbacks. Reject unknown/mismatched pairs and malformed/conflicting data. Initially only positive normalized expense amounts qualify. Resolve default category names within the current user; missing targets abstain. Return a candidate with category ID/name and minimal evidence. All seven rent/utility details map to Rent.

**Verify:** `cd server && uv run pytest tests/test_stripe_category_mapping.py` → all tests pass. For model changes, also complete the disposable PostgreSQL migration round trip before handoff.

### 2. Wire a one-item prefill into the modal

Add `resolve_event_prefill` in `utils/category_suggestions.py` using existing `evaluate_hints` first. A categorized winning hint wins. A name-only winning hint keeps its title and may receive Stripe category fallback. Without a hint, use trimmed responsible party then description, capped at 255 chars. Require the complete distinct requested ID set to be found; Stripe fallback only applies to unreviewed items with no current-user rejected suggestion. Reuse existing dismissal records even before Stripe inline generation exists. Eagerly load transactions; no API calls and no DB writes. Requests with more than one distinct item keep current hint-only behavior until 003. Keep the existing endpoint/response envelope and make hint IDs nullable for Stripe-only results.

**Verify:** `cd server && uv run pytest tests/test_event_hints.py tests/test_stripe_category_mapping.py` → all tests pass. For model changes, also complete the disposable PostgreSQL migration round trip before handoff.

### 3. Expose the suggestion and preserve edits

Extend handwritten hook types additively with category ID, source and minimal evidence. In the modal show a readable explanation and existing editable category/title controls; missing new fields remain compatible. Existing `category` is a name, so keep the current form's name-based category value until event submission; IDs belong in the evidence contract. Do not overwrite typed edits on background refetch, and never prefill a changed selection with a late response. API failure still allows manual entry. Do not modify inline review or persist suggestions.

**Verify:** `cd client && npm test -- --runInBand CreateEventModal.test.tsx useApi.test.tsx` → all tests pass. For model changes, also complete the disposable PostgreSQL migration round trip before handoff.

## Test plan

Every mapping entry/skip, primary-only fallback, all seven utilities, independent merchant/category confidence, no hints, categorized/name-only hint precedence, malformed data, missing category/ID, reviewed/dismissed item, non-Stripe item, inflow/zero, source text, manual edits, request failure and unchanged multi-item hint behavior. Assert evaluate makes no writes and raw descriptions are unchanged. Use `test_event_hints.py` and modal tests as the patterns.

## Verification commands

- Server targeted tests: `cd server && uv run pytest <test files>` → all pass. Tests use isolated SQLite via `tests/conftest.py`; do not override its isolation.
- Before handoff: `cd server && uv run pytest && make lint` → all tests and ruff lint/format checks pass.
- Client targeted tests: `cd client && npm test -- --runInBand <test names>` → all pass. Before handoff run `npm run typecheck` and `npm run build` → exit 0; also run the full client suite when shared hooks/review behavior changes.
- Dependencies, if absent: `cd server && uv sync`; `cd client && npm ci --legacy-peer-deps`. Do not regenerate dependency locks.
- For a new migration: `cd server && uv run alembic heads` → one head; upgrade/downgrade/upgrade on a disposable PostgreSQL database → no data loss outside that migration. SQLite unit tests do not verify PostgreSQL migration behavior. Never use normal local/production data for migration experiments.

## Done criteria

- [x] The delivered contract is exercised through its user-visible path, not only pure helper tests.
- [x] All targeted commands above pass and new behavior has exact-value assertions.
- [ ] Server full tests/lint and affected client tests/typecheck/build pass; required migration round trip passes.
- [x] New tests use existing SQLite isolation; no live refresh or ordinary database writes occur during validation.
- [x] Diff contains only in-scope files and the index status update; no unrelated user changes were overwritten.
- [x] Record the shipped behavior, verified commands, remaining limitations and the implementation commit in this plan/index.

## Stop conditions

No verified nested classification/confidence shape is available; report only that missing evidence. The taxonomy itself is already provided. Do not guess Plaid fields or change API versions.

Also stop if a prerequisite contract is missing, unrelated drift invalidates the described behavior, an out-of-scope change is necessary, or a verification gate still fails after two reasonable fixes. Report the specific missing evidence/decision instead of implementing later releases.

## Handoff and maintenance

Keep the mapper reusable by later inline and multi-item paths; avoid a strategy framework. Name-based resolution is temporary and is replaced by stable bindings in 005.

Use the operator’s current task branch and imperative commit style (for example, `Add reviewable event suggestions`). Do not push, deploy or open a PR without an explicit instruction. Hand off the commit, commands/results, contract changes and next plan. A later agent reads this plan and the delivered code; it must not need the original conversation.


## Implementation handoff — 2026-11-16

Implementation commit: `3f5a563` (`Add single-transaction Stripe category prefill`).

The existing modal now receives editable category/title suggestions with readable Stripe or event-hint evidence. Categorized hints win; name-only hints retain their title while receiving eligible Stripe categories. Multi-item requests remain hint-only. The resolver requires every distinct requested ID, respects current-user categories and rejections, and skips reviewed, non-Stripe, zero and inflow items. No schema changes, suggestion persistence, raw-description changes or event-amount changes.

Evidence was obtained with explicitly authorized, read-only Stripe account/transaction GET requests using the configured preview version. The sanitized fixture records only `type` and nested `personal_finance.confidence_level`, `primary_label`, `detailed_label`; the observed low-confidence income example correctly abstains. Credentials, merchant/account IDs and raw transactions were not persisted. No refresh or database writes ran.

Verified:
- Targeted server tests: 229 passed before the final three coverage additions; final full server suite: **507 passed**.
- `UV_NO_SYNC=1 UV_CACHE_DIR=/tmp/budgit-uv-cache make lint`: passed. Existing dependencies were reused without syncing or lockfile changes.
- Targeted client tests: **92 passed**.
- `npm run typecheck`: passed.
- `npm run build -- --configLoader runner`: passed. The default config bundler cannot create its temporary directory through dependencies shared outside this sandbox; runner avoids that write.
- Full client suite: **729 passed, 1 failed**. The failure is `FinancialConnectionsForm.test.tsx:403`, “setStripeAccounts is not called when there is an error.” Running the untouched original HEAD suite in `/tmp/budgit-prefill-baseline` reproduces exactly the same failure (24 passed, 1 failed). No out-of-scope fix was made. The release remains BLOCKED on the all-green verification gate.
- `git diff --check`: passed. No migration is required.

The plans were ignored local files in another worktree and were copied here for this handoff. The exact mapping inventory is independently captured under server test fixtures; runtime never reads plans. Later work should resolve the existing client test blocker before marking this release DONE. The next feature slice is 003 (multi-transaction prefill); it was not implemented.


### Review follow-up — dismissal cache

Resolved the review finding by resetting `eventHintSuggestion` queries after successful dismissal. Clearing cached data is necessary: invalidation alone retains stale data, which a reopened form would use before a background response arrives. Added a regression covering initial Stripe prefill, closing the modal, dismissing an existing suggestion, reopening while reevaluation is pending, and receiving no Stripe category.

Verification: 93 affected client tests pass; typecheck and production build (`--configLoader runner`) pass; full client suite has 730 passing tests and the same pre-existing FinancialConnectionsForm failure. No server behavior changed.
