import unittest
from datetime import date, datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.financial_profile import FinancialProfile
from app.services.pdf_export import generate_monthly_pdf
from app.services.excel_export import generate_ledger_excel
from app.services.subscription_leakage import detect_subscription_leakage
from app.services.ledger_stream import (
    build_transaction_snapshot,
    broadcast_ledger_event,
)


class TestReportingAndSync(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Seed test user
        self.user = User(name="Report User", email="report@example.com")
        self.user.set_password("Password123!")
        db.session.add(self.user)
        db.session.commit()

        # Seed profile
        self.profile = FinancialProfile(
            user_id=self.user.user_id, monthly_income_pkr=120000.0
        )
        self.profile.compute_score()
        db.session.add(self.profile)

        # Seed account
        self.account = Account(
            user_id=self.user.user_id, account_name="Meezan Main", account_type="bank"
        )
        db.session.add(self.account)
        db.session.commit()

        # Seed categories
        self.cat_util = Category(
            name="Utilities", icon="⚡", type="expense", user_id=self.user.user_id
        )
        self.cat_ent = Category(
            name="Entertainment", icon="🎬", type="expense", user_id=self.user.user_id
        )
        self.cat_sal = Category(
            name="Salary", icon="💼", type="income", user_id=self.user.user_id
        )
        db.session.add_all([self.cat_util, self.cat_ent, self.cat_sal])
        db.session.commit()

        # Seed recurring subscription transactions (30 day interval with price creep)
        t1 = Transaction(
            user_id=self.user.user_id,
            account_id=self.account.account_id,
            category_id=self.cat_ent.category_id,
            amount=1200.0,
            transaction_type="expense",
            description="Netflix Subscription",
            transaction_date=date(2026, 1, 15),
        )
        t2 = Transaction(
            user_id=self.user.user_id,
            account_id=self.account.account_id,
            category_id=self.cat_ent.category_id,
            amount=1200.0,
            transaction_type="expense",
            description="Netflix Subscription",
            transaction_date=date(2026, 2, 14),
        )
        t3 = Transaction(
            user_id=self.user.user_id,
            account_id=self.account.account_id,
            category_id=self.cat_ent.category_id,
            amount=1500.0,
            transaction_type="expense",
            description="Netflix Subscription",
            transaction_date=date(2026, 3, 16),
        )
        # Seed an income transaction
        t4 = Transaction(
            user_id=self.user.user_id,
            account_id=self.account.account_id,
            category_id=self.cat_sal.category_id,
            amount=120000.0,
            transaction_type="income",
            description="Monthly Salary",
            transaction_date=date(2026, 3, 1),
        )
        db.session.add_all([t1, t2, t3, t4])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_pdf_export_generation(self):
        """PDF generation should return valid PDF header bytes."""
        buf = generate_monthly_pdf(self.user.user_id, month=3, year=2026)
        content = buf.getvalue()
        self.assertTrue(len(content) > 1000)
        self.assertTrue(content.startswith(b"%PDF"))

    def test_excel_export_generation(self):
        """Excel generation should produce valid openpyxl xlsx binary with expected sheets."""
        buf = generate_ledger_excel(self.user.user_id)
        content = buf.getvalue()
        self.assertTrue(len(content) > 1000)
        # XLSX is a zip format starting with PK
        self.assertTrue(content.startswith(b"PK"))

    def test_subscription_leakage_scanner(self):
        """Heuristic leakage scanner should identify recurring subscription and price creep."""
        res = detect_subscription_leakage(self.user.user_id)
        self.assertGreaterEqual(res["subscription_count"], 1)
        self.assertEqual(
            res["active_subscriptions"][0]["normalized"], "netflix subscription"
        )
        self.assertEqual(res["active_subscriptions"][0]["monthly_amount"], 1500.0)
        # Check price creep detection
        self.assertGreaterEqual(len(res["price_creeps"]), 1)
        creep = res["price_creeps"][0]
        self.assertEqual(creep["old_amount"], 1200.0)
        self.assertEqual(creep["new_amount"], 1500.0)
        self.assertEqual(creep["increase_pkr"], 300.0)

    def test_ledger_snapshot_and_broadcast(self):
        """build_transaction_snapshot returns proper tabular dict structure."""
        txn = Transaction.query.filter_by(description="Netflix Subscription").first()
        snap = build_transaction_snapshot(txn)
        self.assertEqual(snap["transaction_id"], txn.transaction_id)
        self.assertEqual(snap["type"], "expense")
        self.assertEqual(snap["amount"], 1200.0)
        self.assertEqual(snap["category"], "Entertainment")
        self.assertEqual(snap["account"], "Meezan Main")

        # Broadcast should execute without uncaught exceptions
        broadcast_ledger_event(self.user.user_id, "transaction_created", snap)


if __name__ == "__main__":
    unittest.main()
