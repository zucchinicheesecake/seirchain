from typing import Dict
from .core.data_types import Transaction, Triad, Triangle
from .core.miner import Miner
from .core.network import Node
from .core.triangular_ledger.triangular_ledger import TriangularLedger

# Global wallets manager
class GlobalWallets:
    def __init__(self) -> None:
        self.wallets: Dict[str, object] = {}
        
    def add_wallet(self, address: str, wallet: object) -> None:
        self.wallets[address] = wallet
        
global_wallets = GlobalWallets()

# ASCII visualization functions
def render_ascii(ledger: TriangularLedger) -> str:
    """Simple ASCII visualization of the triad structure"""
    if not ledger._triad_map:
        return "No triads yet"
    
    # Simple representation showing the depth structure
    output = []
    for triad in ledger._triad_map.values():
        depth_indent = "  " * triad.depth
        output.append(f"{depth_indent}△ Triad {triad.triad_id[:8]} (depth={triad.depth})")
    
    return "\n".join(output)
