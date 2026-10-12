import csv
import io
from datetime import date, datetime
from calendar import monthrange
from collections import defaultdict
from flask import render_template, request, Response, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, case
from . import reports_bp
from ..extensions import db
from ..models.transaction import Transaction
from ..models.category import Category
from ..models.audit_log import AuditLog
from ..services.pdf_export import generate_monthly_pdf
from ..services.excel_export import generate_ledger_excel
from ..services.subscription_leakage import detect_subscription_leakage


@reports_bp.route('/')
@login_required
def index():
    leakage = detect_subscription_leakage(current_user.user_id)
    
    # Category spending breakdown for heatmap/charts
    category_rows = db.session.query(
        Category.name,
        Category.icon,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.transaction_id).label('count')
    ).join(Transaction, Transaction.category_id == Category.category_id).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False
    ).group_by(Category.name, Category.icon).order_by(func.sum(Transaction.amount).desc()).limit(8).all()
    
    categories = [{
        'name': r.name,
        'icon': r.icon or '🏷️',
        'total': float(r.total),
        'count': r.count
    } for r in category_rows]
    
    now = datetime.utcnow()
    return render_template(
        'reports/index.html',
        leakage=leakage,
        categories=categories,
        current_month=now.month,
        current_year=now.year
    )


@reports_bp.route('/monthly')
@login_required
def monthly():
    """Monthly income vs expense summary (cross-DB compatible)."""
    transactions = Transaction.query.filter_by(
        user_id=current_user.user_id, is_deleted=False
    ).order_by(Transaction.transaction_date.desc()).all()

    # Group by month in Python (avoids date_trunc)
    month_data = defaultdict(lambda: {'income': 0, 'expense': 0})
    for txn in transactions:
        key = txn.transaction_date.replace(day=1)
        if txn.transaction_type == 'income':
            month_data[key]['income'] += float(txn.amount)
        else:
            month_data[key]['expense'] += float(txn.amount)

    data = []
    for month_key in sorted(month_data.keys(), reverse=True):
        vals = month_data[month_key]
        data.append({
            'month': month_key.strftime('%B %Y'),
            'income': vals['income'],
            'expense': vals['expense'],
            'savings': vals['income'] - vals['expense'],
        })

    return render_template('reports/monthly.html', data=data)


@reports_bp.route('/category')
@login_required
def category_breakdown():
    """Spending breakdown by category."""
    results = db.session.query(
        Category.name,
        Category.icon,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.transaction_id).label('count'),
        func.round(func.avg(Transaction.amount), 2).label('avg'),
    ).join(Transaction, Transaction.category_id == Category.category_id).filter(
        Transaction.user_id == current_user.user_id,
        Transaction.transaction_type == 'expense',
        Transaction.is_deleted == False,
    ).group_by(Category.name, Category.icon).order_by(func.sum(Transaction.amount).desc()).all()

    data = [{
        'name': r.name,
        'icon': r.icon,
        'total': float(r.total),
        'count': r.count,
        'avg': float(r.avg) if r.avg else 0,
    } for r in results]

    return render_template('reports/category.html', data=data)


@reports_bp.route('/export/csv')
@login_required
def export_csv():
    """Export all transactions as CSV."""
    transactions = Transaction.query.filter_by(
        user_id=current_user.user_id, is_deleted=False
    ).order_by(Transaction.transaction_date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Description', 'Account'])

    for txn in transactions:
        cat_name = txn.category.name if txn.category else ''
        acct_name = txn.account.account_name if txn.account else ''
        writer.writerow([
            txn.transaction_date.isoformat(),
            txn.transaction_type,
            cat_name,
            str(txn.amount),
            txn.description or '',
            acct_name,
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=transactions_{date.today().isoformat()}.csv'}
    )


@reports_bp.route('/export/pdf')
@login_required
def export_pdf():
    """Export executive financial intelligence report as PDF."""
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    pdf_buffer = generate_monthly_pdf(current_user.user_id, month=month, year=year)
    target_year = year or datetime.utcnow().year
    target_month = month or datetime.utcnow().month
    filename = f'FinanceFlow_Statement_{target_year}_{target_month:02d}.pdf'
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route('/export/excel')
@login_required
def export_excel():
    """Export structured ledger and KPIs as an Excel workbook (.xlsx)."""
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    
    start_date = None
    end_date = None
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if end_str:
        try:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    excel_buffer = generate_ledger_excel(current_user.user_id, start_date=start_date, end_date=end_date)
    filename = f'FinanceFlow_Ledger_{date.today().isoformat()}.xlsx'
    
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@reports_bp.route('/audit')
@login_required
def audit_log():
    """View audit log."""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.filter_by(
        user_id=current_user.user_id
    ).order_by(AuditLog.changed_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template('reports/audit.html', logs=logs)
