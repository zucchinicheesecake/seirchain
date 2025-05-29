from .tokenomics import EULERS_NUMBER
from .difficulty import depth_progressive_tax

def calculate_transaction_burn(amount: float) -> float:
    """
    Calculate transaction fee burn: 2.718159% of the amount
    """
    return amount * (EULERS_NUMBER / 100)

def calculate_depth_tax_burn(depth: int) -> float:
    """
    Calculate progressive depth tax burn
    """
    return depth_progressive_tax(depth)

def geometric_milestone_burn(current_supply: float, milestone_factor: float) -> float:
    """
    Execute geometric milestone burn
    """
    return current_supply * milestone_factor
