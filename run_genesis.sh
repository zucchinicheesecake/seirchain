#!/bin/bash

# Define the path to the Python executable in the virtual environment
PYTHON_ENV="/home/amy/new/seirchain/venv/bin/python"

# Define the module path for the genesis script
# IMPORTANT: Use the module path 'seirchain.tools.generate_genesis' with -m
GENESIS_MODULE="seirchain.tools.generate_genesis"

# Check if the virtual environment python exists
if [ ! -f "$PYTHON_ENV" ]; then
    echo "Error: Python virtual environment not found at $PYTHON_ENV"
    echo "Please activate your venv or create it."
    exit 1
fi

# Check if the genesis module path exists (though -m handles discovery)
# We can do a basic check for the underlying file to ensure it's there
if [ ! -f "seirchain/tools/generate_genesis.py" ]; then
    echo "Error: Genesis script file 'seirchain/tools/generate_genesis.py' not found."
    echo "Please ensure you are running this script from the seirchain/ directory."
    exit 1
fi

# Determine the network argument
NETWORK="testnet" # Default network
if [ -n "$1" ]; then # Check if a command-line argument is provided
    NETWORK="$1"
fi

# Run the genesis generation using -m to treat it as a module within the package
echo "Generating genesis ledger for the $NETWORK network..."
"$PYTHON_ENV" -m "$GENESIS_MODULE" "$NETWORK"

if [ $? -eq 0 ]; then
    echo "Genesis ledger generation completed successfully for $NETWORK network."
else
    echo "Genesis ledger generation failed for $NETWORK network. Exiting."
fi

