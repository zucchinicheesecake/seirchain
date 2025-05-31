import unittest
from seirchain.core.simulate import validate_config
from seirchain.config import config

class TestSimulateConfigValidation(unittest.TestCase):
    def test_valid_config(self):
        # Should not raise exception for valid config
        try:
            validate_config()
        except Exception as e:
            self.fail(f"validate_config() raised Exception unexpectedly: {e}")

    def test_invalid_simulation_duration(self):
        original = config.SIMULATION_DURATION_MINUTES
        config.SIMULATION_DURATION_MINUTES = -1
        with self.assertRaises(ValueError):
            validate_config()
        config.SIMULATION_DURATION_MINUTES = original

    def test_invalid_transactions_per_iteration(self):
        original = config.TRANSACTIONS_PER_ITERATION
        config.TRANSACTIONS_PER_ITERATION = -5
        with self.assertRaises(ValueError):
            validate_config()
        config.TRANSACTIONS_PER_ITERATION = original

    def test_invalid_simulation_loop_interval(self):
        original = config.SIMULATION_LOOP_INTERVAL
        config.SIMULATION_LOOP_INTERVAL = 0
        with self.assertRaises(ValueError):
            validate_config()
        config.SIMULATION_LOOP_INTERVAL = original

    def test_invalid_num_simulated_wallets(self):
        original = config.NUM_SIMULATED_WALLETS
        config.NUM_SIMULATED_WALLETS = 0
        with self.assertRaises(ValueError):
            validate_config()
        config.NUM_SIMULATED_WALLETS = original

    def test_invalid_max_depth(self):
        original = config.MAX_DEPTH
        config.MAX_DEPTH = 0
        with self.assertRaises(ValueError):
            validate_config()
        config.MAX_DEPTH = original

if __name__ == "__main__":
    unittest.main()
