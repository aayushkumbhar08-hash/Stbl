"""
Collateral & Margin Engine - Audit Logger & Trade Explanation Engine
Translates quantitative linear programming shifts into plain-English institutional trading narratives.
"""

from datetime import datetime
from typing import Dict, List, Optional
from collateral_engine.models import Asset


def generate_trade_explanation(
    prev_result: Optional[dict],
    current_result: dict,
    is_shock_active: bool = False,
    shock_details: Optional[Dict] = None
) -> List[Dict[str, str]]:
    """
    Generates structured, plain-English action log entries explaining what was traded and why.

    Returns a list of log entries with:
    - 'timestamp': Formatted string
    - 'tag': Categorical label (e.g. '[MARKET SHOCK]', '[REBALANCE]', '[CONCENTRATION]', '[MARGIN CALL]')
    - 'severity': 'info' | 'warning' | 'danger' | 'success'
    - 'title': Headline summary
    - 'explanation': Deep quantitative explanation of the optimizer's moves
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    logs: List[Dict[str, str]] = []

    # If infeasible / breach
    if current_result.get('is_breached') or current_result.get('status') != "Optimal":
        shortfall = abs(current_result.get('margin_surplus'))
        logs.append({
            "timestamp": timestamp,
            "tag": "[MARGIN DEFICIT / INFEASIBLE]",
            "severity": "danger",
            "title": f"Margin Requirement Deficit: Shortfall of ${shortfall:,.2f}",
            "explanation": (
                f"The optimizer exhausted all available eligible inventory and concentration limits, "
                f"generating only ${current_result.get('total_effective_margin'):,.2f} in post-haircut margin against the "
                f"${current_result.get('margin_requirement'):,.2f} threshold. Action needed: Inject unencumbered liquid assets "
                f"or request bilateral concentration waiver."
            )
        })
        return logs

    # Initial Run (no previous comparison)
    if prev_result is None:
        logs.append({
            "timestamp": timestamp,
            "tag": "[INITIAL SOLVE]",
            "severity": "info",
            "title": f"Baseline Collateral Allocation Formulated: ${current_result.get('total_nominal_allocated'):,.2f} Pledged",
            "explanation": (
                f"Pledged ${current_result.get('total_nominal_allocated'):,.2f} nominal across {len(current_result.get('allocations'))} assets "
                f"delivering exactly ${current_result.get('total_effective_margin'):,.2f} post-haircut margin (Target: ${current_result.get('margin_requirement'):,.2f}). "
                f"Weighted yield drag is {current_result.get('total_yield_drag_bps'):.1f} bps (${current_result.get('total_yield_drag_usd'):,.2f}/yr). "
                f"Assets were selected strictly in ascending order of effective cost per margin dollar."
            )
        })
        return logs

    # Market Shock Specific Narrative
    if is_shock_active and shock_details:
        old_haircut = shock_details.get("old_equity_haircut", 0.15) * 100
        new_haircut = shock_details.get("new_equity_haircut", 0.50) * 100
        old_margin = shock_details.get("old_margin", 10_000_000.0)
        new_margin = shock_details.get("new_margin", 12_000_000.0)
        margin_delta = new_margin - old_margin

        logs.append({
            "timestamp": timestamp,
            "tag": "[MARKET SHOCK TRIGGERED]",
            "severity": "warning",
            "title": f"CCP Volatility Shock Injected: Margin +20%, Equity Haircut {old_haircut:.0f}% -> {new_haircut:.0f}%",
            "explanation": (
                f"Clearinghouse issued an intraday risk update: Baseline margin requirement jumped +${margin_delta:,.0f} "
                f"to ${new_margin:,.0f}. Simultaneously, Equity haircut surged from {old_haircut:.0f}% to {new_haircut:.0f}%, "
                f"instantly devaluing equity collateral by {new_haircut - old_haircut:.0f} percentage points."
            )
        })

    # Delta Analysis: What was traded?
    trades_executed = []
    assets = current_result.get('allocations').keys()

    for asset_name in assets:
        old_alloc = prev_result.get('allocations').get(asset_name, 0.0)
        new_alloc = current_result.get('allocations').get(asset_name, 0.0)
        diff = new_alloc - old_alloc

        if abs(diff) > 1.0:
            trades_executed.append({
                "asset": asset_name,
                "old": old_alloc,
                "new": new_alloc,
                "diff": diff,
                "pct_change": ((diff / old_alloc) * 100) if old_alloc > 0 else 100.0
            })

    if not trades_executed:
        logs.append({
            "timestamp": timestamp,
            "tag": "[NO REBALANCE NEEDED]",
            "severity": "info",
            "title": "Portfolio Unchanged",
            "explanation": "Existing allocations remain mathematically optimal under the current constraints."
        })
        return logs

    # Explain trades
    increases = [t for t in trades_executed if t["diff"] > 0]
    decreases = [t for t in trades_executed if t["diff"] < 0]

    # Detailed trade commentary
    for t in decreases:
        details = current_result.get('asset_details')[t["asset"]]
        haircut_pct = details["haircut_percentage"] * 100
        eff_cost = details["effective_cost"] * 100
        logs.append({
            "timestamp": timestamp,
            "tag": "[SUBSTITUTION: SOLD/REDUCED]",
            "severity": "danger",
            "title": f"Liquidated/De-pledged ${abs(t['diff']):,.2f} of {t['asset']} ({t['pct_change']:.1f}%)",
            "explanation": (
                f"Optimizer reduced {t['asset']} from ${t['old']:,.2f} to ${t['new']:,.2f}. "
                f"Reason: With a haircut of {haircut_pct:.1f}%, each dollar of {t['asset']} only yields "
                f"${details['effective_multiplier']:.2f} of recognized margin, driving its effective cost to "
                f"{eff_cost:.2f}% per margin dollar, rendering it uneconomical compared to high-grade liquid collateral."
            )
        })

    for t in increases:
        details = current_result.get('asset_details')[t["asset"]]
        haircut_pct = details["haircut_percentage"] * 100
        eff_cost = details["effective_cost"] * 100
        cap_hit = abs(t["new"] - min(details["amount_owned"], details["max_concentration"])) < 1.0
        cap_note = " (Pledged up to maximum allowable concentration cap)" if cap_hit else ""

        logs.append({
            "timestamp": timestamp,
            "tag": "[SUBSTITUTION: BOUGHT/PLEDGED]",
            "severity": "success",
            "title": f"Allocated +${t['diff']:,.2f} of {t['asset']} (+{t['pct_change']:.1f}%){cap_note}",
            "explanation": (
                f"Optimizer elevated {t['asset']} from ${t['old']:,.2f} to ${t['new']:,.2f}. "
                f"Reason: Low haircut of {haircut_pct:.1f}% gives an effective margin efficiency of "
                f"${details['effective_multiplier']:.2f} per dollar. At an effective opportunity cost of only "
                f"{eff_cost:.2f}%, {t['asset']} is the cheapest-to-deliver asset to absorb the margin requirement."
            )
        })

    # Summary synthesis entry
    net_nominal_change = current_result.get('total_nominal_allocated') - prev_result.get('total_nominal_allocated')
    yield_cost_change = current_result.get('total_yield_drag_usd') - prev_result.get('total_yield_drag_usd')

    logs.append({
        "timestamp": timestamp,
        "tag": "[REBALANCE AUDIT SUMMARY]",
        "severity": "info",
        "title": f"Optimization Complete: Zero Margin Breach Maintained",
        "explanation": (
            f"Active effective collateral: ${current_result.get('total_effective_margin'):,.2f} "
            f"(Surplus buffer: +${current_result.get('margin_surplus'):,.2f}). "
            f"Net nominal portfolio size shifted by {net_nominal_change:+,.2f} USD. "
            f"Annualized opportunity cost changed by {yield_cost_change:+,.2f} USD "
            f"({prev_result.get('total_yield_drag_bps'):.1f} bps -> {current_result.get('total_yield_drag_bps'):.1f} bps). "
            f"All clearinghouse concentration limits strictly enforced."
        )
    })

    return logs
