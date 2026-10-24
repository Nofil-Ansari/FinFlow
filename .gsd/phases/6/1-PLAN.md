---
phase: 6
plan: fix-deprecations-and-teardown
wave: 1
gap_closure: true
---

# Fix: Modernize UTC Timestamps & SQLite Connection Cleanup in Test Harness

## Problem
1. **Datetime Deprecation**: Executing tests logs numerous warnings: `DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC)`.
2. **Unclosed SQLite Database Warnings**: Running `unittest discover` emits ResourceWarnings: `ResourceWarning: unclosed database in <sqlite3.Connection>` due to missing engine disposal in `test_ai_advisor.py` tearDown.

## Root Cause
- Python 3.12+ deprecated `datetime.utcnow()` in standard library.
- Test suites tear down tables via `db.drop_all()` and `db.session.remove()`, but don't explicitly dispose of the SQLAlchemy engine pool connection for SQLite.

## Tasks

<task type="auto">
  <name>Modernize utcnow() across models, services, and routes</name>
  <files>
    finance_app/app/models/account.py,
    finance_app/app/models/transaction.py,
    finance_app/app/models/user.py,
    finance_app/app/services/ledger_stream.py,
    finance_app/app/services/pdf_export.py,
    finance_app/app/services/excel_export.py,
    finance_app/app/reports/routes.py
  </files>
  <action>
    1. Import `timezone` from `datetime`.
    2. Replace instances of `datetime.utcnow()` with `datetime.now(timezone.utc)`.
    3. Update default SQLAlchemy column definitions to `default=lambda: datetime.now(timezone.utc)`.
  </action>
  <verify>python -m unittest tests.test_reporting_and_sync</verify>
  <done>Zero utcnow() DeprecationWarnings logged during module execution.</done>
</task>

<task type="auto">
  <name>Fix SQLite engine cleanup in test harness tearDown</name>
  <files>finance_app/tests/test_ai_advisor.py, finance_app/tests/test_reporting_and_sync.py</files>
  <action>
    1. In `tearDown()` methods, invoke `db.engine.dispose()` after `db.session.remove()`.
    2. Ensure test database connections are closed cleanly.
  </action>
  <verify>python -W error::ResourceWarning -m unittest discover -s tests -p "test_*.py"</verify>
  <done>ResourceWarnings regarding unclosed sqlite connections are eliminated.</done>
</task>

## Success Criteria
- [ ] No `datetime.utcnow()` DeprecationWarnings during test discovery.
- [ ] No `unclosed database` ResourceWarnings during test discovery.
- [ ] 43/43 tests pass cleanly.
