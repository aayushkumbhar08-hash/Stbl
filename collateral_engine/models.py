"""
Collateral & Margin Engine - Models and Data Definitions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Asset:
    """Represents a single collateral asset class in the institution's portfolio."""
    name: str
    amount_owned: float          # Total inventory owned in USD
    yield_drag: float            # Annualized opportunity cost / yield forgone (e.g. 0.02 for 2.0%)
    haircut_percentage: float    # Clearinghouse regulatory discount (e.g. 0.15 for 15%)
    max_concentration: float     # Maximum allowable allocation in USD

    @property
    def effective_multiplier(self) -> float:
        """Percentage of asset value recognized as margin post-haircut."""
        return max(0.0, 1.0 - self.haircut_percentage)

    @property
    def effective_cost_per_margin_dollar(self) -> float:
        """
        Calculates the shadow cost / opportunity cost per dollar of effective margin generated:
        effective_cost = yield_drag / (1 - haircut_percentage)
        """
        mult = self.effective_multiplier
        if mult <= 0:
            return float("inf")
        return self.yield_drag / mult


@dataclass
class OptimizationResult:
    """Captures the output of the Mixed-Integer Linear Programming optimization."""
    status: str                         # 'Optimal', 'Infeasible', 'Unbounded'
    allocations: Dict[str, float]       # Nominal USD allocated per asset
    post_haircut_values: Dict[str, float]# Effective USD margin contribution per asset
    total_nominal_allocated: float      # Sum of pre-haircut allocations
    total_effective_margin: float       # Sum of post-haircut allocations
    margin_requirement: float           # Target margin requirement in USD
    total_yield_drag_usd: float         # Dollar annual cost: sum(alloc_i * yield_drag_i)
    total_yield_drag_bps: float         # Basis points of allocated nominal
    margin_surplus: float               # total_effective_margin - margin_requirement
    is_breached: bool                   # True if total_effective_margin < margin_requirement
    binding_constraints: List[str]      # Names of binding constraints (e.g., concentration caps)
    asset_details: Dict[str, Dict]      # Breakdown of parameters per asset


def get_default_asset_universe() -> Dict[str, Asset]:
    """
    Returns initial mock data representing institutional asset inventory.
    Calibrated such that:
    - In Baseline ($10M margin): Equities and US Treasuries are prioritized.
      Cash is partially allocated ($490k).
    - Market Shock: Equity haircut spikes 15% -> 50% and margin rises +20% ($12M),
      triggering an aggressive reallocation shedding Equities and surging into safe Cash & US Treasuries.
    """
    return {
        "Cash": Asset(
            name="Cash",
            amount_owned=6_000_000.0,
            yield_drag=0.023,          # 2.30% opportunity cost
            haircut_percentage=0.00,   # 0% haircut (risk-free liquidity)
            max_concentration=5_000_000.0
        ),
        "US Treasuries": Asset(
            name="US Treasuries",
            amount_owned=10_000_000.0,
            yield_drag=0.021,          # 2.10% opportunity cost
            haircut_percentage=0.02,   # 2% haircut
            max_concentration=6_000_000.0
        ),
        "Corporate Bonds": Asset(
            name="Corporate Bonds",
            amount_owned=6_000_000.0,
            yield_drag=0.045,          # 4.50% opportunity cost
            haircut_percentage=0.12,   # 12% haircut
            max_concentration=4_000_000.0
        ),
        "Equities": Asset(
            name="Equities",
            amount_owned=10_000_000.0,
            yield_drag=0.017,          # 1.70% opportunity cost in calm markets
            haircut_percentage=0.15,   # 15% standard haircut
            max_concentration=6_000_000.0
        ),
    }


DEFAULT_MARGIN_REQUIREMENT = 10_000_000.0
SHOCK_EQUITY_HAIRCUT = 0.50
SHOCK_MARGIN_MULTIPLIER = 1.20
