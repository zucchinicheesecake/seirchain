import hashlib
import json
import time
from typing import Optional

class Transaction:
    """Represents a transaction in the SeirChain."""
    def __init__(self, sender: str, receiver: str, amount: float, fee: float, signature: Optional[str] = None, timestamp: Optional[float] = None):
        self.sender = sender # Renamed from_addr to sender for clarity, consistent with wallets
        self.receiver = receiver # Renamed to_addr to receiver
        self.amount = amount
        self.fee = fee
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = signature # Placeholder for cryptographic signature
        self.tx_hash = self.hash_transaction() # Pre-calculate transaction hash

    def to_dict(self, include_signature: bool = True):
        """Converts the transaction to a dictionary for hashing/serialization."""
        tx_dict = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "fee": self.fee,
            "timestamp": self.timestamp
        }
        if include_signature and self.signature is not None:
            tx_dict["signature"] = self.signature
        return tx_dict

    def hash_transaction(self) -> str:
        """Hashes the transaction data (excluding signature for signing)."""
        # We hash the dict representation that does not include the signature
        tx_string = json.dumps(self.to_dict(include_signature=False), sort_keys=True)
        return hashlib.sha256(tx_string.encode('utf-8')).hexdigest()

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a Transaction object from a dictionary."""
        return cls(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount'],
            fee=data['fee'],
            signature=data.get('signature'), # Signature is optional during reconstruction
            timestamp=data.get('timestamp') # Ensure timestamp is also loaded
        )

class TransactionNode:
    """
    Represents a node in the transaction DAG within a Triad.
    Wraps a Transaction object and includes a parent_hash for its position in the DAG.
    """
    def __init__(self, transaction: Transaction, parent_hash: Optional[str] = None):
        self.transaction = transaction
        self.parent_hash = parent_hash # Hash of the parent TransactionNode within the Triad or None if root of DAG

    def to_dict(self):
        """Converts the TransactionNode to a dictionary for serialization."""
        return {
            "transaction": self.transaction.to_dict(),
            "parent_hash": self.parent_hash
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a TransactionNode object from a dictionary."""
        return cls(
            transaction=Transaction.from_dict(data['transaction']),
            parent_hash=data.get('parent_hash')
        )


