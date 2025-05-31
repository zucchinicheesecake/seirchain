from .data_types import Transaction, Triad, Triangle
from .miner import Miner
from .network import Node
from .ledger import TriangularLedger

# Global wallets manager
class GlobalWallets:
    def __init__(self):
        self.wallets = {}
        
    def add_wallet(self, address, wallet):
        self.wallets[address] = wallet
        
global_wallets = GlobalWallets()

# ASCII visualization functions
def render_ascii(ledger):
    """Simple ASCII visualization of the triad structure"""
    if not ledger.triads:
        return "No triads yet"
    
    # Simple representation showing the depth structure
    output = []
    for triad in ledger.triads:
        depth_indent = "  " * triad.depth
        output.append(f"{depth_indent}△ Triad {triad.triad_id[:8]} (depth={triad.depth})")
    
    return "\n".join(output)
