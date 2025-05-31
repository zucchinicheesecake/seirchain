#!/usr/bin/env python3
import argparse
from seirchain import render_ascii
from seirchain.ledger import load_ledger

def main():
    parser = argparse.ArgumentParser(description='Visualize SEIRchain ledger')
    parser.add_argument('network', choices=['testnet', 'mainnet'], help='Network to visualize')
    args = parser.parse_args()
    
    ledger = load_ledger(args.network)
    print(render_ascii(ledger))

if __name__ == "__main__":
    main()
