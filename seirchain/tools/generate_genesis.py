import json
import time
from seirchain.core.triangular_ledger.triangular_ledger import TriangularLedger
from seirchain.core.data_types.triad import Triad
from seirchain.config import config

def triad_to_dict(triad):
    return {
        "triad_id": triad.triad_id,
        "triangle_id": triad.triad_id,  # Add triangle_id attribute for genesis triad
        "depth": triad.depth,
        "hash_value": triad.hash_value,
        "parent_hashes": triad.parent_hashes,
        "transactions": [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in triad.transactions] if hasattr(triad, 'transactions') else [],  # Include transactions if any
        "nonce": 0,  # Add nonce attribute for genesis triad
        "difficulty": 0,  # Add difficulty attribute for genesis triad
        "mined_by": "",  # Add mined_by attribute for genesis triad
        "timestamp": int(time.time()),  # Add current timestamp for genesis triad
    }

def generate_genesis(network):
    genesis_triad = Triad(
        triad_id="0"*64,
        depth=0,
        hash_value="0"*64,
        parent_hashes=[]
    )
    # Add a dummy transaction with addresses to genesis triad to satisfy simulation requirements
    genesis_triad.transactions = [{
        "transaction_data": {
            "from_addr": "0x0",
            "to_addr": config.GENESIS_MINER_ADDRESS_testnet,
            "amount": 0,
            "fee": 0,
            "timestamp": int(time.time()),
            "signature": ""
        },
        "tx_hash": "0"*64,
        "timestamp": int(time.time())
    }]

    ledger = TriangularLedger(max_depth=5, genesis_triad=genesis_triad)
    
    # Save ledger to file
    ledger_file = f'ledger_{network}.json'
    ledger_data = {
        "genesis_hash": ledger.genesis_triad.hash_value,
        "all_triads": [triad_to_dict(t) for t in ledger._triad_map.values()]
    }
    with open(ledger_file, 'w') as f:
        json.dump(ledger_data, f, indent=2)
    print(f"Genesis ledger created: {ledger_file}")

if __name__ == "__main__":
    import sys
    generate_genesis(sys.argv[1] if len(sys.argv) > 1 else 'testnet')
