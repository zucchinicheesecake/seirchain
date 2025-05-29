import math
from .tokenomics import GOLDEN_RATIO, PI_OVER_3

BASE_DIFFICULTY = 100

def calculate_difficulty(depth: int) -> float:
    """
    Calculate mining difficulty: D(n) = D₀ × φⁿ × K(n)
    Where K(n) = sin(π/3) × (1 + n²/100)
    """
    sin_pi_over_3 = math.sin(PI_OVER_3)
    k_factor = sin_pi_over_3 * (1 + (depth ** 2) / 100)
    return BASE_DIFFICULTY * (GOLDEN_RATIO ** depth) * k_factor

def depth_progressive_tax(depth: int) -> float:
    """
    Progressive depth taxation: Tax(n) = max(0, (n-10)² × 42)
    """
    if depth <= 10:
        return 0
    return ((depth - 10) ** 2) * 42
