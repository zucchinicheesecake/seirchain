import sys
import json
import os # Import os for path checking
import argparse # Import argparse for command-line arguments

from seirchain.triangular_ledger.ledger import TriangularLedger
from seirchain.visualizer.ascii import render_ascii
from seirchain.config import load_config # Import load_config

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualize SeirChain Fractal Ledger.")
    parser.add_argument('network', type=str, choices=['testnet', 'mainnet'], default='testnet',
                                help='Specify the network whose ledger to visualize (testnet or mainnet).')
    args = parser.parse_args()

    # Load the specific network config to get the ledger file name
    try:
        config = load_config(args.network)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print(f"Please ensure {args.network}_config.ini exists in seirchain/conf/")
        sys.exit(1)

    ledger_file = config['network']['ledger_file']
    max_depth = int(config['ledger']['max_depth'])
    ledger_version = config['ledger']['ledger_version']

    # Check if ledger file exists before attempting to load
    if not os.path.exists(ledger_file):
        print(f"Error: Ledger file '{ledger_file}' not found for {args.network} network.")
        print(f"Please run 'python seirchain/tools/generate_genesis.py {args.network}' or './run_simulation.sh {args.network}' first.")
        sys.exit(1)

    # Initialize a TriangularLedger object with config parameters
    ledger = TriangularLedger(max_depth=max_depth, ledger_version=ledger_version)

    # Attempt to load the ledger from the specified file
    if not ledger.load_from_file(ledger_file):
        print(f"Error: Could not load ledger from {ledger_file}.")
        sys.exit(1)

    ascii_art_lines = render_ascii(ledger.root, ledger)

    for line in ascii_art_lines:
        print(line)

