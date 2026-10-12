"""ReportLab PDF Financial Statement Generator.

Generates an executive monthly financial intelligence report containing:
1. Executive AI Health Summary (Health Score, Savings Rate, Cash Flow, Advice).
2. Tabular itemized ledger with clean alternating row styling.
"""
import io
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from ..models.transaction import Transaction
from ..models.financial_profile import FinancialProfile
from ..models.user import User
from ..extensions import db


def generate_monthly_pdf(user_id: int, month: int = None, year: int = None) -> io.BytesIO:
    """Generate a high-fidelity monthly statement in memory as BytesIO."""
    now = datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year

    user = db.session.get(User, user_id)
    profile = FinancialProfile.query.filter_by(user_id=user_id).first()

    # Query transactions for specified period
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.is_deleted == False,
        db.extract('year', Transaction.transaction_date) == target_year,
        db.extract('month', Transaction.transaction_date) == target_month,
    ).order_by(Transaction.transaction_date.desc())
    transactions = query.all()

    # Calculate month metrics
    total_income = sum(float(t.amount) for t in transactions if t.transaction_type == 'income')
    total_expense = sum(float(t.amount) for t in transactions if t.transaction_type == 'expense')
    net_savings = total_income - total_expense
    savings_rate_pct = (net_savings / total_income * 100) if total_income > 0 else 0.0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6,
    )
    normal_style = ParagraphStyle(
        'ReportNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
    )
    kpi_val_style = ParagraphStyle(
        'KPIVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        alignment=1,
    )
    kpi_lbl_style = ParagraphStyle(
        'KPILbl',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
    )

    story = []

    # Header
    month_name = date(target_year, target_month, 1).strftime('%B %Y')
    story.append(Paragraph(f'FinanceFlow - Financial Statement', title_style))
    user_name = user.username if user else 'Account Holder'
    story.append(Paragraph(f'Statement Period: {month_name}  |  Generated for: {user_name} ({user.email if user else ""})', subtitle_style))
    story.append(Spacer(1, 14))

    # Executive Summary Card Grid (Table)
    health_score = profile.financial_advice_score if profile else 50
    stress_level = profile.financial_stress_level if profile else 'Medium'
    cash_flow = profile.cash_flow_status if profile else ('Positive' if net_savings >= 0 else 'Negative')

    kpi_data = [
        [
            Paragraph(f'PKR {total_income:,.0f}', kpi_val_style),
            Paragraph(f'PKR {total_expense:,.0f}', kpi_val_style),
            Paragraph(f'PKR {net_savings:,.0f}', kpi_val_style),
            Paragraph(f'{health_score}/100', kpi_val_style),
        ],
        [
            Paragraph('Total Income', kpi_lbl_style),
            Paragraph('Total Expenses', kpi_lbl_style),
            Paragraph(f'Net Savings ({savings_rate_pct:.1f}%)', kpi_lbl_style),
            Paragraph(f'AI Health ({stress_level} Stress)', kpi_lbl_style),
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # Executive AI Insights Box
    story.append(Paragraph('Executive AI Advisor Assessment', section_heading))
    ai_bullet_1 = f'  Health Score: Your composite financial score is <b>{health_score}/100</b> with a {cash_flow.lower()} monthly trajectory.'
    ai_bullet_2 = f'  Savings Rate: Current monthly savings rate is <b>{savings_rate_pct:.1f}%</b> (Recommended: 20%+ for long-term wealth stability in Pakistan).'
    if net_savings < 0:
        ai_bullet_3 = '  Alert: Spending exceeded income this month. Review non-essential categories to prevent emergency fund depletion.'
    else:
        ai_bullet_3 = '  Cash Flow: Healthy surplus achieved. Consider allocating excess capital toward KSE-30 mutual funds or National Savings Certificates.'

    insights_data = [
        [Paragraph(ai_bullet_1, normal_style)],
        [Paragraph(ai_bullet_2, normal_style)],
        [Paragraph(ai_bullet_3, normal_style)],
    ]
    insights_table = Table(insights_data, colWidths=[540])
    insights_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(insights_table)
    story.append(Spacer(1, 14))

    # Itemized Ledger Table
    story.append(Paragraph(f'Itemized Ledger ({len(transactions)} transactions)', section_heading))

    table_rows = [[
        Paragraph('<b>Date</b>', normal_style),
        Paragraph('<b>Description</b>', normal_style),
        Paragraph('<b>Category</b>', normal_style),
        Paragraph('<b>Account</b>', normal_style),
        Paragraph('<b>Type</b>', normal_style),
        Paragraph('<b>Amount (PKR)</b>', normal_style),
    ]]

    for txn in transactions:
        cat_name = txn.category.name if txn.category else 'Uncategorized'
        acct_name = txn.account.account_name if txn.account else 'Primary'
        amt_color = '#16a34a' if txn.transaction_type == 'income' else '#dc2626'
        amt_text = f"<font color='{amt_color}'><b>{'+' if txn.transaction_type == 'income' else '-'}{float(txn.amount):,.2f}</b></font>"
        
        table_rows.append([
            Paragraph(txn.transaction_date.strftime('%Y-%m-%d'), normal_style),
            Paragraph((txn.description or 'N/A')[:32], normal_style),
            Paragraph(cat_name[:18], normal_style),
            Paragraph(acct_name[:18], normal_style),
            Paragraph(txn.transaction_type.capitalize(), normal_style),
            Paragraph(amt_text, normal_style),
        ])

    if len(transactions) == 0:
        table_rows.append([
            Paragraph('No transactions recorded for this billing cycle.', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
            Paragraph('', normal_style),
        ])

    ledger_table = Table(table_rows, colWidths=[65, 140, 95, 90, 60, 90])
    ledger_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]
    # Header text white override
    for c in range(6):
        ledger_style.append(('TEXTCOLOR', (c, 0), (c, 0), colors.white))

    # Alternating row background
    for r in range(1, len(table_rows)):
        if r % 2 == 0:
            ledger_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor('#f8fafc')))

    ledger_table.setStyle(TableStyle(ledger_style))
    story.append(ledger_table)

    doc.build(story)
    buffer.seek(0)
    return buffer

