import hashlib
import time

class Triad:
    def __init__(self, triad_id, depth, hash_value, parent_hashes):
        self.triad_id = triad_id
        self.depth = depth
        self.hash_value = hash_value
        self.parent_hashes = parent_hashes
        
    def __repr__(self):
        return f"Triad(id={self.triad_id[:8]}, depth={self.depth})"

class Transaction:
    def __init__(self, transaction_data, tx_hash, timestamp):
        self.transaction_data = transaction_data
        self.tx_hash = tx_hash
        self.timestamp = timestamp
        
    def __repr__(self):
        return f"Transaction(hash={self.tx_hash[:8]})"

class Triangle:
    def __init__(self, triad, coordinates):
        self.triad = triad
        self.coordinates = coordinates
        self.transactions = []
        
    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        
    def get_transactions(self):
        return self.transactions
        
    def __repr__(self):
        return f"Triangle(triad={self.triad}, trans={len(self.transactions)})"
