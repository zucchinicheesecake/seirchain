from typing import List, Tuple, Optional
import hashlib
import json

class Triangle:
    def __init__(self, depth: int, coordinates: Tuple[int, int], parent=None):
        self.depth = depth
        self.coordinates = coordinates
        self.transactions = []
        self.children: List['Triangle'] = []
        self.parent = parent
        self.mined_by = None
        self.timestamp = None
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Quantum-resistant hash with depth-based salt"""
        salt = f"△{self.depth:03d}"
        data = {
            "depth": self.depth,
            "coords": self.coordinates,
            "tx_count": len(self.transactions),
            "parent": self.parent.coordinates if self.parent else "genesis"
        }
        return hashlib.sha3_512(
            (salt + json.dumps(data, sort_keys=True)).encode()
        ).hexdigest()

    def add_transaction(self, tx):
        """Add transaction with automatic hash update"""
        self.transactions.append(tx)
        self.hash = self.calculate_hash()

    def subdivide(self):
        """Fractal subdivision with geometric progression"""
        if self.children:
            return self.children
            
        base_x, base_y = self.coordinates
        for i in range(3):
            # Fractal coordinate calculation (Sierpiński pattern)
            child_coords = (
                base_x * 3 + (i % 3),
                base_y * 3 + (i // 3)
            )
            child = Triangle(self.depth + 1, child_coords, parent=self)
            self.children.append(child)
        return self.children

    def get_all_transactions(self):
        """BFS transaction aggregation"""
        transactions = []
        queue = [self]
        while queue:
            node = queue.pop(0)
            transactions.extend(node.transactions)
            queue.extend(node.children)
        return transactions

    def to_dict(self):
        """Serialization for persistence"""
        return {
            "depth": self.depth,
            "coordinates": self.coordinates,
            "transactions": [tx.__dict__ for tx in self.transactions],
            "mined_by": self.mined_by,
            "hash": self.hash,
            "children": [child.to_dict() for child in self.children]
        }
