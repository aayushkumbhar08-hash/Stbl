Created At: 2026-09-05T21:18:10+05:30
Completed At: 2026-09-05T21:18:10+05:30
File Path: `file:///c:/Users/Aayush/.gemini/antigravity/brain/df835117-58b0-4602-9e07-2cc4fad9878d/walkthrough.md`
Total Lines: 90
Total Bytes: 5705
Showing lines 1 to 90
The following code has been modified to include a line number before every line, in the format: <line_number>: <original_line>. Please note that any changes targeting the original code should remove the line number, colon, and leading space.
1: # Walkthrough: Collateral & Margin Engine
2: 
3: We have designed, built, and verified an institutional-grade **Collateral & Margin Engine** web application powered by **Python**, **PuLP** (Mixed-Integer Linear Programming), **Streamlit**, and **Plotly**.
4: 
5: ---
6: 
7: ## 🏛️ What Was Built
8: 
9: ### 1. Mathematical Optimizer Core (`collateral_engine/optimizer.py` & `models.py`)
10: - **Objective Function**: Minimizes total opportunity cost (yield drag):
11:   $$\min \sum_{i \in \mathcal{A}} x_i \cdot \text{yield\_drag}_i$$
12: - **Constraint 1 (Clearinghouse Margin Requirement)**:
13:   $$\sum_{i \in \mathcal{A}} x_i \cdot (1 - \text{haircut}_i) \ge \text{Margin Requirement}$$
14: - **Constraint 2 (Concentration & Inventory Bounds)**:
15:   $$0 \le x_i \le \min(\text{amount\_owned}_i, \text{max\_concentration}_i)$$
16: - **Cheapest-to-Deliver (CTD) Shadow Frontier**:
17:   $$\text{Effective Cost}_i = \frac{\text{yield\_drag}_i}{1 - \text{haircut}_i}$$
18:   Explains the mathematical hierarchy of asset selection.
19: 
20: ### 2. Plain-English Audit Logger (`collateral_engine/audit_logger.py`)
21: - Evaluates optimization state transitions (baseline vs shock, parameter tweaks).
22: - Generates categorized action logs (`[MARKET SHOCK TRIGGERED]`, `[SUBSTITUTION: SOLD/REDUCED]`, `[SUBSTITUTION: BOUGHT/PLEDGED]`, `[REBALANCE AUDIT SUMMARY]`).
23: - Explains **what** was traded and **why** (e.g. effective cost shifts, haircut devaluations, and concentration cap limits).
24: 
25: ### 3. High-Contrast SaaS UI & Dark Terminal Architecture (`app.py`)
26: - **Global Cream & Navy Palette**:
27:   - Main app background set to warm off-white/cream (`#F7F5F0`).
28:   - Primary text and headers set to deep navy/black (`#111827`).
29: - **Hero Typography & Brand Accent**:
30:   - Massive, bold header: *"Optimize your institutional `<span class="purple-accent">collateral</span>`"* styled with vibrant purple (`#7C3AED`).
31: - **Top Row KPI Metric Cards with Purple Badges**:
32:   - Three high-contrast cards in `st.columns(3)` for **Required Margin**, **Total Collateral Pledged**, and **Total Yield Drag**.
33:   - Small rounded purple tags/badges (`● LIVE CCP`, `● OPTIMIZED`, `● COST BPS`).
34:   - Real-time red/green delta changes triggered instantly upon market stress events.
35: - **The "Dark Terminal" Card (`#18181B`)**:
36:   - Sleek dark-mode container with rounded corners, subtle drop shadow, macOS window dots (`dot-red`, `dot-yellow`, `dot-green`), and monospace title bar.
37:   - Houses the **`plotly.express` stacked bar chart** configured with a transparent background (`rgba(0,0,0,0)`) and primary data bars utilizing the purple accent palette (`#7C3AED`, `#9333EA`, `#34D399`, `#FBBF24`).
38:   - Superimposed red dashed margin threshold line (`fig.add_hline`) with real-time status annotations.
39:   - Houses the **Monospace Action Logs** directly below the chart, formatted with subdued grey timestamps (`#71717A`) and vibrant purple actions/alerts (`#A855F7` / `#C084FC`).
40: - **Enterprise Institutional Risk Console Sidebar (`st.sidebar`)**:
41:   - **Desk Header & Workspace Selector**: `APEX PRIME // RISK & LIQUIDITY DESK` with live status badge `🟢 CCP LIVE FEED CONNECTED` and account switcher.
42:   - **Quick Stress-Scenario Presets**: One-click radio selector (`Baseline Normal`, `2023 SVB Duration Flight`, `Severe Market Liquidity Freeze`) that dynamically triggers inventory and haircut updates and re-solves the LP.
43:   - **Real-Time Collateral Headroom Meter**: Custom progress bar displaying buffer coverage percentage (e.g. `118.5% Funded`), with purple/emerald gradient for funded state and alert red warning (`CRITICAL: PLEDGE DEFICIT`) on breach.
44:   - **Styled Asset Cards with Financial Metadata**: Replaced generic expanders with institutional cards tagging `Level 1 HQLA | 0% Floor`, `AAA Rated | Duration: 2.1Y`, `BBB- (Investment Grade) | Spread: +145bps`, and `High Volatility | S&P 500 Only`.
45:   - **Compact 2x2 Grid Controls**: Streamlined inputs (Owned, Haircut, Max Cap, Yield Drag) into non-scroll 2x2 columns.
46:   - **Institutional Control Bar**: `⚡ Re-Optimize` (Solid Purple `#8A2BE2`), `🔄 Reset` (clean outline), and expander with clearinghouse regulatory clauses (CFTC §39.13(g), EMIR RTS 153/2013, Basel III, BCBS-IOSCO).
47:   - **Micro-Styling Polish**: Purple slider thumbs/tracks (`#8A2BE2`), crisp input borders (`#E5E7EB`), and refined visual hierarchy.
48: 
49: ---
50: 
51: ## 🧪 Verification & Test Results
52: 
53: ### 1. Automated Unit Tests (`tests/test_optimizer.py`)
54: Executed with `python -m unittest tests/test_optimizer.py`:
55: - `test_baseline_optimization`: Verified PuLP solves to `Optimal`, post-haircut margin $\ge \$10,000,000$, and all concentration caps are satisfied.
56: - `test_market_shock_rebalancing`: Verified that when Equity haircut jumps to 50% and margin rises to \$12M, Equities allocation drops and US Treasuries/Cash allocations surge.
57: - `test_infeasibility_handling`: Verified engine detects and diagnoses severe deficits if requirement exceeds portfolio capacity.
58: - `test_concentration_limit_binding`: Verified reallocation to next cheapest asset when a concentration cap binds.
59: - `test_cheapest_to_deliver_order`: Verified effective cost ranking consistency.
60: 
61: **Output:**
62: ```
63: Ran 5 tests in 0.258s
64: OK
65: ```
66: 
67: ### 2. Live Streamlit Server
68: - Verified server is running healthy at `http://localhost:8501`.
69: - Health check `GET http://localhost:8501/_stcore/health` returned `200 ok`.
70: 
71: ---
72: 
73: ## 🖥️ How to Run & Access
74: 
75: 1. **Access the Live Web App**:
76:    The Streamlit app is actively running on port 8501. Open:
77:    ```
78:    http://localhost:8501
79:    ```
80: 
81: 2. **To Start/Restart Manually**:
82:    ```powershell
83:    .venv\Scripts\streamlit.exe run app.py
84:    ```
85: 
86: 3. **To Run Test Suite**:
87:    ```powershell
88:    .venv\Scripts\python.exe -m unittest discover tests
89:    ```
90: 
The above content shows the entire, complete file contents of the requested file.
