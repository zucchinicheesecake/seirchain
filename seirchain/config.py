import os

class Config:
    def __init__(self):
        # Base directory for data files (ledger, wallets)
        # Assumes 'data' directory is sibling to 'seirchain' directory
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True) # Ensure data directory exists

        # --- Blockchain Core Settings ---
        self.GENESIS_MINER_ADDRESS_testnet = "testnet_genesis_miner_0x123abc"
        self.DIFFICULTY = 4  # Number of leading zeros required for a valid hash
        self.MINING_REWARD = 50.0  # Reward for mining a triad
        self.MAX_NONCE_ATTEMPTS = 1_000_000  # Max attempts for Proof-of-Work (adjust for desired speed)
        self.MAX_TRANSACTIONS_PER_TRIAD = 100 # Max transactions a triad can hold
        # Maximum depth of the ledger. Beyond this, older triads might be pruned
        # or require more complex consensus mechanisms.
        self.MAX_DEPTH = 1000
        # Transaction Fee
        self.TRANSACTION_FEE = 0.001
        # Max children a triad can have (should be consistent with Triad.MAX_CHILD_CAPACITY)
        self.MAX_CHILD_CAPACITY = 3

        # --- P2P Network Settings (placeholder for future implementation) ---
        self.P2P_PORT = 8000 # Default port for the P2P node
        self.BOOTSTRAP_NODES = ["127.0.0.1:8001"] # Example: connect to a node on port 8001 initially
        self.PEER_DISCOVERY_INTERVAL = 5 # How often to try connecting to bootstrap nodes (seconds)

        # --- Simulation/Visualizer Settings ---
        self.VISUALIZER_ANIMATION_INTERVAL = 0.08 # How often the visualizer updates (seconds)
        self.DUMMY_TRANSACTION_CHANCE = 0.3 # Probability of adding a dummy transaction per mining loop iteration
        self.SIMULATION_DURATION_MINUTES = 5 # Added this line: Duration of the simulation
        self.TRANSACTIONS_PER_ITERATION = 5 # Added for simulate.py to use
        self.SIMULATION_LOOP_INTERVAL = 0.1 # Added for simulate.py to use
        self.SAVE_LEDGER_PERIODICALLY = True # Added for simulate.py to use
        self.SAVE_INTERVAL_SECONDS = 30 # Added for simulate.py to use
        self.NUM_SIMULATED_WALLETS = 10 # Added for simulate.py to use
        self.INITIAL_DISTRIBUTION_AMOUNT = 1000 # Added for simulate.py to use


# Instantiate the Config class so it can be imported by other modules
config = Config()

