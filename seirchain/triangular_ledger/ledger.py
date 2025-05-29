import json
import time
import hashlib
from typing import Optional, List, Tuple
from collections import deque

from seirchain.data_types.transaction import Transaction # <--- CHANGED HERE

class TransactionNode:
    """Represents a transaction within a Triangle."""
    def __init__(self, transaction_data: dict, tx_hash: str):
        self.transaction_data = transaction_data
        self.tx_hash = tx_hash # SHA3-256 hash of the transaction data
        self.timestamp = time.time() # Timestamp when the transaction was added to the node

    def to_dict(self):
        return {
            "transaction_data": self.transaction_data,
            "tx_hash": self.tx_hash,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(transaction_data=data['transaction_data'], tx_hash=data['tx_hash'])


class Triangle:
    """
    Represents a single triangle (block) in the fractal ledger.
    Can store a transaction or act as a parent for child triangles.
    """
    def __init__(self, triangle_id: str, parent_id: Optional[str] = None, depth: int = 0):
        self.triangle_id = triangle_id
        self.parent_id = parent_id
        self.depth = depth
        self.transactions: List[TransactionNode] = []
        self.children: List[Triangle] = []
        self.mined_by: Optional[str] = None
        self.timestamp: Optional[float] = None
        self.nonce: Optional[int] = None

    def add_transaction(self, tx_node: TransactionNode):
        """Adds a transaction node to this triangle."""
        self.transactions.append(tx_node)

    def add_child(self, child_triangle):
        """Adds a child triangle."""
        self.children.append(child_triangle)

    def to_dict(self):
        """Converts the Triangle object to a dictionary for serialization."""
        return {
            "triangle_id": self.triangle_id,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "children": [child.to_dict() for child in self.children],
            "mined_by": self.mined_by,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a Triangle object from a dictionary."""
        triangle = cls(
            triangle_id=data['triangle_id'],
            parent_id=data['parent_id'],
            depth=data['depth']
        )
        triangle.transactions = [TransactionNode.from_dict(tx_data) for tx_data in data.get('transactions', [])]
        triangle.children = [cls.from_dict(child_data) for child_data in data.get('children', [])]
        triangle.mined_by = data.get('mined_by')
        triangle.timestamp = data.get('timestamp')
        triangle.nonce = data.get('nonce')
        return triangle

    def get_header_hash(self, nonce: int) -> str:
        """
        Generates a hash for the triangle's header,
        including parent_id, depth, and nonce for mining.
        """
        header_string = f"{self.parent_id or ''}{self.depth}{nonce}"
        if self.transactions:
            transactions_string = "".join(tx.tx_hash for tx in self.transactions)
            header_string += hashlib.sha256(transactions_string.encode('utf-8')).hexdigest()
        
        return hashlib.sha256(header_string.encode('utf-8')).hexdigest()


class TriangularLedger:
    """
    Manages the fractal (Sierpinski) ledger structure.
    """
    def __init__(self, max_depth: int = 6, ledger_version: str = "seir-2.1"):
        self.root: Optional[Triangle] = None
        self.max_depth = max_depth
        self.ledger_version = ledger_version
        self._initialize_root()

    def _initialize_root(self):
        """Initializes the genesis (root) triangle of the ledger."""
        if self.root is None:
            genesis_id = hashlib.sha256(f"seirchain-genesis-{time.time()}".encode('utf-8')).hexdigest()
            self.root = Triangle(triangle_id=genesis_id, parent_id=None, depth=0)

    def add_triangle(self, parent_triangle: Triangle, new_triangle: Triangle):
        """Adds a new triangle as a child to an existing parent triangle."""
        if new_triangle.depth <= self.max_depth:
            parent_triangle.add_child(new_triangle)
            return True
        return False

    def find_triangle(self, target_depth: int) -> Tuple[Optional[Triangle], Optional[List[Triangle]]]:
        """
        Finds a suitable triangle at a specific depth to add a transaction or
        new child triangle. Prioritizes triangles that are not yet full (have less than 3 children).
        Returns the chosen triangle and the path to it.
        """
        if not self.root:
            return None, None

        q = deque([(self.root, [self.root])])

        eligible_triangles_at_depth = []

        while q:
            current_triangle, current_path = q.popleft()

            if current_triangle.depth == target_depth:
                if len(current_triangle.children) < 3:
                    eligible_triangles_at_depth.append((current_triangle, current_path))
                else:
                    eligible_triangles_at_depth.append((current_triangle, current_path))
            
            for child in current_triangle.children:
                if child.depth <= target_depth:
                    q.append((child, current_path + [child]))
        
        if not eligible_triangles_at_depth:
            q_fallback = deque([(self.root, [self.root])])
            fallback_options = []
            while q_fallback:
                current_triangle, current_path = q_fallback.popleft()
                if len(current_triangle.children) < 3 and current_triangle.depth < self.max_depth:
                    fallback_options.append((current_triangle, current_path))
                for child in current_triangle.children:
                    q_fallback.append((child, current_path + [child]))
            
            if fallback_options:
                fallback_options.sort(key=lambda x: x[0].depth)
                return fallback_options[0]
            
            return None, None

        eligible_triangles_at_depth.sort(key=lambda x: (len(x[0].children), x[0].timestamp if x[0].timestamp is not None else float('inf')))

        return eligible_triangles_at_depth[0]


    def _count_triangles(self, start_node: Triangle) -> int:
        """Recursively counts all triangles from a given start node."""
        count = 1
        for child in start_node.children:
            count += self._count_triangles(child)
        return count

    def to_dict(self):
        """Converts the entire ledger to a dictionary for serialization."""
        return {
            "root": self.root.to_dict() if self.root else None,
            "max_depth": self.max_depth,
            "ledger_version": self.ledger_version
        }

    def save_to_file(self, filename: str = "ledger.json"):
        """Saves the entire ledger to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def load_from_file(self, filename: str = "ledger.json") -> bool:
        """Loads the entire ledger from a JSON file."""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.root = Triangle.from_dict(data['root'])
                self.max_depth = data.get('max_depth', self.max_depth)
                self.ledger_version = data.get('ledger_version', self.ledger_version)
            return True
        except FileNotFoundError:
            return False
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {filename}. File might be corrupt.")
            return False
        except KeyError as e:
            print(f"Error loading ledger from {filename}: Missing key {e}. File format might be incompatible.")
            return False

    def get_all_transactions(self) -> List[Transaction]:
        """Collects all transactions from the entire ledger."""
        all_txs = []
        if not self.root:
            return all_txs

        q = deque([self.root])
        while q:
            current_triangle = q.popleft()
            for tx_node in current_triangle.transactions:
                all_txs.append(Transaction.from_dict(tx_node.transaction_data))
            for child in current_triangle.children:
                q.append(child)
        return all_txs

