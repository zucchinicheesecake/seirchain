from datetime import datetime

def get_address_activity(address, ledger, wallet_manager, depth=3):
    """Get recent activity for an address"""
    if not wallet_manager.wallet_exists(address):
        return {"error": "Address not found"}
    
    # Get wallet and transaction history
    wallet = wallet_manager.get_wallet(address)
    all_transactions = []
    
    # Scan ledger for transactions involving this address
    for triad in ledger.triads:
        for tx in getattr(triad, 'transactions', []):
            if tx.from_addr == address or tx.to_addr == address:
                all_transactions.append({
                    "tx_hash": tx.tx_hash,
                    "timestamp": datetime.fromtimestamp(tx.timestamp).isoformat(),
                    "direction": "out" if tx.from_addr == address else "in",
                    "amount": tx.amount,
                    "fee": tx.fee if tx.from_addr == address else 0,
                    "counterparty": tx.to_addr if tx.from_addr == address else tx.from_addr,
                    "triad_id": triad.triad_id
                })
    
    # Sort by timestamp descending
    all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Get latest transactions based on depth
    recent_tx = all_transactions[:depth] if depth > 0 else all_transactions
    
    return {
        "address": address,
        "balance": wallet.balance,
        "transaction_count": len(all_transactions),
        "recent_transactions": recent_tx
    }

def get_transaction_history(address, ledger, max_transactions=100):
    """Get full transaction history for an address"""
    history = []
    for triad in ledger.triads:
        for tx in getattr(triad, 'transactions', []):
            if tx.from_addr == address or tx.to_addr == address:
                history.append({
                    "tx_hash": tx.tx_hash,
                    "block": triad.triad_id,
                    "timestamp": tx.timestamp,
                    "from": tx.from_addr,
                    "to": tx.to_addr,
                    "value": tx.amount,
                    "fee": tx.fee
                })
                if len(history) >= max_transactions:
                    return history
    return history
