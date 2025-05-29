# seirchain/__init__.py

# This file makes 'seirchain' a Python package.
# It can also be used to expose commonly used components directly under the 'seirchain' namespace.

# Example: Expose core components for easier import
from .triangular_ledger.ledger import TriangularLedger, Triangle, TransactionNode
from .wallet_manager.keys import Wallet
from .enhanced_miner.cpu_miner import CpuMiner
from .visualizer.ascii import render_ascii
from .data_types.transaction import Transaction # <--- CHANGED HERE: from .types to .data_types

__version__ = "0.2.1" # Example version, increment as needed

# You can add more package-level initialization here if necessary

