class Triad:
    def __init__(self, triad_id, depth, hash_value, parent_hashes, **kwargs):
        self.triad_id = triad_id
        self.depth = depth
        self.hash = hash_value  # Using 'hash' as the attribute name
        self.parent_hashes = parent_hashes
        
        # Handle any additional properties
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def __str__(self):
        return (
            f"Triad: {self.triad_id[:8]}..., "
            f"depth={self.depth}, "
            f"hash={self.hash[:8]}..., "
            f"parents={len(self.parent_hashes)}"
        )
        
    def __repr__(self):
        return (
            f"<Triad {self.triad_id[:8]} "
            f"d={self.depth} "
            f"h={self.hash[:8]} "
            f"p={len(self.parent_hashes)}>"
        )


class TriadNode:
    def __init__(self, triad_id, depth):
        self.triad_id = triad_id
        self.depth = depth
        self.transactions = []
        
    def add_transaction(self, tx_data):
        from .transaction import Transaction
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
