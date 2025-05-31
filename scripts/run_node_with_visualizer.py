#!/usr/bin/env python3
import argparse
import time
from seirchain import TriangularLedger, Miner, Node, global_wallets, render_ascii
from seirchain.data_types import Transaction, Triad, Triangle

def run_node(port, miner_threads):
    # Initialize ledger
    ledger = TriangularLedger()
    ledger.create_genesis_triad()
    
    # Initialize wallet manager (simplified)
    class WalletManager:
        def update_balances(self, tx):
            pass
            
    wallet_manager = WalletManager()
    
    # Initialize node
    node = Node(host='0.0.0.0', port=port, ledger=ledger, wallet_manager=wallet_manager)
    
    # Start miner
    miner_address = "miner-address"
    miner = Miner(ledger, node, wallet_manager, miner_address, num_threads=miner_threads)
    
    # Start services
    print("Starting Seirchain Node with Visualizer...")
    node.start()
    miner.start()
    
    # Visualization loop
    try:
        print("Initialization complete. Starting services...")
        print("Starting visualization thread...")
        while True:
            print("\n==== TRIAD MATRIX ====")
            print(f"Depth: {ledger.triads[-1].depth if ledger.triads else 0}")
            print(f"Triads: {len(ledger.triads)}")
            print(f"Pending Transactions: {len(ledger.transaction_pool)}")
            print("Fractal Representation:")
            print(render_ascii(ledger))
            print("================")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nStopping node...")
        miner.stop()
        node.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a SEIRchain node')
    parser.add_argument('--network', type=str, default='mainnet', help='Network to join')
    parser.add_argument('--port', type=int, default=5050, help='Port to listen on')
    parser.add_argument('--miner-threads', type=int, default=1, help='Number of mining threads')
    args = parser.parse_args()
    
    run_node(args.port, args.miner_threads)
