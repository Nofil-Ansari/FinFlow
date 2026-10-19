# Research: Phase 4 — Advanced Analytics, Reporting & Real-Time Data Sync

> Conducted on 2026-10-12

## 1. Real-Time Data Streaming for Spreadsheets & BigQuery
### Problem
External tools (MS Excel with Power Query / Office JS Add-ins, Google Sheets Apps Script, and cloud ingestion pipelines for BigQuery) require streaming data updates rather than static manual re-exports.

### Solution: `Flask-SocketIO` with `simple-websocket`
- **Driver**: `simple-websocket` provides clean standalone WebSocket support on standard WSGI servers without requiring eventlet/gevent monkey-patching, perfectly compatible with Python 3.13 on Windows.
- **Authentication**: Token-based query param or session cookie auth upon client connection to namespace `/ws/ledger`.
- **Payload Schema**: Emits clean tabular rows:
  ```json
  {
    "event": "transaction_created",
    "timestamp": "2026-10-12T08:00:00Z",
    "data": {
      "transaction_id": 42,
      "date": "2026-10-12",
      "amount": 2500.0,
      "type": "expense",
      "category": "Food",
      "account": "Meezan Bank",
      "description": "Groceries",
      "balance_after": 77500.0
    }
  }
  ```

---

## 2. Reporting Engines: ReportLab vs OpenPyXL

### A. ReportLab (PDF)
- **Why**: 100% pure Python, zero native OS dependencies (unlike WeasyPrint which requires GTK/Cairo).
- **Architecture**: `SimpleDocTemplate` with `io.BytesIO` buffer, custom table styles (`Table`, `TableStyle`), palette matching dark/clean financial theme, and executive summary header.
- **PKR Formatting**: Formats currency with commas (e.g. `PKR 85,000.00`) and includes AI composite advice score indicator.

### B. OpenPyXL (Excel `.xlsx`)
- **Why**: Native support for styled Excel workbooks, column auto-sizing, header fills, number formats (`"PKR" #,##0.00`).
- **Compatibility**: Direct import into Microsoft Excel, Google Sheets, Power BI, and BigQuery table loaders.

---

## 3. Subscription Leakage Algorithm
- **Detection Logic**: Group transactions by normalized description tokens (e.g., `netflix`, `spotify`, `gym`, `tapmad`, `nayatel`) and check intervals between successive occurrences.
- **Threshold**: Intervals of 28 to 32 days with variance <= 2 days flag a recurring subscription.
- **Price Creep Alert**: If price increases by >5% compared to the 3-month trailing average, flag as `Price Increase Detected`.
