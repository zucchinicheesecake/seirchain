import math

# Mathematical Constants
GENESIS_SUPPLY = 21_000_000
BETA = 0.30
GOLDEN_RATIO = (1 + math.sqrt(5)) / 2
EULERS_NUMBER = math.e
PI_OVER_3 = math.pi / 3

def calculate_supply(depth: int) -> float:
    """
    Calculate token supply at given depth: S(n) = S₀ × (1 - β)ⁿ
    """
    return GENESIS_SUPPLY * ((1 - BETA) ** depth)

def calculate_mining_units(depth: int) -> int:
    """
    Calculate mineable units at depth: T(n) = 3ⁿ
    """
    return 3 ** depth

def calculate_token_density(depth: int) -> float:
    """
    Calculate tokens per mining unit: ρ(n) = S₀ × (β̄/3)ⁿ
    """
    beta_bar = 1 - BETA
    return GENESIS_SUPPLY * ((beta_bar / 3) ** depth)

def calculate_scarcity_index(depth: int) -> float:
    """
    Calculate scarcity index: S₀/S(n)
    """
    return GENESIS_SUPPLY / calculate_supply(depth)

def get_commitment_tier(usdt_amount: float) -> dict:
    """
    Determine commitment tier based on USDT amount
    """
    if usdt_amount < 13.01:
        return {"access_depth": 0, "multiplier": 0.0, "tier": "Insufficient"}
    elif 13.01 <= usdt_amount < 100:
        return {"access_depth": 5, "multiplier": 1.00, "tier": "Entry"}
    elif 100 <= usdt_amount < 1000:
        return {"access_depth": 10, "multiplier": 1.15, "tier": "Moderate"}
    elif 1000 <= usdt_amount < 10000:
        return {"access_depth": 15, "multiplier": 1.35, "tier": "Significant"}
    else:
        return {"access_depth": 20, "multiplier": 1.60, "tier": "Institutional"}
