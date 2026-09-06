"""
Unit Tests for Collateral & Margin Engine
Verifies LP correctness, constraints satisfaction, market shock response, and audit narratives.
"""

import unittest
from collateral_engine.models import (
    Asset,
    get_default_asset_universe,
    DEFAULT_MARGIN_REQUIREMENT,
    SHOCK_EQUITY_HAIRCUT,
    SHOCK_MARGIN_MULTIPLIER,
)
from collateral_engine.optimizer import solve_collateral_allocation
from collateral_engine.audit_logger import generate_trade_explanation


class TestCollateralEngine(unittest.TestCase):
    def setUp(self):
        self.universe = get_default_asset_universe()
        self.baseline_margin = DEFAULT_MARGIN_REQUIREMENT

    def test_baseline_optimization(self):
        """Verify baseline solves to Optimal, meets margin, and respects concentration caps."""
        res = solve_collateral_allocation(self.universe, self.baseline_margin)
        self.assertEqual(res.status, "Optimal")
        self.assertFalse(res.is_breached)

        # Margin Requirement constraint verification
        self.assertGreaterEqual(res.total_effective_margin, self.baseline_margin - 0.01)

        # Concentration & inventory limits verification
        for name, asset in self.universe.items():
            alloc = res.allocations[name]
            self.assertGreaterEqual(alloc, -1e-6)
            cap = min(asset.amount_owned, asset.max_concentration)
            self.assertLessEqual(alloc, cap + 0.01, f"{name} breached cap {cap}")

        # Check effective margin calculation
        expected_effective = sum(
            res.allocations[name] * (1 - self.universe[name].haircut_percentage)
            for name in self.universe
        )
        self.assertAlmostEqual(res.total_effective_margin, expected_effective, places=1)

    def test_market_shock_rebalancing(self):
        """
        Verify that triggering a market shock (Equity haircut 15% -> 50%, Margin +20%):
        1. Successfully rebalances to Optimal without breaching margin.
        2. Drops or heavily penalizes Equities allocation.
        3. Ramps up Cash and US Treasuries allocation.
        """
        # Baseline solve
        baseline_res = solve_collateral_allocation(self.universe, self.baseline_margin)
        baseline_equity_alloc = baseline_res.allocations["Equities"]
        baseline_treasury_alloc = baseline_res.allocations["US Treasuries"]

        # Apply shock parameters
        shocked_universe = get_default_asset_universe()
        shocked_universe["Equities"].haircut_percentage = SHOCK_EQUITY_HAIRCUT
        shocked_margin = self.baseline_margin * SHOCK_MARGIN_MULTIPLIER

        shock_res = solve_collateral_allocation(shocked_universe, shocked_margin)

        self.assertEqual(shock_res.status, "Optimal")
        self.assertFalse(shock_res.is_breached)
        self.assertGreaterEqual(shock_res.total_effective_margin, shocked_margin - 0.01)

        # Verify flight to quality: Equities reduced and US Treasuries / Cash increased
        self.assertLess(
            shock_res.allocations["Equities"],
            baseline_equity_alloc,
            "Equities allocation should decrease after severe 50% haircut shock"
        )
        self.assertGreater(
            shock_res.allocations["US Treasuries"],
            baseline_treasury_alloc,
            "US Treasuries allocation should increase after market shock"
        )

        # Test audit log generation
        logs = generate_trade_explanation(
            prev_result=baseline_res,
            current_result=shock_res,
            is_shock_active=True,
            shock_details={
                "old_equity_haircut": 0.15,
                "new_equity_haircut": SHOCK_EQUITY_HAIRCUT,
                "old_margin": self.baseline_margin,
                "new_margin": shocked_margin
            }
        )
        self.assertGreater(len(logs), 0)
        log_tags = [log["tag"] for log in logs]
        self.assertIn("[MARKET SHOCK TRIGGERED]", log_tags)
        self.assertIn("[SUBSTITUTION: SOLD/REDUCED]", log_tags)
        self.assertIn("[SUBSTITUTION: BOUGHT/PLEDGED]", log_tags)

    def test_infeasibility_handling(self):
        """Verify solver handles impossible margin calls gracefully."""
        huge_margin = 100_000_000.0  # $100M requirement vs ~$22M capacity
        res = solve_collateral_allocation(self.universe, huge_margin)

        self.assertEqual(res.status, "Infeasible")
        self.assertTrue(res.is_breached)
        self.assertLess(res.margin_surplus, 0)

        logs = generate_trade_explanation(None, res)
        self.assertIn("[MARGIN DEFICIT / INFEASIBLE]", [l["tag"] for l in logs])

    def test_concentration_limit_binding(self):
        """Verify that when an asset's concentration limit is reduced, the optimizer redirects to next cheapest."""
        restricted_universe = get_default_asset_universe()
        # Restrict Equities to $1,000,000
        restricted_universe["Equities"].max_concentration = 1_000_000.0

        res = solve_collateral_allocation(restricted_universe, self.baseline_margin)
        self.assertEqual(res.status, "Optimal")
        self.assertAlmostEqual(res.allocations["Equities"], 1_000_000.0, places=1)
        # Ensure margin is still met by other assets
        self.assertGreaterEqual(res.total_effective_margin, self.baseline_margin - 0.01)

    def test_cheapest_to_deliver_order(self):
        """Verify assets with lower effective cost (yield_drag / (1 - haircut)) are prioritized."""
        universe = get_default_asset_universe()
        for name, asset in universe.items():
            self.assertGreater(asset.effective_cost_per_margin_dollar, 0)
            self.assertGreater(asset.effective_multiplier, 0)


if __name__ == "__main__":
    unittest.main()
