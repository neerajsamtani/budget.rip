# Category suggestions: execution roadmap

Prepared 2026-11-15 against `974b2c0`. No application code has changed. Start with the [complete feature definition](FEATURE-category-suggestions.md); it records the intended product, confirmed choices and proposed later policies. Each plan below also includes its own context, scope, contracts, tests and stop conditions for an agent without conversation history.

## Independently shippable releases

| Plan | What users get | Dependencies | Effort | Status |
| --- | --- | --- | --- | --- |
| [002](002-single-transaction-prefill.md) | Editable Stripe category prefill and explanation for one transaction in the existing modal | None; PR #147 is present | S–M | BLOCKED — implemented in `3f5a563`; read-only API shape verified; 507 server/92 targeted client tests, lint, typecheck and build pass. Full client suite: 729 pass/1 pre-existing FinancialConnectionsForm failure, reproduced on original HEAD. See 002 handoff; next slice 003. |
| [003](003-multi-transaction-prefill.md) | One suggested category for a selected group when every mapped category agrees | 002 | S | TODO |
| [004](004-inline-category-review.md) | Stripe suggestions after refresh with inline title/category editing, accept and dismiss | 003 | M | TODO |
| [005](005-custom-category-mappings.md) | Inspect/map/skip every known label; custom categories and renaming work reliably | 004 | M | TODO |
| [006](006-financial-flow-coverage.md) | Income and financial-movement suggestions with explicit sign/label policies | 005; review proposed defaults before coding | M | TODO |
| [007](007-suggestion-lifecycle.md) | Stale-evidence explanations, deliberate recompute, undo dismissal | 004, 005 | M | TODO |
| [008](008-remember-corrections.md) | Explicitly save a correction as a narrow reusable hint | 007 | S–M | TODO |
| [009](009-bulk-suggestion-review.md) | Review several displayed suggestions as separate events, with per-item results and safe retries | 004, 007 | M | TODO |
| [010](010-suggested-transaction-groups.md) | Inspect/confirm candidate transfer and refund groups as one event | 003, 006, 009; review matching policy | M–L | TODO |
| [011](011-suggestion-coverage-controls.md) | Coverage gaps, explained skips, stored-data dry-run/apply and honest outcome metrics | 004; integrates later contracts when available | M | TODO |

Default execution order is numerical, **one agent/feature at a time**. Agents should stop after their slice is verified and handed off; they should not implement adjacent plans just because files overlap. This document does not launch agents, authorize deployment, or require completing the roadmap before releasing 002.

006's proposed policy is not a prerequisite for 007–009. 011 can move forward after 004 if real coverage data would help choose priorities. Its mapping/lifecycle/group integrations appear only after their own releases. There is no separate engine-only milestone: 002 delivers UI value with the minimal shared mapper.

## Agent handoff protocol

1. Read the selected plan and actual delivered dependency code. Run its drift check; prerequisite changes are expected, unrelated incompatible changes must be reconciled.
2. Implement only that feature, including meaningful tests and applicable migration validation. Preserve raw descriptions, review decisions, user isolation and event totals.
3. Verify the stated commands. Record the implementation commit, what shipped, evidence/limitations and any additive API contracts in the plan and this row.
4. Mark the row DONE only after its acceptance tests pass. Hand back before the next slice. Do not publish, deploy or refresh real bank data without the operator's instruction.

Status values: TODO, IN PROGRESS, DONE, BLOCKED (specific reason), REJECTED (reason). Priority defaults: 002–004 first, then user control/coverage/scale releases as useful. Effort is per feature, not a time estimate or a commitment to build all ten now.

## Initial crosswalk and evidence

[Version-1 exact inventory](stripe-personal-finance-mapping.json): 19 primary labels and 128 detailed pairs, 50 mapped/78 intentionally skipped. **All rent and utilities map to Rent.** Counts describe taxonomy rules, not real transaction coverage. 005 enables explicit custom mappings for all known labels; 006 expands financial-flow defaults. Preserve this original inventory as baseline evidence rather than silently revising its historical counts.

The user supplied the taxonomy. The planner inspected both provided Stripe links, but its available public/browser views omitted the preview classification fields. Plan 002 must confirm the exact nested classification/confidence shape from a sanitized stored response or entitled schema. It need not rediscover labels, change API versions or refresh Stripe.

## File visibility

Use plans 002–011 for execution. Numbering is preserved so existing references and dependencies stay stable.

This repository ignores `*.md`. These Markdown plans exist locally but will not appear in ordinary Git diffs unless explicitly force-added later; no commits/staging were performed while planning. The JSON inventory is visible as an untracked file. An agent in another checkout needs these plan artifacts transferred or explicitly versioned; do not assume ignored Markdown travels with a code commit.
