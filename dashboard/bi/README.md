# NexusBI Enterprise • Business Intelligence Suite (Examples 16–20)
**Modern SaaS Dashboard Redesign & Interactive BI Analytics**

NexusBI Enterprise is a modern, high-performance SaaS Business Intelligence platform featuring 5 interactive analytics dashboards (Examples 16 through 20), designed with an executive-grade user interface, dark/light theme switching, multi-currency recalculation, CSV export engines, and deep-dive inspection drawers.

---

## 🌟 Included BI Modules

### 16. Monthly Sales Performance Analysis
* **Core KPIs**: Total Monthly Sales Revenue, Order Volume, Average Order Value (AOV), and Month-over-Month (MoM) Growth Rate.
* **Interactive Visualizations**:
  - Current Year vs Prior Year Monthly Revenue comparison line chart with area fill and variance tooltips.
  - Sales Performance by Product Category (horizontal bar chart with revenue shares).
  - Geographic Sales Distribution (interactive doughnut chart by region: North America, Europe, APAC, LATAM, Middle East).
  - Ranked Top 5 Best-Selling Products table with trend indicators.
* **Interactions**:
  - Filter by Quarterly periods (Q1, Q2, Q3, Q4) or Full Year.
  - Filter by Active vs Prior Year.
  - Filter by Product Category.
  - **Instant CSV Export**: Generates and downloads a clean, formatted CSV of all sales records with one click.

---

### 17. Product Profitability Analysis
* **Core KPIs**: Total Portfolio Revenue, Total COGS / Direct Costs, Net Gross Profit, and Gross Margin %.
* **Interactive Visualizations**:
  - Revenue vs Cost (COGS) side-by-side grouped bar chart.
  - Product-level Gross Profit Margin visualization with benchmark threshold (>50% green, >20% yellow, <20% red).
  - Most Profitable vs Watchlist / Loss-Making items breakdown.
* **Interactions**:
  - Filter by Product Category.
  - Sort by Gross Profit ($), Revenue ($), Cost ($), or Margin (%).
  - **Click-to-Inspect Modal**: Clicking any product row opens the **Product Unit Economics Drawer**, revealing unit retail price, direct infrastructure allocation, customer support/SLA overhead, transaction fees, net contribution, and automated AI profitability recommendations.

---

### 18. Inventory Analytics & Restock Manager
* **Core KPIs**: Total Inventory Value ($), Stock Units On Hand, Low-Stock Alerts, Out-of-Stock Criticals, and Overstocked SKUs (>90 days supply).
* **Interactive Visualizations**:
  - Stock Health Distribution chart (In Stock, Low Stock, Stockout, Overstock).
  - Capital tied up in Inventory by Category bar chart.
  - Turnover velocity ratings (Fast, Moderate, Slow movers).
* **Interactions**:
  - Real-time instant search by SKU or Product Name.
  - Filter by Stock Status (In Stock, Low Stock Alert, Out of Stock, Overstocked).
  - Visual status badges and warning highlights for critical inventory items.
  - **Automated Reorder Action**: Clicking "Reorder" or opening the item drawer generates an automated Purchase Order (PO) with Economic Order Quantity (EOQ) calculations, warehouse location tracking, and an interactive confirmation toast.

---

### 19. Customer Purchase Behaviour Analysis
* **Core KPIs**: Total Active Customers, New Customer Acquisition (+18.4% MoM), Returning Buyers (84.6%), Repeat Purchase Rate (68.4%), Average Customer Lifetime Value (CLV), and Purchase Frequency.
* **Interactive Visualizations**:
  - Customer Segmentation Distribution (Champions VIP, Loyal Regulars, Potential Loyalists, At Risk / Slipping, Hibernating).
  - 12-Month Cohort Retention Decay curve.
  - Spend Behaviour: Annual Spend vs. Predicted CLV by segment.
  - Top Spending Customers Leaderboard with RFM (Recency, Frequency, Monetary) scoring.
* **Interactions**:
  - Filter by Customer Cohort / Segment.
  - Instant search by Customer Name or Contact Email.
  - **Customer 360° Profile Modal**: Inspect full account profile, RFM scores, projected CLV, and past purchase history ledger.

---

### 20. Executive Financial & Revenue Forecast Analysis
* **Core KPIs**: Annual Run-Rate (ARR), Net Operating Margin %, Total Operating Expenses (OpEx), Runway Duration (Months), and Historical Forecast Accuracy.
* **Interactive Visualizations**:
  - Predictive Revenue Forecast with dynamic Scenario Modeling (Bull Case +15%, Base Case, Bear Case -10%) and confidence bands.
  - Operating Expenses (OpEx) departmental distribution doughnut chart.
  - Quarterly Cash Flow Trajectory (Operating Inflow vs OpEx and CapEx).
  - Departmental Budget vs. Actual Variance analysis table.
* **Interactions**:
  - Dynamic forecast horizon selector (3 Months, 6 Months, 12 Months).
  - Scenario toggle (Base, Bull, Bear) dynamically re-renders confidence projections in real time.

---

## 🎨 Design & SaaS Architecture

1. **Dark & Light Modes**:
   - Dark Mode: Ultra-sleek slate theme (`#090d16` background, `#0f172a` glass cards, glowing accent indicators).
   - Light Mode: Clean SaaS aesthetic with crisp slate typography and soft borders.
   - 1-click theme switch persisted in `localStorage`.
2. **Multi-Currency Converter**:
   - Instant live conversion across USD (`$`), INR (`₹`), and EUR (`€`).
   - Dynamically converts all KPI cards, table rows, and Chart.js tooltips.
3. **Chart.js 4.4 Engine**:
   - Automatically adapts axes, grids, and tooltips to the active color scheme.
   - Smooth easing transitions between filters and tab switches.
4. **Interactive Modals & Toast System**:
   - Unobtrusive floating glass toast notifications for asynchronous actions (PO generation, CSV download, currency switch).
   - Deep-dive slide-overs and dialogs for product unit economics, warehouse logistics, and customer profiles.

---

## 🚀 How to Run

### Method 1: Instant Browser Launch (Zero Installation)
Simply double-click or open `index.html` in any modern web browser (Chrome, Edge, Firefox, Safari):
```
file:///C:/Users/Shrithil S Shetty/.gemini/antigravity/scratch/bi-saas-dashboard/index.html
```

### Method 2: Python Development Server
```bash
cd "C:\Users\Shrithil S Shetty\.gemini\antigravity\scratch\bi-saas-dashboard"
python server.py
# Opens automatically at http://localhost:8080
```

### Method 3: Node.js Server
```bash
cd "C:\Users\Shrithil S Shetty\.gemini\antigravity\scratch\bi-saas-dashboard"
node server.js
# Open http://localhost:8080 in your browser
```
