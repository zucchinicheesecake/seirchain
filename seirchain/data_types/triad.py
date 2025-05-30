import hashlib
import json
import time

class Triad:
    MAX_CHILD_CAPACITY = 3 # This should align with config.MAX_CHILD_CAPACITY

    def __init__(self, triad_id, depth, parent_hashes, transactions, nonce, difficulty, miner_address, timestamp=None, current_hash=None, child_hashes=None):
        self.triad_id = triad_id
        self.depth = depth
        self.parent_hashes = sorted(parent_hashes) # Ensure consistent hashing
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.transactions = transactions # List of TransactionNode objects
        self.nonce = nonce
        self.difficulty = difficulty
        self.miner_address = miner_address
        self.hash = current_hash if current_hash is not None else self.calculate_hash() # Calculate hash on init if not provided
        self.child_hashes = child_hashes if child_hashes is not None else [] # To be populated by ledger

    def calculate_hash(self):
        # Ensure transactions are sorted for consistent hashing
        # Convert TransactionNode objects to dictionaries for hashing
        transactions_data = [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.transactions]
        transactions_data_sorted = sorted(transactions_data, key=lambda x: x.get('tx_id', '')) # Sort by tx_id

        triad_string = f"{self.triad_id}" \
                       f"{self.depth}" \
                       f"{json.dumps(self.parent_hashes, sort_keys=True)}" \
                       f"{self.timestamp}" \
                       f"{json.dumps(transactions_data_sorted, sort_keys=True)}" \
                       f"{self.nonce}" \
                       f"{self.difficulty}" \
                       f"{self.miner_address}"
        
        return hashlib.sha256(triad_string.encode('utf-8')).hexdigest()

    def add_child_hash(self, child_hash):
        """Adds a child hash to this triad, if capacity allows."""
        if child_hash not in self.child_hashes and len(self.child_hashes) < self.MAX_CHILD_CAPACITY:
            self.child_hashes.append(child_hash)
            return True
        return False

    def is_full(self):
        """Checks if the triad has reached its maximum child capacity."""
        return len(self.child_hashes) >= self.MAX_CHILD_CAPACITY

    def to_dict(self):
        """Converts the Triad object to a dictionary for serialization."""
        return {
            "triad_id": self.triad_id,
            "depth": self.depth,
            "parent_hashes": self.parent_hashes,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.transactions], # Convert transactions to dicts
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "miner_address": self.miner_address,
            "hash": self.hash,
            "child_hashes": self.child_hashes
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Triad object from a dictionary."""
        # Import locally to avoid circular dependency issues if TransactionNode also imports Triad
        from seirchain.data_types.transaction_node import TransactionNode 

        # Convert transaction dictionaries back to TransactionNode objects
        transactions = [TransactionNode.from_dict(tx_data) for tx_data in data.get("transactions", [])]
        
        triad = cls(
            triad_id=data["triad_id"],
            depth=data["depth"],
            parent_hashes=data.get("parent_hashes", []), # Use .get with default for robustness
            transactions=transactions,
            nonce=data["nonce"],
            difficulty=data["difficulty"],
            miner_address=data["miner_address"],
            timestamp=data.get("timestamp"), # Pass timestamp from data
            current_hash=data.get("hash"),     # Pass hash from data
            child_hashes=data.get("child_hashes", []) # Pass child_hashes from data
        )
        return triad
