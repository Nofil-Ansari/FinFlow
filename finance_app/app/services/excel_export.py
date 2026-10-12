"""OpenPyXL Excel Financial Statement Generator.

Produces high-fidelity spreadsheet workbooks formatted for:
- Executive financial reviews.
- Power Query automated refreshes.
- Google Sheets / BigQuery data connector imports.
"""
import io
from datetime import datetime, date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from ..models.transaction import Transaction
from ..models.financial_profile import FinancialProfile
from ..models.user import User
from ..extensions import db


def generate_ledger_excel(user_id: int, start_date: date = None, end_date: date = None) -> io.BytesIO:
    """Generate a styled multi-sheet Excel workbook in memory as BytesIO."""
    user = db.session.get(User, user_id)
    profile = FinancialProfile.query.filter_by(user_id=user_id).first()

    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.is_deleted == False
    )
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    transactions = query.order_by(Transaction.transaction_date.desc()).all()

    wb = openpyxl.Workbook()

    # Style definitions
    navy_fill = PatternFill(start_color='0F172A', end_color='0F172A', fill_type='solid')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    title_font = Font(name='Calibri', size=14, bold=True, color='0F172A')
    kpi_val_font = Font(name='Calibri', size=12, bold=True, color='1E293B')
    kpi_lbl_font = Font(name='Calibri', size=10, color='64748B')
    bold_font = Font(name='Calibri', size=11, bold=True)
    normal_font = Font(name='Calibri', size=11)
    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    # Sheet 1: Summary KPI Dashboard
    ws_summary = wb.active
    ws_summary.title = 'Executive Summary'
    ws_summary.views.sheetView[0].showGridLines = True

    total_income = sum(float(t.amount) for t in transactions if t.transaction_type == 'income')
    total_expense = sum(float(t.amount) for t in transactions if t.transaction_type == 'expense')
    net_savings = total_income - total_expense
    savings_rate_pct = (net_savings / total_income * 100) if total_income > 0 else 0.0
    health_score = profile.financial_advice_score if profile else 50

    ws_summary['A1'] = 'FinanceFlow - Financial Executive Summary'
    ws_summary['A1'].font = title_font
    ws_summary['A2'] = f'Report Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")} | User: {user.username if user else ""}'
    ws_summary['A2'].font = kpi_lbl_font

    summary_cards = [
        ('Total Income (PKR)', total_income, '#,##0.00'),
        ('Total Expenses (PKR)', total_expense, '#,##0.00'),
        ('Net Savings (PKR)', net_savings, '#,##0.00'),
        ('Savings Rate', savings_rate_pct / 100.0, '0.0%'),
        ('AI Health Score', health_score, '0'),
        ('Total Transactions', len(transactions), '#,##0'),
    ]

    row_idx = 5
    for label, val, num_fmt in summary_cards:
        ws_summary.cell(row=row_idx, column=1, value=label).font = kpi_lbl_font
        c = ws_summary.cell(row=row_idx, column=2, value=val)
        c.font = kpi_val_font
        c.number_format = num_fmt
        c.alignment = Alignment(horizontal='right')
        ws_summary.cell(row=row_idx, column=1).border = thin_border
        ws_summary.cell(row=row_idx, column=2).border = thin_border
        row_idx += 1

    ws_summary.column_dimensions['A'].width = 28
    ws_summary.column_dimensions['B'].width = 22

    # Sheet 2: Raw Ledger Statement (Power Query & BigQuery ready)
    ws_ledger = wb.create_sheet(title='Raw Ledger')
    ws_ledger.views.sheetView[0].showGridLines = True
    ws_ledger.freeze_panes = 'A2'

    headers = [
        'Transaction ID',
        'Date',
        'Description',
        'Category',
        'Account',
        'Type',
        'Amount (PKR)',
        'Currency',
        'Exchange Rate',
        'Amount in Base',
    ]

    for col_num, h_text in enumerate(headers, 1):
        cell = ws_ledger.cell(row=1, column=col_num, value=h_text)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal='center' if col_num in (1, 2, 6, 8) else 'left')

    for row_idx, txn in enumerate(transactions, 2):
        ws_ledger.cell(row=row_idx, column=1, value=txn.transaction_id).alignment = Alignment(horizontal='center')
        ws_ledger.cell(row=row_idx, column=2, value=txn.transaction_date.strftime('%Y-%m-%d')).alignment = Alignment(horizontal='center')
        ws_ledger.cell(row=row_idx, column=3, value=txn.description or '')
        ws_ledger.cell(row=row_idx, column=4, value=txn.category.name if txn.category else 'Uncategorized')
        ws_ledger.cell(row=row_idx, column=5, value=txn.account.account_name if txn.account else 'Primary')
        ws_ledger.cell(row=row_idx, column=6, value=txn.transaction_type.capitalize()).alignment = Alignment(horizontal='center')
        
        amt_cell = ws_ledger.cell(row=row_idx, column=7, value=float(txn.amount))
        amt_cell.number_format = '#,##0.00'
        if txn.transaction_type == 'expense':
            amt_cell.font = Font(name='Calibri', size=11, color='DC2626')
        else:
            amt_cell.font = Font(name='Calibri', size=11, color='16A34A')

        ws_ledger.cell(row=row_idx, column=8, value=txn.currency or 'PKR').alignment = Alignment(horizontal='center')
        rate_cell = ws_ledger.cell(row=row_idx, column=9, value=float(txn.exchange_rate or 1))
        rate_cell.number_format = '0.0000'
        base_cell = ws_ledger.cell(row=row_idx, column=10, value=float(txn.amount_in_base))
        base_cell.number_format = '#,##0.00'

        for col_num in range(1, 11):
            ws_ledger.cell(row=row_idx, column=col_num).border = thin_border

    # Auto-adjust column widths
    for col in ws_ledger.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_ledger.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

