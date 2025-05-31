import json
import os
from typing import List
from seirchain.core.data_types import Triad, Transaction

class TriangularLedger:
    def __init__(self) -> None:
        self.triads: List[Triad] = []
        self.transaction_pool: List[Transaction] = []
        
    def add_triad(self, triad: Triad) -> None:
        self.triads.append(triad)
        
    def add_transaction(self, transaction: Transaction) -> None:
        self.transaction_pool.append(transaction)
        
    def load_ledger(self, network: str) -> None:
        """Load ledger from JSON file"""
        filename = f"data/ledger_{network}.json"
        if not os.path.exists(filename):
            self.generate_genesis_triad()
            return
            
        with open(filename, 'r') as f:
            ledger_data = json.load(f)
            
            # Load triads with proper key mapping
            self.triads = []
            for t in ledger_data.get('triads', []):
                # Handle key name differences
                if 'hash' in t and 'hash_value' not in t:
                    t['hash_value'] = t.pop('hash')
                self.triads.append(Triad(**t))
                
            # Load transaction pool
            self.transaction_pool = [
                Transaction(**tx) for tx in ledger_data.get('transaction_pool', [])
            ]
                
    def save_ledger(self, network: str) -> None:
        """Save ledger to JSON file"""
        ledger_data = {
            'triads': [t.__dict__ for t in self.triads],
            'transaction_pool': [tx.__dict__ for tx in self.transaction_pool]
        }
        filename = f"data/ledger_{network}.json"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(ledger_data, f, indent=2)
            
    def generate_genesis_triad(self) -> None:
        """Create the first triad in the matrix"""
        genesis = Triad(
            triad_id="0"*64,
            depth=0,
            hash_value="0"*64,
            parent_hashes=[]
        )
        self.triads = [genesis]
        
    def __repr__(self) -> str:
        return f"TriangularLedger(triads={len(self.triads)}, transactions={len(self.transaction_pool)})"
