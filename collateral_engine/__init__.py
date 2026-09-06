"""
Collateral & Margin Engine Package
"""

from collateral_engine.models import (
    Asset,
    OptimizationResult,
    get_default_asset_universe,
    DEFAULT_MARGIN_REQUIREMENT,
    SHOCK_EQUITY_HAIRCUT,
    SHOCK_MARGIN_MULTIPLIER,
)
from collateral_engine.optimizer import solve_collateral_allocation
from collateral_engine.audit_logger import generate_trade_explanation

__all__ = [
    "Asset",
    "OptimizationResult",
    "get_default_asset_universe",
    "DEFAULT_MARGIN_REQUIREMENT",
    "SHOCK_EQUITY_HAIRCUT",
    "SHOCK_MARGIN_MULTIPLIER",
    "solve_collateral_allocation",
    "generate_trade_explanation",
]
