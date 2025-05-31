class Triad:
    """
    Represents a Triad in the triangular ledger.
    Attributes:
        triad_id (str): Unique identifier for the triad.
        depth (int): Depth level in the ledger.
        hash_value (str): Hash of the triad.
        parent_hashes (list): List of parent triad hashes.
        child_hashes (list): List of child triad hashes.
    """
    def __init__(self, triad_id, depth, hash_value, parent_hashes, **kwargs):
        self.triad_id = triad_id
        self.depth = depth
        self.hash_value = hash_value  # Use consistent attribute name 'hash_value'
        self.parent_hashes = parent_hashes
        self.child_hashes = []  # Initialize child_hashes as empty list

        # Handle any additional properties
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_child(self, child_triad):
        if not hasattr(self, 'child_hashes'):
            self.child_hashes = []
        if child_triad.hash_value not in self.child_hashes:
            self.child_hashes.append(child_triad.hash_value)
            
    def __str__(self):
        return (
            f"Triad: {self.triad_id[:8]}..., "
            f"depth={self.depth}, "
            f"hash={self.hash_value[:8]}..., "
            f"parents={len(self.parent_hashes)}"
        )
        
    def __repr__(self):
        return (
            f"<Triad {self.triad_id[:8]} "
            f"d={self.depth} "
            f"h={self.hash_value[:8]} "
            f"p={len(self.parent_hashes)}>"
        )

    def to_dict(self):
        return {
            'triad_id': self.triad_id,
            'depth': self.depth,
            'hash_value': self.hash_value,
            'parent_hashes': self.parent_hashes,
            'child_hashes': self.child_hashes,
            # Add any other relevant attributes if needed
        }


class TriadNode:
    """
    Represents a node in the triangular ledger containing transactions.
    Attributes:
        triad_id (str): Unique identifier for the triad node.
        depth (int): Depth level in the ledger.
        transactions (list): List of transactions associated with this node.
    """
    def __init__(self, triad_id, depth):
        self.triad_id = triad_id
        self.depth = depth
        self.transactions = []
        
    def add_transaction(self, tx_data):
        from .transaction import Transaction
        if not isinstance(tx_data, dict):
            raise ValueError("Transaction data must be a dictionary")
        required_keys = ['transaction_data', 'tx_hash', 'timestamp']
        for key in required_keys:
            if key not in tx_data:
                raise ValueError(f"Missing key '{key}' in transaction data")
        tx = Transaction(
            transaction_data=tx_data['transaction_data'],
            tx_hash=tx_data['tx_hash'],
            timestamp=tx_data['timestamp']
        )
        self.transactions.append(tx)
        
    def fractal_hash(self):
        """Generate fractal hash for this triad node"""
        import hashlib
        hash_input = f"{self.triad_id}-{self.depth}-" + \
                     "-".join(tx.tx_hash for tx in self.transactions)
        return hashlib.sha256(hash_input.encode()).hexdigest()
        
    def __repr__(self):
        return f"<TriadNode {self.triad_id[:8]} d={self.depth} txs={len(self.transactions)}>"
