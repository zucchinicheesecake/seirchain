#!/bin/bash

# Define the path to the Python executable in the virtual environment
PYTHON_ENV="/home/amy/new/seirchain/venv/bin/python"

# Define the module path for the main simulation script
# IMPORTANT: Use the module path 'seirchain.simulate' with -m
SIMULATION_MODULE="seirchain.simulate"

# Check if the virtual environment python exists
if [ ! -f "$PYTHON_ENV" ]; then
    echo "Error: Python virtual environment not found at $PYTHON_ENV"
    echo "Please activate your venv or create it."
    exit 1
fi

# Check if the simulation module's underlying file exists
if [ ! -f "seirchain/simulate.py" ]; then
    echo "Error: Simulation script file 'seirchain/simulate.py' not found."
    echo "Please ensure you are running this script from the seirchain/ directory."
    exit 1
fi

# Determine the network argument
NETWORK="testnet" # Default network
if [ -n "$1" ]; then # Check if a command-line argument is provided
    NETWORK="$1"
fi

# Run the simulation using -m to treat it as a module within the package
"$PYTHON_ENV" -m "$SIMULATION_MODULE" "$NETWORK" "${@:2}"

if [ $? -eq 0 ]; then
    echo "Simulation completed successfully for $NETWORK network."
else
    echo "Simulation failed for $NETWORK network. Exiting."
fi

