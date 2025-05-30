import time
import hashlib

class TransactionNode:
    def __init__(self, sender_address, recipient_address, amount, fee, timestamp=None, tx_id=None):
        self.sender_address = sender_address
        self.recipient_address = recipient_address
        self.amount = float(amount)
        self.fee = float(fee)
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.tx_id = tx_id if tx_id is not None else self.calculate_hash() # Unique ID for transaction

    def calculate_hash(self):
        """Calculates a unique hash for the transaction."""
        transaction_string = f"{self.sender_address}{self.recipient_address}{self.amount}{self.fee}{self.timestamp}"
        return hashlib.sha256(transaction_string.encode('utf-8')).hexdigest()

    def to_dict(self):
        """Converts the TransactionNode object to a dictionary for serialization."""
        return {
            "sender_address": self.sender_address,
            "recipient_address": self.recipient_address,
            "amount": self.amount,
            "fee": self.fee,
            "timestamp": self.timestamp,
            "tx_id": self.tx_id
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a TransactionNode object from a dictionary."""
        return cls(
            sender_address=data["sender_address"],
            recipient_address=data["recipient_address"],
            amount=data["amount"],
            fee=data["fee"],
            timestamp=data["timestamp"],
            tx_id=data["tx_id"]
        )

