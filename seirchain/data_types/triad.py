import hashlib
import json # Import json for consistent transaction serialization

class Triad:
    def __init__(self, index, timestamp, transactions, nonce, previous_hash, hash, difficulty, miner_address):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions # List of transaction dictionaries
        self.nonce = nonce
        self.previous_hash = previous_hash
        self.hash = hash
        self.difficulty = difficulty
        self.miner_address = miner_address

    def calculate_hash(self):
        """Calculates the hash of the Triad."""
        # Ensure transactions are serialized consistently for hashing
        transaction_string = json.dumps(self.transactions, sort_keys=True)
        triad_string = f"{self.index}{self.previous_hash}{self.timestamp}{transaction_string}{self.nonce}{self.difficulty}{self.miner_address}"
        return hashlib.sha256(triad_string.encode('utf-8')).hexdigest()

    def to_dict(self):
        """Converts the Triad object to a dictionary for serialization."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'nonce': self.nonce,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'difficulty': self.difficulty,
            'miner_address': self.miner_address
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Triad object from a dictionary."""
        return cls(
            index=data['index'],
            timestamp=data['timestamp'],
            transactions=data['transactions'],
            nonce=data['nonce'],
            previous_hash=data['previous_hash'],
            hash=data['hash'],
            difficulty=data['difficulty'],
            miner_address=data['miner_address']
        )
