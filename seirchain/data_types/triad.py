# seirchain/data_types/triad.py
import hashlib
import json
import time

class Triad:
    """
    Represents a Triad (block) in the SeirChain's fractal ledger.
    Each Triad can have multiple parent hashes, allowing for the branching structure.
    """
    def __init__(self, triad_id, depth, parent_hashes, transactions, nonce, hash, difficulty, miner_address):
        self.triad_id = triad_id # A unique identifier for this Triad
        self.depth = depth # The depth level in the fractal matrix
        self.parent_hashes = parent_hashes if parent_hashes is not None else [] # List of parent Triad hashes
        self.transactions = transactions # List of TransactionNode objects
        self.nonce = nonce
        self.timestamp = time.time() # Timestamp of creation
        self.hash = hash # The calculated hash of this Triad
        self.difficulty = difficulty
        self.miner_address = miner_address
        self.child_hashes = [] # List to store hashes of Triads that reference this Triad as a parent

    def calculate_hash(self):
        """
        Calculates the SHA256 hash of the Triad, incorporating parent hashes.
        """
        transactions_data = [tx.to_dict() for tx in self.transactions]
        transaction_string = json.dumps(transactions_data, sort_keys=True)
        
        parent_hashes_string = json.dumps(sorted(self.parent_hashes), sort_keys=True)

        triad_string = f"{self.triad_id}{self.depth}{parent_hashes_string}{self.timestamp}{transaction_string}{self.nonce}{self.difficulty}{self.miner_address}"
        return hashlib.sha256(triad_string.encode('utf-8')).hexdigest()

    def add_child_hash(self, child_hash):
        """Adds a child Triad's hash to this Triad's list of children."""
        if child_hash not in self.child_hashes:
            self.child_hashes.append(child_hash)
            return True
        return False

    def is_full(self):
        """Checks if this Triad has reached its maximum number of children (3)."""
        return len(self.child_hashes) >= 3 # Triads can have up to 3 children

    def to_dict(self):
        """Converts the Triad object to a dictionary for serialization."""
        return {
            'triad_id': self.triad_id,
            'depth': self.depth,
            'parent_hashes': self.parent_hashes,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'nonce': self.nonce,
            'timestamp': self.timestamp,
            'hash': self.hash,
            'difficulty': self.difficulty,
            'miner_address': self.miner_address,
            'child_hashes': self.child_hashes
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Triad object from a dictionary."""
        from seirchain.data_types.transaction_node import TransactionNode # Import here to avoid circular dependency
        transactions = [TransactionNode.from_dict(tx_data) for tx_data in data.get('transactions', [])]
        
        instance = cls(
            triad_id=data['triad_id'],
            depth=data['depth'],
            parent_hashes=data.get('parent_hashes', []),
            transactions=transactions,
            nonce=data['nonce'],
            hash=data['hash'],
            difficulty=data['difficulty'],
            miner_address=data['miner_address']
        )
        instance.child_hashes = data.get('child_hashes', [])
        return instance

    def __repr__(self):
        return (f"Triad(id={self.triad_id[:8]}..., depth={self.depth}, "
                f"parents={len(self.parent_hashes)}, children={len(self.child_hashes)}, "
                f"hash={self.hash[:8]}...)")

