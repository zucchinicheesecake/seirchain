import time
import hashlib
import json # Import json for consistent string representation

class Transaction:
    def __init__(self, sender, receiver, amount, fee, timestamp=None, signature=None):
        self.sender = sender
        self.receiver = receiver
        self.amount = float(amount)
        self.fee = float(fee)
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = signature # In a real system, this would be a cryptographic signature

    def calculate_hash(self):
        """Calculates a SHA256 hash of the transaction's core data."""
        transaction_string = f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.timestamp}"
        return hashlib.sha256(transaction_string.encode()).hexdigest()

    def to_dict(self):
        """Converts the transaction to a dictionary for serialization."""
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "fee": self.fee,
            "timestamp": self.timestamp,
            "signature": self.signature
        }

    def to_dict_string(self):
        """Returns a JSON string representation of the transaction's dictionary, sorted for consistent hashing."""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self):
        return f"Transaction(from={self.sender[:8]}... to={self.receiver[:8]}... amt={self.amount})"

class TransactionNode:
    """
    Represents a node in the transaction graph, holding a transaction
    and a reference to its parent transaction node's hash within the same triad.
    This allows for a Directed Acyclic Graph (DAG) of transactions within a triad.
    """
    def __init__(self, transaction, parent_hash=None):
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be an instance of Transaction class.")
        self.transaction = transaction
        self.parent_hash = parent_hash # Hash of the parent TransactionNode within the triad

    def to_dict(self):
        """Converts the TransactionNode to a dictionary for serialization."""
        return {
            "transaction_data": self.transaction.to_dict(), # This structure is critical
            "parent_hash": self.parent_hash
        }

    def calculate_hash(self):
        """Calculates a hash for the TransactionNode based on its content and parent."""
        node_string = f"{self.transaction.calculate_hash()}{self.parent_hash or ''}"
        return hashlib.sha256(node_string.encode()).hexdigest()

    def __repr__(self):
        return f"TxNode(tx_hash={self.transaction.calculate_hash()[:8]}..., parent_hash={self.parent_hash[:8] if self.parent_hash else 'None'})"


