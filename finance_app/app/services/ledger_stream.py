"""Real-time ledger WebSocket streaming service.

Provides authenticated WebSocket namespace at /ws/ledger that broadcasts
transaction lifecycle events (create, update, delete) to connected clients.
Designed for integration with Excel Power Query, Google Sheets, and BigQuery
streaming ingest pipelines.
"""
import json
import logging
from datetime import datetime
from flask import request
from flask_login import current_user
from flask_socketio import Namespace, emit, disconnect, join_room, leave_room

logger = logging.getLogger(__name__)


class LedgerNamespace(Namespace):
    """WebSocket namespace for real-time ledger streaming at /ws/ledger."""

    def on_connect(self):
        """Authenticate client on WebSocket connection.

        Requires the user to be authenticated via Flask-Login session cookie
        or an auth_token query parameter matching the user's session.
        """
        if not current_user.is_authenticated:
            logger.warning('Unauthenticated WebSocket connection attempt')
            disconnect()
            return False

        user_room = f'user_{current_user.user_id}'
        join_room(user_room)
        logger.info(f'WebSocket connected: user {current_user.user_id}')
        emit('ledger_status', {
            'status': 'connected',
            'user_id': current_user.user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Live ledger sync active'
        })

    def on_disconnect(self):
        """Handle client disconnection."""
        if current_user.is_authenticated:
            user_room = f'user_{current_user.user_id}'
            leave_room(user_room)
            logger.info(f'WebSocket disconnected: user {current_user.user_id}')

    def on_ping(self, data=None):
        """Respond to client ping for connection health checks."""
        emit('pong', {'timestamp': datetime.utcnow().isoformat()})


def broadcast_ledger_event(user_id, event_type, transaction_data):
    """Broadcast a ledger event to all connected clients of a specific user.

    Args:
        user_id: The user ID whose clients should receive the event.
        event_type: One of 'transaction_created', 'transaction_updated',
                    'transaction_deleted'.
        transaction_data: Dictionary containing the transaction row snapshot
                         with keys: transaction_id, date, description,
                         category, account, type, amount, currency, balance.
    """
    from ..extensions import socketio

    payload = {
        'event': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'data': transaction_data,
    }

    user_room = f'user_{user_id}'
    socketio.emit(
        'ledger_event',
        payload,
        namespace='/ws/ledger',
        room=user_room,
    )
    logger.info(f'Broadcast {event_type} to user {user_id}')


def build_transaction_snapshot(txn):
    """Build a tabular row snapshot from a Transaction model instance.

    Returns a dict suitable for spreadsheet row insertion with all columns
    needed by external analytics tools.
    """
    return {
        'transaction_id': txn.transaction_id,
        'date': txn.transaction_date.isoformat() if txn.transaction_date else None,
        'description': txn.description or '',
        'category': txn.category.name if txn.category else 'Uncategorized',
        'category_icon': txn.category.icon if txn.category else '',
        'account': txn.account.account_name if txn.account else '',
        'type': txn.transaction_type,
        'amount': float(txn.amount),
        'currency': txn.currency or 'PKR',
        'exchange_rate': float(txn.exchange_rate or 1),
        'amount_base': txn.amount_in_base,
        'is_deleted': txn.is_deleted,
    }
