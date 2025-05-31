import hashlib
import time

class Triad:
    def __init__(self, triad_id, depth, hash_value, parent_hashes):
        self.triad_id = triad_id
        self.depth = depth
        self.hash_value = hash_value
        self.parent_hashes = parent_hashes
        self.child_hashes = []  # Add child_hashes attribute

    def add_child(self, child_triad):
        if not hasattr(self, 'child_hashes'):
            self.child_hashes = []
        self.child_hashes.append(child_triad.hash_value)
        
    def __repr__(self):
        return f"Triad(id={self.triad_id[:8]}, depth={self.depth})"

class Transaction:
    def __init__(self, transaction_data, tx_hash, timestamp):
        self.transaction_data = transaction_data
        self.tx_hash = tx_hash
        self.timestamp = timestamp
        
    def __repr__(self):
        return f"Transaction(hash={self.tx_hash[:8]})"

from typing import List, Tuple, Any

class Triangle:
    def __init__(self, triad: 'Triad', coordinates: Tuple[int, int]):
        """
        Triangle wraps a Triad with coordinates and transactions.
        """
        self.triad = triad
        self.coordinates = coordinates
        self.transactions: List[Any] = []
        
    def add_transaction(self, transaction: Any) -> None:
        """
        Add a transaction to this triangle.
        """
        self.transactions.append(transaction)
        
    def get_transactions(self) -> List[Any]:
        """
        Get the list of transactions in this triangle.
        """
        return self.transactions

    def get_hash(self) -> str:
        """
        Convenience method to get the triad's hash_value.
        """
        return self.triad.hash_value
        
    def __repr__(self) -> str:
        return f"Triangle(triad={self.triad}, trans={len(self.transactions)})"
