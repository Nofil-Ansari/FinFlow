---
phase: 4
plan: 4
wave: 3
depends_on: [4.1, 4.2, 4.3]
---

# Plan 4.4: Integration Testing & Verification Suite

## Objective
Verify the entire Phase 4 feature set through automated unit and integration tests and ensure zero regressions across existing application test suites.

## Context
- .gsd/SPEC.md
- finance_app/tests/test_finance_app.py
- finance_app/tests/test_ai_advisor.py

## Tasks

<task type="auto">
  <name>Create comprehensive Phase 4 test suite</name>
  <files>finance_app/tests/test_reporting_and_sync.py</files>
  <action>
    1. Create `tests/test_reporting_and_sync.py`.
    2. Write test cases for:
       - PDF generation returns valid `%PDF` header bytes with non-zero length.
       - Excel generation returns valid `.xlsx` zip structure with expected worksheet names.
       - Subscription leakage heuristics accurately detect recurring 30-day patterns and price creep.
       - Export routes enforce authentication and return 200 OK with correct headers.
       - WebSocket event broadcaster functions safely under mock/test context.
  </action>
  <verify>python -m unittest tests.test_reporting_and_sync.py</verify>
  <done>All Phase 4 unit and integration tests pass with 100% success.</done>
</task>

<task type="auto">
  <name>Run full application test discovery and verify zero regressions</name>
  <files>finance_app/tests/</files>
  <action>
    1. Run `python -m unittest discover tests`.
    2. Verify all existing 23 tests plus new Phase 4 tests pass without error.
    3. Verify active Flask server at http://127.0.0.1:5000 responds to /reports/.
  </action>
  <verify>python -m unittest discover tests</verify>
  <done>All test suites pass cleanly with zero regressions on branch LLM_pilot_branch.</done>
</task>

## Success Criteria
- [ ] Complete discovery suite passes cleanly.
- [ ] Phase 4 features verified functional without breaking existing ledger or AI advisor capabilities.
