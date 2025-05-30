import hashlib
import time
from seirchain.data_types.transaction import TransactionNode # Import TransactionNode

class Triad:
    """
    Represents a Triad (analogous to a block) in the SeirChain.
    Each Triad contains transactions, links to parent triads, and a proof-of-work.
    """
    def __init__(self, triad_id, depth, parent_hashes, transactions, nonce, difficulty, miner_address, timestamp=None, current_hash=None, child_hashes=None):
        self.triad_id = triad_id
        self.depth = depth
        self.parent_hashes = parent_hashes if parent_hashes is not None else []
        self.transactions = transactions if transactions is not None else [] # List of TransactionNode objects
        self.nonce = nonce
        self.difficulty = difficulty
        self.miner_address = miner_address
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.hash = current_hash if current_hash is not None else self.calculate_hash()
        self.child_hashes = child_hashes if child_hashes is not None else [] # Stores hashes of child triads

    def calculate_hash(self):
        """
        Calculates the SHA256 hash of the triad's contents.
        The hash includes all core attributes to ensure immutability.
        """
        # Ensure transactions are serialized consistently
        transactions_data = ""
        for tx_node in self.transactions:
            # Assuming TransactionNode.to_dict() and Transaction.to_dict() exist and are ordered
            transactions_data += tx_node.transaction.to_dict_string() + (tx_node.parent_hash or "")

        triad_string = f"{self.triad_id}{self.depth}{self.parent_hashes}{transactions_data}{self.nonce}{self.difficulty}{self.miner_address}{self.timestamp}"
        return hashlib.sha256(triad_string.encode()).hexdigest()

    def add_child(self, child_triad):
        """
        Adds a child triad's hash to this triad's child_hashes list.
        This method is crucial for building the triangular structure.
        """
        if child_triad.hash not in self.child_hashes:
            self.child_hashes.append(child_triad.hash)

    def to_dict(self):
        """
        Converts the Triad object to a dictionary for serialization (e.g., to JSON).
        Includes all necessary attributes.
        """
        return {
            "triad_id": self.triad_id,
            "depth": self.depth,
            "parent_hashes": self.parent_hashes,
            "transactions": [tx_node.to_dict() for tx_node in self.transactions],
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "mined_by": self.miner_address,
            "timestamp": self.timestamp,
            "triangle_id": self.hash, # Using 'triangle_id' for consistency with loading
            "children": [] # Children are reconstructed recursively from their own Triad data
        }

    def __repr__(self):
        return f"Triad(id={self.triad_id[:8]}..., depth={self.depth}, hash={self.hash[:8]}..., parents={len(self.parent_hashes)})"


