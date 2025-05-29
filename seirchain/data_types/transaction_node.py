# seirchain/data_types/transaction_node.py
import hashlib
import json
import time

class TransactionNode:
    """
    Represents a single transaction in the SeirChain network.
    Now with more functional (for simulation) signing and verification.
    """
    def __init__(self, sender_address, receiver_address, amount, fee, timestamp=None, signature=None):
        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount
        self.fee = fee
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = signature # Placeholder for cryptographic signature

        # The hash is calculated when the object is created
        self.hash = self.calculate_hash()

    def _get_hashable_data(self):
        """Returns a dictionary of data used for hashing and signing."""
        return {
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'fee': self.fee,
            'timestamp': self.timestamp
        }

    def calculate_hash(self):
        """Calculates the SHA256 hash of the transaction data."""
        transaction_data = self._get_hashable_data()
        transaction_string = json.dumps(transaction_data, sort_keys=True).encode('utf-8')
        return hashlib.sha256(transaction_string).hexdigest()

    def sign(self, private_key_seed):
        """
        Simulates signing the transaction. In a real system, private_key_seed
        would be a cryptographic private key. Here, it's used to generate
        a deterministic "signature" for simulation purposes.
        """
        # Hash the transaction data + a private key seed to simulate a signature
        data_to_sign = json.dumps(self._get_hashable_data(), sort_keys=True) + str(private_key_seed)
        self.signature = hashlib.sha256(data_to_sign.encode('utf-8')).hexdigest()

    def verify_signature(self, public_key_seed):
        """
        Simulates verifying the transaction signature. In a real system,
        public_key_seed would be a cryptographic public key.
        Here, it verifies against the simulated signature.
        """
        if not self.signature:
            return False # No signature to verify

        # Recalculate what the signature *should* be based on the provided public_key_seed
        # In a real system, this would be a public key operation on the signature and data.
        # For simulation, we'll assume public_key_seed can regenerate the same logic.
        # (Note: In a real system, you'd verify the signature with the public key, not re-sign.)
        expected_signature_base = json.dumps(self._get_hashable_data(), sort_keys=True) + str(public_key_seed)
        expected_signature = hashlib.sha256(expected_signature_base.encode('utf-8')).hexdigest()
        
        return self.signature == expected_signature

    def to_dict(self):
        """Converts the TransactionNode object to a dictionary for serialization."""
        return {
            'sender_address': self.sender_address,
            'receiver_address': self.receiver_address,
            'amount': self.amount,
            'fee': self.fee,
            'timestamp': self.timestamp,
            'hash': self.hash,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a TransactionNode object from a dictionary."""
        instance = cls(
            sender_address=data['sender_address'],
            receiver_address=data['receiver_address'],
            amount=data['amount'],
            fee=data['fee'],
            timestamp=data['timestamp'],
            signature=data.get('signature')
        )
        instance.hash = data.get('hash', instance.calculate_hash())
        return instance

    def __repr__(self):
        return f"TxNode(sender={self.sender_address[:8]}..., receiver={self.receiver_address[:8]}..., amount={self.amount})"


