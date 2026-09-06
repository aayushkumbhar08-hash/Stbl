# Collateral & Margin Engine

An institutional-grade **Collateral & Margin Management Engine** that mathematically determines the cheapest-to-deliver (CTD) combination of assets a financial institution can pledge to a central clearinghouse (CCP) without breaching margin requirements or concentration limits.

---

## 📌 Mathematical Formulation

### Parameters & Decision Variables
Let the asset classes be $\mathcal{A} = \{\text{Cash}, \text{US Treasuries}, \text{Corporate Bonds}, \text{Equities}\}$.
For each asset $i \in \mathcal{A}$:
- $O_i$: Amount owned (unencumbered inventory in USD)
- $c_i$: Annual opportunity cost / yield drag (annual rate)
- $h_i$: Regulatory haircut discount applied by the clearinghouse ($0 \le h_i < 1$)
- $C_i$: Maximum allowable concentration limit in USD
- $M$: Target Margin Requirement (Baseline: \$10,000,000)

**Decision Variable:**
- $x_i \ge 0$: Nominal dollar allocation of asset $i$ pledged as collateral.

### Objective Function
Minimize the total opportunity cost (yield drag) of the pledged portfolio:
$$\min \sum_{i \in \mathcal{A}} x_i \cdot c_i$$

### Constraints
1. **Clearinghouse Margin Requirement (Post-Haircut Value):**
   $$\sum_{i \in \mathcal{A}} x_i \cdot (1 - h_i) \ge M$$

2. **Inventory & Concentration Bounds:**
   $$0 \le x_i \le \min(O_i, C_i) \quad \forall i \in \mathcal{A}$$

### Cheapest-to-Deliver (CTD) Shadow Frontier
The LP solver prioritizes assets according to their effective opportunity cost per dollar of recognized margin:
$$\text{Effective Marginal Cost}_i = \frac{c_i}{1 - h_i}$$

---

## ⚡ Market Shock Simulation
Clearinghouses dynamically update margin schedules and haircuts during volatility events. Clicking **"Trigger Market Shock"** executes an intraday shock scenario:
1. **Equity Haircut Spikes from 15% to 50%**:
   - Drops the margin factor from $0.85 \rightarrow 0.50$.
   - Spikes the effective cost of Equities from $2.00\% \rightarrow 3.40\%$.
2. **Margin Requirement Escalates by +20%**:
   - Baseline \$10,000,000 rises to \$12,000,000.
3. **Automated Optimizer Reaction**:
   - The engine automatically re-solves the Mixed-Integer LP.
   - Pledges are aggressively withdrawn from penalized Equities and re-routed into safe Cash and US Treasuries to avoid a clearinghouse margin breach.
4. **Action Log & Audit Trail**:
   - Generates a plain-English institutional explanation of every trade executed, explaining *what* changed and *why*.

---

## 🚀 Quickstart & Execution

### 1. Environment Setup
The project uses Python 3.12 with `uv`:
```powershell
# Virtual environment is located at .venv
.venv\Scripts\activate
```

### 2. Run the Streamlit Dashboard
```powershell
.venv\Scripts\streamlit.exe run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Run Automated Tests
```powershell
.venv\Scripts\python.exe -m unittest discover tests
```

---

## 📁 Project Structure

```
init/
├── app.py                     # Interactive Streamlit dashboard with Plotly charts
├── collateral_engine/
│   ├── __init__.py
│   ├── models.py              # Asset dataclass, universe configuration, and types
│   ├── optimizer.py           # PuLP Linear Programming formulation & solver
│   └── audit_logger.py        # Plain-English trade explanation & delta narrative engine
├── tests/
│   └── test_optimizer.py      # Unit test suite verifying LP constraints & shock dynamics
└── README.md                  # Project documentation
```
