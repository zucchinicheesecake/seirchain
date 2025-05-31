class Triangle:
    def __init__(self, triad, coordinates=(0, 0)):
        self.triad = triad
        self.coordinates = coordinates
        self.transactions = []  # Now has transactions attribute
        self.children = []
        
    def add_transaction(self, transaction):
        """Add a transaction to this triangle"""
        self.transactions.append(transaction)

    def get_transactions(self):
        """Return the list of transactions"""
        return self.transactions
        
    def add_child(self, triangle):
        """Add a child triangle in the fractal structure"""
        self.children.append(triangle)
        
    def fractal_position(self, depth):
        """Calculate position in fractal space"""
        x, y = self.coordinates
        return (x * (2**depth), y * (2**depth))
        
    def __repr__(self):
        return f"<Triangle {self.triad.triad_id[:8]} @ {self.coordinates} with {len(self.transactions)} transactions>"
