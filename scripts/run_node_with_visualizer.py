#!/usr/bin/env python3
import argparse
import time
import logging
from seirchain import TriangularLedger, Miner, Node, global_wallets, render_ascii
from seirchain.core.data_types import Transaction, Triad, Triangle
from seirchain.config import config

logger = logging.getLogger(__name__)

def run_node(port: int, miner_threads: int, network: str = 'mainnet') -> None:
    # Initialize ledger
    ledger = TriangularLedger(config.MAX_DEPTH)
    
    # Load ledger from file or create genesis triad
    try:
        ledger = TriangularLedger.load_from_json(f"data/ledger_{network}.json")
        logger.info(f"Ledger loaded from data/ledger_{network}.json")
    except (FileNotFoundError, ValueError) as e:
        logger.warning(f"Ledger load failed: {e}. Creating new genesis triad.")
        genesis_triad = Triad(
            triad_id="0"*64,
            depth=0,
            hash_value="0"*64,
            parent_hashes=[]
        )
        ledger.add_triad(genesis_triad)
    
    # Initialize wallet manager (simplified)
    class WalletManager:
        def update_balances(self, tx: Transaction) -> None:
            pass
            
    wallet_manager = WalletManager()
    
    # Initialize node
    node = Node(host='0.0.0.0', port=port, ledger=ledger, wallet_manager=wallet_manager)
    
    # Start miner
    miner_address = "miner-address"
    miner = Miner(ledger, node, wallet_manager, miner_address, num_threads=miner_threads)
    
    # Start services
    logger.info("Starting Seirchain Node with Visualizer...")
    node.start()
    miner.start()
    
    # Visualization loop
    try:
        logger.info("Initialization complete. Starting services...")
        logger.info("Starting visualization thread...")
        while True:
            print("\n==== TRIAD MATRIX ====")
            print(f"Depth: {ledger.genesis_triad.depth if ledger.genesis_triad else 0}")
            print(f"Triads: {len(ledger._triad_map)}")
            print(f"Pending Transactions: {len(ledger.transaction_pool)}")
            print("Fractal Representation:")
            print(render_ascii(ledger))
            print("================")
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Stopping node...")
        miner.stop()
        node.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a SEIRchain node')
    parser.add_argument('--network', type=str, default='mainnet', help='Network to join')
    parser.add_argument('--port', type=int, default=5050, help='Port to listen on')
    parser.add_argument('--miner-threads', type=int, default=1, help='Number of mining threads')
    args = parser.parse_args()
    
    run_node(args.port, args.miner_threads, args.network)
