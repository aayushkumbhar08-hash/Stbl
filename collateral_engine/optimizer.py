"""
Collateral & Margin Engine - PuLP Optimization Module
Mixed-Integer Linear Programming / Linear Programming formulation for cheapest-to-deliver collateral allocation.
"""

import warnings
from typing import Dict, List, Tuple
import pulp

warnings.filterwarnings("ignore", category=DeprecationWarning)

from collateral_engine.models import Asset


def solve_collateral_allocation(
    assets: Dict[str, Asset],
    margin_requirement: float,
    verbose: bool = False
) -> dict:
    """
    Formulates and solves the collateral optimization LP using PuLP:

    Objective:
        Minimize sum(x_i * yield_drag_i)

    Subject to:
        1. sum(x_i * (1 - haircut_i)) >= margin_requirement (Effective Margin constraint)
        2. 0 <= x_i <= min(amount_owned_i, max_concentration_i) (Bounds & Concentration limits)

    Parameters:
        assets: Dictionary of Asset objects keyed by asset name
        margin_requirement: Required effective post-haircut collateral in USD
        verbose: Whether to print PuLP solver output

    Returns:
        OptimizationResult dataclass instance
    """
    # 1. Initialize LP problem
    prob = pulp.LpProblem("Cheapest_To_Deliver_Collateral", pulp.LpMinimize)

    # 2. Define decision variables: x_i is the nominal USD allocation for asset i
    x_vars: Dict[str, pulp.LpVariable] = {}
    upper_bounds: Dict[str, float] = {}

    for name, asset in assets.items():
        # Upper bound is the minimum of total owned inventory and concentration cap
        cap = min(asset.amount_owned, asset.max_concentration)
        upper_bounds[name] = cap
        x_vars[name] = pulp.LpVariable(
            name=f"alloc_{name.replace(' ', '_')}",
            lowBound=0.0,
            upBound=cap,
            cat=pulp.LpContinuous
        )

    # 3. Objective Function: Minimize total yield drag
    prob += pulp.lpSum([x_vars[name] * asset.yield_drag for name, asset in assets.items()]), "Total_Yield_Drag"

    # 4. Constraint 1: Effective Margin Requirement post-haircut
    margin_constraint = pulp.lpSum([
        x_vars[name] * asset.effective_multiplier
        for name, asset in assets.items()
    ]) >= margin_requirement
    prob += margin_constraint, "Margin_Requirement_Constraint"

    # 5. Solve problem using CBC solver
    solver = pulp.PULP_CBC_CMD(msg=1 if verbose else 0)
    prob.solve(solver)

    status_str = pulp.LpStatus[prob.status]

    # 6. Extract solution or handle infeasibility
    allocations: Dict[str, float] = {}
    post_haircut_values: Dict[str, float] = {}
    binding_constraints: List[str] = []

    if prob.status == pulp.constants.LpStatusOptimal:
        for name, asset in assets.items():
            val = float(pulp.value(x_vars[name]) or 0.0)
            # Clip small numerical floating noise
            if abs(val) < 1e-6:
                val = 0.0
            allocations[name] = round(val, 2)
            post_haircut_values[name] = round(val * asset.effective_multiplier, 2)

            # Check binding asset constraints
            if abs(val - upper_bounds[name]) < 1.0 and upper_bounds[name] > 0:
                if upper_bounds[name] == asset.max_concentration:
                    binding_constraints.append(f"{name} at Max Concentration Cap (${asset.max_concentration:,.0f})")
                else:
                    binding_constraints.append(f"{name} at Inventory Cap (${asset.amount_owned:,.0f})")

        total_nominal = sum(allocations.values())
        total_effective = sum(post_haircut_values.values())
        total_yield_cost = sum(allocations[name] * assets[name].yield_drag for name in assets)
        total_bps = (total_yield_cost / total_nominal * 10000) if total_nominal > 0 else 0.0
        surplus = total_effective - margin_requirement

        if abs(surplus) < 1.0:
            binding_constraints.append("Margin Requirement Strictly Binding")

        return dict(
            status="Optimal",
            allocations=allocations,
            post_haircut_values=post_haircut_values,
            total_nominal_allocated=round(total_nominal, 2),
            total_effective_margin=round(total_effective, 2),
            margin_requirement=round(margin_requirement, 2),
            total_yield_drag_usd=round(total_yield_cost, 2),
            total_yield_drag_bps=round(total_bps, 1),
            margin_surplus=round(surplus, 2),
            is_breached=False,
            binding_constraints=binding_constraints,
            asset_details={
                name: {
                    "amount_owned": asset.amount_owned,
                    "yield_drag": asset.yield_drag,
                    "haircut_percentage": asset.haircut_percentage,
                    "max_concentration": asset.max_concentration,
                    "effective_multiplier": asset.effective_multiplier,
                    "effective_cost": asset.effective_cost_per_margin_dollar
                }
                for name, asset in assets.items()
            }
        )

    # Infeasible or error fallback: allocate maximum possible capacity and report breach
    for name, asset in assets.items():
        cap = upper_bounds[name]
        allocations[name] = cap
        post_haircut_values[name] = round(cap * asset.effective_multiplier, 2)

    total_nominal = sum(allocations.values())
    total_effective = sum(post_haircut_values.values())
    total_yield_cost = sum(allocations[name] * assets[name].yield_drag for name in assets)
    total_bps = (total_yield_cost / total_nominal * 10000) if total_nominal > 0 else 0.0
    surplus = total_effective - margin_requirement

    return dict(
        status="Infeasible" if prob.status == pulp.constants.LpStatusInfeasible else status_str,
        allocations=allocations,
        post_haircut_values=post_haircut_values,
        total_nominal_allocated=round(total_nominal, 2),
        total_effective_margin=round(total_effective, 2),
        margin_requirement=round(margin_requirement, 2),
        total_yield_drag_usd=round(total_yield_cost, 2),
        total_yield_drag_bps=round(total_bps, 1),
        margin_surplus=round(surplus, 2),
        is_breached=True,
        binding_constraints=["All Asset Concentration Caps Exhausted", "Insufficient Eligible Collateral"],
        asset_details={
            name: {
                "amount_owned": asset.amount_owned,
                "yield_drag": asset.yield_drag,
                "haircut_percentage": asset.haircut_percentage,
                "max_concentration": asset.max_concentration,
                "effective_multiplier": asset.effective_multiplier,
                "effective_cost": asset.effective_cost_per_margin_dollar
            }
            for name, asset in assets.items()
        }
    )
