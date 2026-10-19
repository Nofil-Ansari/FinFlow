---
phase: 4
plan: 3
wave: 2
depends_on: [4.1, 4.2]
---

# Plan 4.3: Heuristic Subscription Leakage Scanner & Category Heatmaps

## Objective
Build an automated heuristic subscription leakage detection engine that flags 28–32 day billing cycles and price creeps, and upgrade the `/reports/` UI with interactive category spending heatmaps and WebSocket connection badges.

## Context
- .gsd/SPEC.md
- finance_app/app/reports/routes.py
- finance_app/app/templates/reports/index.html

## Tasks

<task type="auto">
  <name>Build Heuristic Subscription Leakage Detection Service</name>
  <files>finance_app/app/services/subscription_leakage.py</files>
  <action>
    1. Create `app/services/subscription_leakage.py` with `detect_subscription_leakage(user_id)`.
    2. Group debit transactions by normalized merchant text and analyze cadence variance.
    3. Identify:
       - Regular 28–32 day subscriptions (e.g. Netflix, Spotify, Gym, ISP).
       - Price creep (current amount > 1.05 * past average).
       - Duplicate/overlapping services in identical category.
    4. Return structured leakage report with total annual leakage PKR estimate.
  </action>
  <verify>python -c "from app.services.subscription_leakage import detect_subscription_leakage; print(callable(detect_subscription_leakage))"</verify>
  <done>Service identifies recurring cadence and price increases from raw transaction history.</done>
</task>

<task type="auto">
  <name>Upgrade Reports UI with Heatmaps, Leakage Widget & Export Buttons</name>
  <files>finance_app/app/templates/reports/index.html, finance_app/app/reports/routes.py</files>
  <action>
    1. Update `app/reports/routes.py` to pass subscription leakage and export parameters to template.
    2. In `app/templates/reports/index.html`:
       - Add Subscription Leakage banner card with savings potential in PKR.
       - Add Category Spending Heatmap / Breakdown chart.
       - Add Export Action toolbar: "📄 Download PDF Report" and "📊 Export Excel (.xlsx)".
       - Add Live WebSocket Sync status indicator ("🟢 Live Ledger Sync Active").
  </action>
  <verify>python -m unittest tests.test_reporting_and_sync.TestReportsUI</verify>
  <done>Reports page renders heatmap, leakage alert cards, export download triggers, and WebSocket status.</done>
</task>

## Success Criteria
- [ ] Users can see detected subscription leakage with PKR savings opportunities.
- [ ] One-click downloads for PDF and Excel reports available directly on `/reports/`.
- [ ] Real-time sync badge displayed on reports dashboard.
