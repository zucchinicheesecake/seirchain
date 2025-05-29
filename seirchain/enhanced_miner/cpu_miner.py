import hashlib
import time
from typing import Optional

from seirchain.triangular_ledger.ledger import Triangle, TransactionNode
from seirchain.data_types.transaction import Transaction # <--- CHANGED HERE

class CpuMiner:
    def __init__(self, miner_address: Optional[str] = None):
        self.miner_address = miner_address if miner_address else self._generate_miner_address()
        self.difficulty = 2 # Default difficulty, can be updated from config

    def _generate_miner_address(self) -> str:
        """Generates a simple unique address for the miner."""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()

    def mine(self, target_triangle: Triangle, transaction: Transaction) -> Optional[Triangle]:
        """
        Mines a transaction into the target_triangle by finding a valid nonce.
        Updates the triangle with mining details upon success.
        Returns the updated triangle if successful, None otherwise (e.g., if target_triangle is None).
        """
        if not target_triangle:
            return None

        # Add transaction to the triangle before mining, as its hash is part of the header
        tx_node = TransactionNode(
            transaction_data=transaction.to_dict(),
            tx_hash=transaction.hash_transaction()
        )
        target_triangle.add_transaction(tx_node)

        nonce = 0
        max_nonce = 10000000 # A reasonable upper bound for nonce search for testing

        # The mining target (e.g., hash must start with '0' * difficulty)
        target_prefix = "0" * self.difficulty
        
        found = False
        while nonce < max_nonce:
            header_hash = target_triangle.get_header_hash(nonce)
            if header_hash.startswith(target_prefix):
                target_triangle.nonce = nonce
                target_triangle.mined_by = self.miner_address
                target_triangle.timestamp = time.time()
                target_triangle.triangle_id = header_hash # The new ID is the hash of its content
                found = True
                break
            nonce += 1
        
        if not found:
            # If not mined, remove the transaction to avoid issues later
            if tx_node in target_triangle.transactions:
                target_triangle.transactions.remove(tx_node)
            return None # Indicate failure
        
        return target_triangle

