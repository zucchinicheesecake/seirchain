import sys
import json
import os
import argparse

from seirchain.config import config as global_config
from seirchain.triangular_ledger.triangular_ledger import TriangularLedger
from seirchain.visualizer.ascii import render_ascii # Assuming this path is correct

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize SeirChain Fractal Ledger.")
    parser.add_argument('network', type=str, choices=['testnet', 'mainnet'], default='testnet',
                                help='Specify the network whose ledger to visualize (testnet or mainnet).')
    args = parser.parse_args()

    # --- Configuration Loading ---
    config_filename = f"config_{args.network}.json"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    network_config_path = os.path.join(current_dir, config_filename)

    try:
        global_config.load_from_file(network_config_path)
        print(f"Loaded configuration from {network_config_path}")
    except FileNotFoundError:
        print(f"Error: Configuration file '{network_config_path}' not found for {args.network} network.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration from {network_config_path}: {e}")
        sys.exit(1)

    # --- Ledger Loading ---
    ledger_file = f"ledger_{args.network}.json"
    
    if not os.path.exists(ledger_file):
        print(f"Error: Ledger file '{ledger_file}' not found for {args.network} network.")
        print(f"Please run './run_simulation.sh {args.network}' or './run_genesis.sh {args.network}' first.")
        sys.exit(1)

    ledger = None 
    try:
        ledger = TriangularLedger.load_from_json(ledger_file)
        if not ledger:
            print(f"Error: Could not load ledger from {ledger_file} (loaded_ledger is None).")
            sys.exit(1)
        print(f"Successfully loaded ledger from {ledger_file}. Total triads: {ledger.get_total_triads()}")
    except Exception as e:
        print(f"Error loading ledger from {ledger_file}: {e}")
        sys.exit(1)

    # --- ASCII Visualization ---
    # FIX: Changed 'ledger.root' to 'ledger.genesis_triad'
    if ledger and ledger.genesis_triad: 
        print("\nGenerating ASCII visualization...")
        # FIX: Changed 'ledger.root' to 'ledger.genesis_triad' when passing to render_ascii
        ascii_art_lines = render_ascii(ledger.genesis_triad, ledger)
        for line in ascii_art_lines:
            print(line)
        print("\nASCII visualization complete.")
    else:
        print("No genesis triad found in the ledger. Cannot visualize.")


