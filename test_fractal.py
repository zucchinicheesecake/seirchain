from seirchain.miner import Miner
from seirchain.data_types import Triad, Transaction, Triangle
import time

def test_fractal_mining():
    print("Testing fractal mining...")
    
    # Create mock objects
    mock_triad = Triad('', 1, '', [])
    mock_node = Triangle(mock_triad, (0,0))
    mock_node.add_transaction(Transaction({}, 'tx_hash1', time.time()))
    
    # Test mining
    miner = Miner(None, None, None, 'test')
    hash_val = miner.calculate_fractal_hash(mock_node, 123)
    print(f"Fractal hash: {hash_val}")
    
    # Validate hash
    assert hash_val.startswith("00000") is False  # Without mining
    print("Test passed!")

if __name__ == "__main__":
    test_fractal_mining()
