import hashlib
from typing import List, Optional

# IMPORT THE ACTUAL Triad and TransactionNode classes
from seirchain.data_types.triad import Triad # <--- IMPORTANT: This is the real Triad
from seirchain.data_types.transaction import TransactionNode # Needed for transaction type hints

# --- REMOVE THE REDUNDANT 'Triangle' CLASS STUB HERE ---
# It was causing the type mismatch and is no longer needed.

# Global list to store the ASCII lines
_tree_lines: List[str] = []

# Update node type hint to Triad and add ledger_instance for child lookups
def build_tree_string(node: Triad, prefix: str = '', is_last: bool = True, ledger_instance=None):
    """
    Recursively builds the ASCII tree string from a Triad node.
    Requires ledger_instance to look up child Triad objects from their hashes.
    """
    global _tree_lines
    if not node:
        return

    branch = '└── ' if is_last else '├── '
    # FIX: Use node.hash as the unique identifier for display
    node_str = f"{prefix}{branch}△ Depth {node.depth}, Hash {node.hash[:8]}..."
    _tree_lines.append(node_str)

    # Add transaction info if any
    for i, tx_node in enumerate(node.transactions):
        tx_prefix = prefix + ('    ' if is_last else '│   ')
        # Use node.child_hashes for checking if current transaction is the last element
        tx_branch = '└── ' if i == len(node.transactions) - 1 and not node.child_hashes else '├── '
        # FIX: Access the hash from the actual Transaction object within TransactionNode
        _tree_lines.append(f"{tx_prefix}{tx_branch}Tx: {tx_node.transaction.calculate_hash()[:8]}...")

    # Recursively call for children
    # FIX: Iterate over node.child_hashes and retrieve the actual Triad objects
    for i, child_hash in enumerate(node.child_hashes):
        # Ensure ledger_instance is provided and the child hash exists in its map
        if ledger_instance and child_hash in ledger_instance._triad_map:
            child_node = ledger_instance._triad_map[child_hash] # Get the actual child Triad object
            new_prefix = prefix + ('    ' if is_last else '│   ')
            is_last_child = (i == len(node.child_hashes) - 1)
            # Pass ledger_instance recursively
            build_tree_string(child_node, new_prefix, is_last_child, ledger_instance)
        # else:
            # print(f"Warning: Child hash {child_hash[:8]}... not found in ledger map.")


def render_ascii(root_triangle: Triad, ledger_instance) -> List[str]: # Type hint root_triangle to Triad
    """
    Renders the fractal ledger as an ASCII tree.
    `ledger_instance` is crucial for accessing child triads from their hashes.
    """
    global _tree_lines
    _tree_lines = [] # Clear previous lines before rendering

    if not root_triangle:
        return ["(Empty Ledger)"]
    
    # Pass the ledger_instance down to build_tree_string for child lookup
    build_tree_string(root_triangle, ledger_instance=ledger_instance)

    return _tree_lines

# --- REMOVE OR COMMENT OUT THE '__main__' TEST BLOCK ---
# This test block relied on the old 'Triangle' stub class and will no longer work correctly.
# If you want to test ascii.py in isolation, you'd need to create real Triad and Ledger objects.
# if __name__ == '__main__':
#     print("--- Example ASCII Tree ---")
#     # This part should be updated to use actual Triad and Ledger objects for testing
#     # For now, it's safer to remove or comment out as it relies on the old Triangle stub.
#     print("--------------------------")

