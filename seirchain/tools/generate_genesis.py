import json
from seirchain.ledger import TriangularLedger
from seirchain.data_types import Triad

def generate_genesis(network):
    ledger = TriangularLedger()
    ledger.create_genesis_triad()
    
    # Save ledger to file
    ledger_file = f'ledger_{network}.json'
    with open(ledger_file, 'w') as f:
        json.dump([t.__dict__ for t in ledger.triads], f)
    print(f"Genesis ledger created: {ledger_file}")

if __name__ == "__main__":
    import sys
    generate_genesis(sys.argv[1] if len(sys.argv) > 1 else 'testnet')
