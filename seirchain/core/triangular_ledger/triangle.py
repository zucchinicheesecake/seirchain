class Triangle:
    """
    Represents a Triangle in the triangular ledger fractal structure.
    Attributes:
        triad (Triad): The associated Triad object.
        coordinates (tuple): Coordinates in fractal space.
        transactions (list): List of transactions in this triangle.
        children (list): List of child triangles.
    """
    def __init__(self, triad, coordinates=(0, 0)):
        self.triad = triad
        self.coordinates = coordinates
        self.transactions = []  # Now has transactions attribute
        self.children = []
        
    def add_transaction(self, transaction):
        """Add a transaction to this triangle"""
        if transaction is None:
            raise ValueError("Cannot add None as a transaction")
        self.transactions.append(transaction)

    def get_transactions(self):
        """Return the list of transactions"""
        return self.transactions
        
    def add_child(self, triangle):
        """Add a child triangle in the fractal structure"""
        if triangle is None:
            raise ValueError("Cannot add None as a child triangle")
        self.children.append(triangle)
        
    def fractal_position(self, depth):
        """Calculate position in fractal space"""
        x, y = self.coordinates
        return (x * (2**depth), y * (2**depth))
        
    def __repr__(self):
        return f"<Triangle {self.triad.triad_id[:8]} @ {self.coordinates} with {len(self.transactions)} transactions>"
