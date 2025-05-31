#!/bin/bash

# SeirChain Quick Start Setup Script

# This script automates the installation and setup of the SeirChain project.
# It assumes you have Python 3 and Git installed.

set -e # Exit immediately if a command exits with a non-zero status.

# 1. Clone the repository (you might want to customize the URL)
echo "Cloning the SeirChain repository..."
# git clone https://github.com/your-username/seirchain.git # Replace with actual repo URL if different
# cd seirchain

# 2. Create and activate the virtual environment
echo "Setting up the Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
echo "Installing project dependencies..."
pip install -r requirements.txt

# 4. Basic check (optional)
echo "Verifying the setup..."
python3 -c "import tqdm; print('SeirChain setup looks good!')"

echo "SeirChain setup complete! You can now run the simulations."
echo "See RUNNING_SIMULATIONS.md for instructions."


