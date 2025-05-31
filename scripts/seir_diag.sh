#!/bin/bash
echo "SeirChain Diagnostics Report"
echo "============================"
date
echo

echo "Virtual Environment:"
echo "-------------------"
if [ -f "venv/bin/activate" ]; then
    echo "Virtual environment exists"
    source venv/bin/activate
    pip list 2>/dev/null | grep -E 'ecdsa|cryptography|base58'
else
    echo "Virtual environment NOT FOUND"
fi

echo -e "\nPython Path:"
echo "-----------"
python -c "import sys; print('\n'.join(sys.path))"

echo -e "\nModule Check:"
echo "------------"
python -c "
try:
    from seirchain.triangular_ledger import TriangularLedger
    print('TriangularLedger import: SUCCESS')
except ImportError as e:
    print(f'TriangularLedger import: FAILED ({str(e)}')
    
try:
    from seirchain.types.transaction import Transaction
    print('Transaction import: SUCCESS')
except ImportError as e:
    print(f'Transaction import: FAILED ({str(e)}')
    
try:
    from seirchain.enhanced_miner.cpu_miner import CpuMiner
    print('CpuMiner import: SUCCESS')
except ImportError as e:
    print(f'CpuMiner import: FAILED ({str(e)}')
"

echo -e "\nFile Structure:"
echo "--------------"
find seirchain -type f | sort
