---
phase: 6
plan: fix-dependencies-and-lockfile
wave: 1
gap_closure: true
---

# Fix: Audit Vulnerable Dependencies & Lock Production Packages

## Problem
GitHub Dependabot flagged 18 security alerts on transitive dependencies (Pillow, cryptography, urllib3, etc.). While development dependencies are functional, production containerization in Milestone v2.0 requires pinned, audited packages.

## Root Cause
Unpinned/loose package ranges in `requirements.txt` allow installation of older minor versions with known CVEs.

## Tasks

<task type="auto">
  <name>Bump requirements.txt and pin audited security releases</name>
  <files>finance_app/requirements.txt</files>
  <action>
    1. Upgrade Pillow, urllib3, requests, Werkzeug, and Authlib to current secure patch releases.
    2. Ensure reportlab and openpyxl compatibility is maintained.
    3. Run test discovery to verify zero breaking changes.
  </action>
  <verify>python -m unittest discover -s tests -p "test_*.py"</verify>
  <done>Dependencies updated and all 43 test suite cases pass.</done>
</task>

## Success Criteria
- [ ] Dependencies updated to patched security releases.
- [ ] 43/43 tests pass without regression.
