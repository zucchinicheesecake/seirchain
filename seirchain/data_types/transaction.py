class Transaction:
    def __init__(self, transaction_data, tx_hash, timestamp):
        self.transaction_data = transaction_data
        self.tx_hash = tx_hash
        self.timestamp = timestamp
        
    @property
    def from_addr(self):
        return self.transaction_data['from_addr']
        
    @property
    def to_addr(self):
        return self.transaction_data['to_addr']
        
    @property
    def amount(self):
        return self.transaction_data['amount']
        
    @property
    def fee(self):
        return self.transaction_data['fee']
        
    def __repr__(self):
        return (
            f"Tx[hash={self.tx_hash[:12]}..., "
            f"from={self.from_addr[:12]}..., "
            f"to={self.to_addr[:12]}..., "
            f"amount={self.amount}, "
            f"fee={self.fee}]"
        )


class TransactionNode:
    """Represents a transaction within a Triad fractal structure"""
    def __init__(self, transaction, children=None):
        self.transaction = transaction
        self.children = children or []
        self.position = (0, 0)  # X,Y in fractal space
        
    def add_child(self, node):
        self.children.append(node)
        
    def __repr__(self):
        return f"TxNode[{self.transaction} @ {self.position}]"
