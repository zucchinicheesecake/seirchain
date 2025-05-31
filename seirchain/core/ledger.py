from seirchain.data_types import Triad, Triangle

class TriangularLedger:
    def __init__(self):
        self.triads = []  # Stores Triad objects
        self.transaction_pool = []  # Stores Transaction objects
        self.triangle_nodes = []  # Stores Triangle visualization objects
        self.genesis_created = False
        
    def create_genesis_triad(self):
        """Create the genesis triad"""
        if not self.genesis_created:
            genesis = Triad(
                triad_id="0"*64,
                depth=0,
                hash_value="0"*64,
                parent_hashes=[]
            )
            self.add_triad(genesis)
            self.genesis_created = True
            
    def add_transaction(self, transaction):
        """Add a transaction to the pool"""
        self.transaction_pool.append(transaction)
        
    def add_triad(self, triad):
        """Add a mined triad to the ledger"""
        self.triads.append(triad)
        # Create visualization node
        triad_node = Triangle(triad, coordinates=(0, 0))
        self.triangle_nodes.append(triad_node)
        
    def get_latest_triad(self):
        """Get the latest triad in the chain"""
        if self.triads:
            return self.triads[-1]
        return None
        
    def __repr__(self):
        return f"TriangularLedger(triads={len(self.triads)}, tx_pool={len(self.transaction_pool)})"
def load_ledger(network):
    """Load ledger from file"""
    ledger = TriangularLedger()
    try:
        with open(f'ledger_{network}.json', 'r') as f:
            data = json.load(f)
            for triad_data in data:
                triad = Triad(
                    triad_id=triad_data['triad_id'],
                    depth=triad_data['depth'],
                    hash_value=triad_data['hash_value'],
                    parent_hashes=triad_data['parent_hashes']
                )
                ledger.add_triad(triad)
    except FileNotFoundError:
        print(f"No ledger found for {network}, using empty ledger")
    return ledger
