import re
from datetime import datetime, timedelta
from collections import defaultdict
from ..models.transaction import Transaction
from ..extensions import db


def _normalize_merchant(description: str) -> str:
    """Normalize transaction description by stripping numbers, dates, reference codes."""
    if not description:
        return 'unknown'
    text = description.lower()
    text = re.sub(r'[0-9]+', '', text)
    text = re.sub(r'[#\-_/:\*]+', ' ', text)
    tokens = [t.strip() for t in text.split() if len(t.strip()) > 2]
    return ' '.join(tokens[:3]) if tokens else text.strip()


def detect_subscription_leakage(user_id: int) -> dict:
    """Scan debit transactions for recurring subscriptions, price creep, and dormant leakage.

    Returns a dictionary with:
    - active_subscriptions: list of detected recurring services
    - price_creeps: subscriptions where price increased by >5%
    - potential_annual_leakage_pkr: estimated PKR savings if optimized
    - total_monthly_commitment_pkr: total active monthly subscription run-rate
    """
    transactions = Transaction.query.filter_by(
        user_id=user_id,
        transaction_type='expense',
        is_deleted=False
    ).order_by(Transaction.transaction_date.asc()).all()

    # Group transactions by normalized merchant name
    merchant_groups = defaultdict(list)
    for txn in transactions:
        norm = _normalize_merchant(txn.description)
        if norm:
            merchant_groups[norm].append(txn)

    active_subscriptions = []
    price_creeps = []
    total_monthly_commitment = 0.0
    total_annual_leakage = 0.0

    for merchant, txns in merchant_groups.items():
        if len(txns) < 2:
            continue

        # Calculate intervals in days between consecutive transactions
        intervals = []
        for i in range(1, len(txns)):
            diff = (txns[i].transaction_date - txns[i-1].transaction_date).days
            intervals.append(diff)

        # Check if intervals cluster around 28-32 days (monthly) or 6-8 days (weekly)
        monthly_matches = [d for d in intervals if 25 <= d <= 35]
        is_monthly = len(monthly_matches) >= 1 and (len(monthly_matches) / len(intervals) >= 0.5)

        if is_monthly:
            amounts = [float(t.amount) for t in txns]
            latest_amount = amounts[-1]
            earlier_amounts = amounts[:-1]
            avg_past = sum(earlier_amounts) / len(earlier_amounts) if earlier_amounts else latest_amount

            category_name = txns[-1].category.name if txns[-1].category else 'Entertainment'
            last_billed = txns[-1].transaction_date.strftime('%Y-%m-%d')

            sub_info = {
                'merchant': txns[-1].description or merchant.title(),
                'normalized': merchant,
                'category': category_name,
                'monthly_amount': latest_amount,
                'billing_cycle_days': int(sum(monthly_matches) / len(monthly_matches)),
                'billing_count': len(txns),
                'last_billed': last_billed,
            }
            active_subscriptions.append(sub_info)
            total_monthly_commitment += latest_amount

            # Detect price creep (> 5% increase over past average)
            if latest_amount > (avg_past * 1.05) and (latest_amount - avg_past) >= 100:
                creep_diff = latest_amount - avg_past
                price_creeps.append({
                    'merchant': sub_info['merchant'],
                    'old_amount': avg_past,
                    'new_amount': latest_amount,
                    'increase_pkr': creep_diff,
                    'increase_pct': round(((latest_amount - avg_past) / avg_past) * 100, 1),
                })
                total_annual_leakage += (creep_diff * 12)

    # If user has >= 4 subscriptions, estimate 1 redundant leakage service
    if len(active_subscriptions) >= 4:
        lowest_subs = sorted(active_subscriptions, key=lambda s: s['monthly_amount'])
        total_annual_leakage += (lowest_subs[0]['monthly_amount'] * 12)

    return {
        'active_subscriptions': active_subscriptions,
        'subscription_count': len(active_subscriptions),
        'price_creeps': price_creeps,
        'total_monthly_commitment_pkr': round(total_monthly_commitment, 2),
        'potential_annual_leakage_pkr': round(total_annual_leakage, 2),
    }
