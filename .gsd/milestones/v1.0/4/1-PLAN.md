---
phase: 4
plan: 1
wave: 1
depends_on: []
---

# Plan 4.1: Real-Time Ledger WebSocket Streaming Service

## Objective
Implement a secure WebSocket streaming service on `/ws/ledger` using `Flask-SocketIO` that broadcasts real-time transaction lifecycle events to connected spreadsheet connectors, Power Query clients, and cloud analytics ingest pipelines.

## Context
- .gsd/SPEC.md
- .gsd/DECISIONS.md
- finance_app/app/extensions.py
- finance_app/app/models/transaction.py

## Tasks

<task type="auto">
  <name>Install SocketIO dependencies and initialize extension</name>
  <files>finance_app/requirements.txt, finance_app/app/extensions.py, finance_app/app/__init__.py</files>
  <action>
    1. Add `flask-socketio>=5.3.6` and `simple-websocket>=1.0.0` to requirements.txt.
    2. In `app/extensions.py`, instantiate `socketio = SocketIO(cors_allowed_origins="*")`.
    3. In `app/__init__.py`, initialize `socketio.init_app(app)` in `create_app()`.
    4. Ensure graceful fallback if running under standard WSGI test runners.
  </action>
  <verify>python -c "from app.extensions import socketio; print(socketio)"</verify>
  <done>Flask-SocketIO is successfully imported and initialized in the application context.</done>
</task>

<task type="auto">
  <name>Build Ledger WebSocket namespace and transaction event broadcaster</name>
  <files>finance_app/app/services/ledger_stream.py, finance_app/app/transactions/routes.py</files>
  <action>
    1. Create `app/services/ledger_stream.py` defining `LedgerNamespace` on `/ws/ledger`.
    2. Add client authentication verifying session user or auth token.
    3. Implement `broadcast_ledger_event(user_id, event_type, transaction_data)` helper.
    4. Hook into transaction creation, update, and deletion in `app/transactions/routes.py` to broadcast tabular row snapshots.
  </action>
  <verify>python -m unittest tests.test_reporting_and_sync.TestLedgerStream</verify>
  <done>WebSocket namespace authenticates users and emits JSON ledger events on transaction changes.</done>
</task>

## Success Criteria
- [ ] WebSocket endpoint accessible at `/ws/ledger`.
- [ ] Authenticated client receives real-time transaction event payloads with full tabular columns (account, category, amount, balance).
