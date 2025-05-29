import hashlib
from typing import List, Optional

# Assuming Triangle and TriangularLedger are accessible,
# or we just rely on their dictionary representations for visualization.
# For simplicity, we'll assume the objects are passed directly for now.
# If these functions were in a separate package, they'd import Triangle etc.
# For now, we'll rely on the structure of the Triangle object.

class Triangle: # Re-define a stub for type hinting, or import if possible
    # This is a stub for type hinting if not imported.
    # In a real setup, you'd import the actual Triangle class.
    # For this visualizer, we just need to know it has depth, triangle_id, and children.
    def __init__(self, triangle_id: str, depth: int, children: Optional[list] = None, transactions: Optional[list] = None):
        self.triangle_id = triangle_id
        self.depth = depth
        self.children = children if children is not None else []
        self.transactions = transactions if transactions is not None else []
    
    # Placeholder for get_header_hash if needed, or other methods
    def get_header_hash(self, nonce: int) -> str:
        return hashlib.sha256(f"{self.triangle_id}{self.depth}{nonce}".encode()).hexdigest()


# Global list to store the ASCII lines
_tree_lines: List[str] = []

def build_tree_string(node: Triangle, prefix: str = '', is_last: bool = True):
    """Recursively builds the ASCII tree string."""
    global _tree_lines

    if not node:
        return

    branch = '└── ' if is_last else '├── '
    
    node_str = f"{prefix}{branch}△ Depth {node.depth}, ID {node.triangle_id[:8]}..."
    _tree_lines.append(node_str)

    # Add transaction info if any
    for i, tx_node in enumerate(node.transactions):
        tx_prefix = prefix + ('    ' if is_last else '│   ')
        tx_branch = '└── ' if i == len(node.transactions) - 1 and not node.children else '├── '
        # Assuming tx_node has a tx_hash or similar identifiable attribute
        _tree_lines.append(f"{tx_prefix}{tx_branch}Tx: {tx_node.tx_hash[:8]}...")

    # Recursively call for children
    for i, child in enumerate(node.children):
        new_prefix = prefix + ('    ' if is_last else '│   ')
        is_last_child = (i == len(node.children) - 1)
        build_tree_string(child, new_prefix, is_last_child)

def render_ascii(root_triangle: Triangle, ledger) -> List[str]:
    """
    Renders the fractal ledger as an ASCII tree.
    `ledger` parameter is included for consistency but not directly used by render_ascii's logic.
    """
    global _tree_lines
    _tree_lines = [] # Clear previous lines before rendering
    
    if not root_triangle:
        return ["(Empty Ledger)"]

    build_tree_string(root_triangle)
    return _tree_lines

if __name__ == '__main__':
    # This is a simple example for testing purposes
    # In a real scenario, you'd load a ledger and pass its root
    
    # Create a dummy ledger structure
    root = Triangle("genesis_root", 0)
    
    child1 = Triangle("child1_id", 1)
    child1_tx1 = type('obj', (object,), {'tx_hash': 'tx1a'})() # Mock TransactionNode
    child1_tx2 = type('obj', (object,), {'tx_hash': 'tx1b'})()
    child1.transactions.append(child1_tx1)
    child1.transactions.append(child1_tx2)


    child2 = Triangle("child2_id", 1)
    child2_tx1 = type('obj', (object,), {'tx_hash': 'tx2a'})()
    child2.transactions.append(child2_tx1)
    

    grandchild1_1 = Triangle("gc1_1_id", 2)
    grandchild1_1_tx1 = type('obj', (object,), {'tx_hash': 'gtx1a'})()
    grandchild1_1.transactions.append(grandchild1_1_tx1)
    
    root.children.append(child1)
    root.children.append(child2)
    child1.children.append(grandchild1_1)

    print("--- Example ASCII Tree ---")
    for line in render_ascii(root, None): # For standalone testing, ledger argument is just a placeholder here
        print(line)
    print("--------------------------")

