import os
import json # <--- THIS LINE IS IMPORTANT

class Config:
    def __init__(self):
        self.load_default_config() # Call a method to load defaults

    def load_default_config(self):
        # Base directory for data files (ledger, wallets)
        # Assumes 'data' directory is sibling to 'seirchain' directory
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists

        # --- Blockchain Core Settings ---
        self.GENESIS_MINER_ADDRESS_testnet = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        self.DIFFICULTY = 4  # Number of leading zeros required for a valid hash
        self.MINING_REWARD = 50.0  # Reward for mining a triad
        self.MAX_NONCE_ATTEMPTS = 1_000_000  # Max attempts for Proof-of-Work (adjust for desired speed)
        self.MAX_TRANSACTIONS_PER_TRIAD = 100 # Max transactions a triad can hold
        self.MAX_DEPTH = 1000 # Maximum depth of the ledger.
        self.TRANSACTION_FEE = 0.001
        self.MAX_CHILD_CAPACITY = 3 # Max children a triad can have

        # --- P2P Network Settings (placeholder for future implementation) ---
        self.P2P_PORT = 8000 # Default port for the P2P node
        self.BOOTSTRAP_NODES = ["127.0.0.1:8001"]
        self.PEER_DISCOVERY_INTERVAL = 5

        # --- Simulation/Visualizer Settings ---
        self.VISUALIZER_ANIMATION_INTERVAL = 0.08
        self.DUMMY_TRANSACTION_CHANCE = 0.3
        self.SIMULATION_DURATION_MINUTES = 5
        self.TRANSACTIONS_PER_ITERATION = 5
        self.SIMULATION_LOOP_INTERVAL = 0.1
        self.SAVE_LEDGER_PERIODICALLY = True
        self.SAVE_INTERVAL_SECONDS = 30
        self.NUM_SIMULATED_WALLETS = 10
        self.INITIAL_DISTRIBUTION_AMOUNT = 1000

    def load_from_file(self, config_file_path): # <--- THIS IS THE NEW METHOD
        """Loads configuration from a specified JSON file, overriding defaults."""
        try:
            with open(config_file_path, 'r') as f:
                data = json.load(f)
            print(f"Loading configuration from {config_file_path}")
            # Update attributes of this Config instance with values from the JSON file
            for key, value in data.items():
                # Assuming config keys in JSON are uppercase and match attribute names
                setattr(self, key.upper(), value)
            print("Configuration loaded successfully.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from config file {config_file_path}: {e}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred while loading config from {config_file_path}: {e}")

# Instantiate the Config class so it can be imported by other modules
config = Config()

