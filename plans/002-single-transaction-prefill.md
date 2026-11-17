# 002: Single-transaction category prefill

Implemented in `3f5a563`; dismissal-cache fix in `8be47e2`. Release status: BLOCKED on a pre-existing full client suite failure. Base: `e632860`.

The existing event modal suggests an editable title/category and explains the evidence. Creation requires explicit confirmation. No migration, persisted Stripe suggestions, backfill, refresh, raw-description changes, or event-amount changes.

## Contract

- `/api/event-hints/evaluate` returns `{data: {suggestion: null | {name, category, category_id, source, source_metadata, matched_hint_id, matched_hint_name}}}`. Category is a name; new client fields are optional and hint IDs nullable.
- Categorized winning hints take precedence. Name-only winning hints retain their title and may receive Stripe category fallback. Without a hint, use trimmed responsible party then description, capped at 255 characters.
- Stripe fallback requires one distinct, found, unreviewed Stripe expense with positive normalized amount, no current-user rejection, and a mapped category owned by the current user. Missing IDs, weak/malformed/conflicting evidence, and unavailable categories abstain. Multiple items retain hint-only behavior.
- Parse only nested `personal_finance` labels with high/very-high classification confidence, independently of merchant confidence. The test inventory covers all 128 pairs: 50 mapped, 78 skipped; five primary-only fallbacks; all seven rent/utilities details map to Rent. Runtime code never reads fixtures or plans.
- Preserve edits during refetch and isolate responses by selection. API failure permits manual entry. Successful dismissal resets cached prefills so reopening waits for fresh evidence.

## Evidence and verification

The nested shape was confirmed on 2026-11-16 with authorized read-only Stripe GET requests using the configured preview version. [Sanitized evidence](../server/tests/fixtures/stripe_personal_finance_evidence.json) contains only classification type, labels, and confidence. [Taxonomy inventory](../server/tests/fixtures/stripe_personal_finance_mapping.json) preserves the user-provided crosswalk.

- Server: `uv run pytest` — 507 passed; `make lint` — passed. Tests use existing SQLite isolation.
- Client: `npm test -- --runInBand CreateEventModal.test.tsx useApi.test.tsx` — 93 passed; `npm run typecheck` — passed.
- Build: `npm run build -- --configLoader runner` — passed; runner avoids temporary writes through shared dependencies outside the sandbox.
- Full client suite: 730 passed, one failure at `FinancialConnectionsForm.test.tsx:403`, reproduced on untouched original HEAD. Leave that unrelated test unchanged.

This cleanup compacts the fixture without dropping cases, removes redundant runtime abstentions, and shortens handoff notes. Next feature slice: multi-transaction prefill (003), which is outside this implementation.
