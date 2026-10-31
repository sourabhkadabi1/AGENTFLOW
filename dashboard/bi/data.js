/**
 * NexusBI Enterprise - Mock Business Intelligence Dataset
 * Comprehensive, realistic data for Examples 16-20
 */

const BIData = {
  // Global metadata
  currencies: {
    USD: { symbol: '$', rate: 1.0 },
    INR: { symbol: '₹', rate: 86.5 },
    EUR: { symbol: '€', rate: 0.92 }
  },

  categories: ['All', 'Enterprise Cloud', 'Developer Tools', 'Cyber Security', 'Data & AI', 'IoT & Hardware'],
  regions: ['All', 'North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East'],

  // ==========================================
  // EXAMPLE 16: MONTHLY SALES PERFORMANCE DATA
  // ==========================================
  salesPerformance: {
    monthlyData: [
      { month: 'Jan', year: 2025, revenue: 980000, priorYear: 820000, orders: 5800, aov: 168.96, growth: 12.5 },
      { month: 'Feb', year: 2025, revenue: 1050000, priorYear: 890000, orders: 6100, aov: 172.13, growth: 7.1 },
      { month: 'Mar', year: 2025, revenue: 1180000, priorYear: 970000, orders: 6900, aov: 171.01, growth: 12.4 },
      { month: 'Apr', year: 2025, revenue: 1120000, priorYear: 940000, orders: 6600, aov: 169.70, growth: -5.1 },
      { month: 'May', year: 2025, revenue: 1240000, priorYear: 1020000, orders: 7200, aov: 172.22, growth: 10.7 },
      { month: 'Jun', year: 2025, revenue: 1310000, priorYear: 1080000, orders: 7600, aov: 172.37, growth: 5.6 },
      { month: 'Jul', year: 2025, revenue: 1290000, priorYear: 1090000, orders: 7500, aov: 172.00, growth: -1.5 },
      { month: 'Aug', year: 2025, revenue: 1350000, priorYear: 1130000, orders: 7800, aov: 173.08, growth: 4.7 },
      { month: 'Sep', year: 2025, revenue: 1390000, priorYear: 1160000, orders: 8100, aov: 171.60, growth: 3.0 },
      { month: 'Oct', year: 2025, revenue: 1420000, priorYear: 1200000, orders: 8250, aov: 172.12, growth: 2.2 },
      { month: 'Nov', year: 2025, revenue: 1560000, priorYear: 1310000, orders: 9000, aov: 173.33, growth: 9.9 },
      { month: 'Dec', year: 2025, revenue: 1680000, priorYear: 1420000, orders: 9650, aov: 174.09, growth: 7.7 }
    ],
    categoryBreakdown: [
      { category: 'Enterprise Cloud', revenue: 4950000, share: 34.1, orders: 19800, growth: 18.2 },
      { category: 'Cyber Security', revenue: 3620000, share: 24.9, orders: 16200, growth: 22.4 },
      { category: 'Data & AI', revenue: 2980000, share: 20.5, orders: 15100, growth: 31.8 },
      { category: 'Developer Tools', revenue: 1860000, share: 12.8, orders: 24300, growth: 8.5 },
      { category: 'IoT & Hardware', revenue: 1120000, share: 7.7, orders: 5100, growth: 4.2 }
    ],
    regionBreakdown: [
      { region: 'North America', revenue: 6250000, share: 43.0, orders: 36200 },
      { region: 'Europe', revenue: 3950000, share: 27.2, orders: 23100 },
      { region: 'Asia Pacific', revenue: 2780000, share: 19.1, orders: 16800 },
      { region: 'Latin America', revenue: 940000, share: 6.5, orders: 5900 },
      { region: 'Middle East', revenue: 610000, share: 4.2, orders: 3500 }
    ],
    topSellingProducts: [
      { id: 'PRD-01', name: 'Nexus Cloud Enterprise Tier', category: 'Enterprise Cloud', revenue: 2180000, units: 3640, growth: 24.1, trend: 'up' },
      { id: 'PRD-02', name: 'Sentinel Zero-Trust Gateway', category: 'Cyber Security', revenue: 1740000, units: 2900, growth: 19.5, trend: 'up' },
      { id: 'PRD-03', name: 'Cortex Vector AI Pipeline', category: 'Data & AI', revenue: 1450000, units: 2420, growth: 38.2, trend: 'up' },
      { id: 'PRD-04', name: 'DevFlow CI/CD Cluster Pro', category: 'Developer Tools', revenue: 980000, units: 4900, growth: 11.2, trend: 'up' },
      { id: 'PRD-05', name: 'EdgeMesh Sensor Hub V2', category: 'IoT & Hardware', revenue: 620000, units: 1240, growth: -2.4, trend: 'down' }
    ]
  },

  // ==========================================
  // EXAMPLE 17: PRODUCT PROFITABILITY DATA
  // ==========================================
  productsProfitability: [
    { id: 'PRD-01', name: 'Nexus Cloud Enterprise Tier', category: 'Enterprise Cloud', revenue: 2180000, cost: 741200, profit: 1438800, margin: 66.0, units: 3640, unitPrice: 598.90, unitCost: 203.62, status: 'Hero' },
    { id: 'PRD-02', name: 'Sentinel Zero-Trust Gateway', category: 'Cyber Security', revenue: 1740000, cost: 609000, profit: 1131000, margin: 65.0, units: 2900, unitPrice: 600.00, unitCost: 210.00, status: 'Hero' },
    { id: 'PRD-03', name: 'Cortex Vector AI Pipeline', category: 'Data & AI', revenue: 1450000, cost: 623500, profit: 826500, margin: 57.0, units: 2420, unitPrice: 599.17, unitCost: 257.64, status: 'Star' },
    { id: 'PRD-04', name: 'DevFlow CI/CD Cluster Pro', category: 'Developer Tools', revenue: 980000, cost: 470400, profit: 509600, margin: 52.0, units: 4900, unitPrice: 200.00, unitCost: 96.00, status: 'Star' },
    { id: 'PRD-05', name: 'Nexus Private Cloud Node', category: 'Enterprise Cloud', revenue: 890000, cost: 462800, profit: 427200, margin: 48.0, units: 1100, unitPrice: 809.09, unitCost: 420.73, status: 'Stable' },
    { id: 'PRD-06', name: 'CyberShield Endpoint DLP', category: 'Cyber Security', revenue: 810000, cost: 421200, profit: 388800, margin: 48.0, units: 2700, unitPrice: 300.00, unitCost: 156.00, status: 'Stable' },
    { id: 'PRD-07', name: 'NeuralSearch Index Engine', category: 'Data & AI', revenue: 760000, cost: 395200, profit: 364800, margin: 48.0, units: 1900, unitPrice: 400.00, unitCost: 208.00, status: 'Stable' },
    { id: 'PRD-08', name: 'GitSync Monorepo Runner', category: 'Developer Tools', revenue: 540000, cost: 302400, profit: 237600, margin: 44.0, units: 3600, unitPrice: 150.00, unitCost: 84.00, status: 'Stable' },
    { id: 'PRD-09', name: 'EdgeMesh Sensor Hub V2', category: 'IoT & Hardware', revenue: 620000, cost: 483600, profit: 136400, margin: 22.0, units: 1240, unitPrice: 500.00, unitCost: 390.00, status: 'Low Margin' },
    { id: 'PRD-10', name: 'Legacy SQL Bridge Adapter', category: 'Enterprise Cloud', revenue: 310000, cost: 263500, profit: 46500, margin: 15.0, units: 620, unitPrice: 500.00, unitCost: 425.00, status: 'Low Margin' },
    { id: 'PRD-11', name: 'IoT Cellular Telemetry Card', category: 'IoT & Hardware', revenue: 290000, cost: 266800, profit: 23200, margin: 8.0, units: 1450, unitPrice: 200.00, unitCost: 184.00, status: 'Watchlist' },
    { id: 'PRD-12', name: 'Basic Sandbox Community VM', category: 'Developer Tools', revenue: 140000, cost: 154000, profit: -14000, margin: -10.0, units: 2800, unitPrice: 50.00, unitCost: 55.00, status: 'Loss Maker' }
  ],

  // ==========================================
  // EXAMPLE 18: INVENTORY MANAGEMENT DATA
  // ==========================================
  inventoryCatalog: [
    { sku: 'SKU-CLD-101', name: 'Rackmount Cloud Server Blade X4', category: 'Enterprise Cloud', stock: 142, minSafety: 50, reorderQty: 100, unitCost: 1850, value: 262700, status: 'In Stock', turnover: 4.8, leadTimeDays: 14, movement: 'Fast' },
    { sku: 'SKU-SEC-202', name: 'HSM Cryptographic Security Module', category: 'Cyber Security', stock: 18, minSafety: 25, reorderQty: 40, unitCost: 3400, value: 61200, status: 'Low Stock', turnover: 5.2, leadTimeDays: 21, movement: 'Fast' },
    { sku: 'SKU-SEC-205', name: 'Zero-Trust YubiKey FIPS Token (Box 100)', category: 'Cyber Security', stock: 320, minSafety: 100, reorderQty: 250, unitCost: 950, value: 304000, status: 'In Stock', turnover: 6.4, leadTimeDays: 7, movement: 'Fast' },
    { sku: 'SKU-DAT-301', name: 'GPU Accelerator PCIe Card (H100)', category: 'Data & AI', stock: 0, minSafety: 15, reorderQty: 30, unitCost: 28500, value: 0, status: 'Out of Stock', turnover: 8.9, leadTimeDays: 35, movement: 'Fast' },
    { sku: 'SKU-DAT-308', name: 'NVMe Gen5 Enterprise SSD Array 8TB', category: 'Data & AI', stock: 24, minSafety: 30, reorderQty: 60, unitCost: 1200, value: 28800, status: 'Low Stock', turnover: 5.1, leadTimeDays: 10, movement: 'Fast' },
    { sku: 'SKU-DEV-401', name: 'Developer Testbed SBC Octa-Core', category: 'Developer Tools', stock: 850, minSafety: 200, reorderQty: 300, unitCost: 85, value: 72250, status: 'In Stock', turnover: 4.2, leadTimeDays: 12, movement: 'Moderate' },
    { sku: 'SKU-DEV-412', name: 'Debug Probe JTAG Interface Kit', category: 'Developer Tools', stock: 12, minSafety: 20, reorderQty: 50, unitCost: 240, value: 2880, status: 'Low Stock', turnover: 3.1, leadTimeDays: 15, movement: 'Moderate' },
    { sku: 'SKU-IOT-501', name: 'Industrial IoT LoRa Gateway V3', category: 'IoT & Hardware', stock: 340, minSafety: 80, reorderQty: 120, unitCost: 450, value: 153000, status: 'Overstocked', turnover: 1.4, leadTimeDays: 25, movement: 'Slow' },
    { sku: 'SKU-IOT-504', name: 'Harsh Environment Temp/Humidity Sensor', category: 'IoT & Hardware', stock: 1200, minSafety: 300, reorderQty: 400, unitCost: 65, value: 78000, status: 'Overstocked', turnover: 1.1, leadTimeDays: 20, movement: 'Slow' },
    { sku: 'SKU-IOT-509', name: 'Sub-GHz Wireless Repeater Node', category: 'IoT & Hardware', stock: 0, minSafety: 40, reorderQty: 80, unitCost: 180, value: 0, status: 'Out of Stock', turnover: 2.8, leadTimeDays: 18, movement: 'Moderate' },
    { sku: 'SKU-CLD-118', name: '400Gbps QSFP-DD Fiber Transceiver', category: 'Enterprise Cloud', stock: 85, minSafety: 40, reorderQty: 100, unitCost: 620, value: 52700, status: 'In Stock', turnover: 5.8, leadTimeDays: 8, movement: 'Fast' },
    { sku: 'SKU-SEC-230', name: 'Rackmount Power Redundancy UPS 3U', category: 'Cyber Security', stock: 9, minSafety: 15, reorderQty: 25, unitCost: 2100, value: 18900, status: 'Low Stock', turnover: 2.9, leadTimeDays: 28, movement: 'Moderate' }
  ],

  // ==========================================
  // EXAMPLE 19: CUSTOMER PURCHASE BEHAVIOUR DATA
  // ==========================================
  customerAnalytics: {
    metrics: {
      totalCustomers: 18450,
      newCustomers: 2840,
      returningCustomers: 15610,
      avgCLV: 1425,
      avgPurchaseFrequency: 4.2,
      avgOrderValue: 171.80,
      repeatPurchaseRate: 68.4
    },
    segments: [
      { name: 'Champions (VIP)', count: 2760, share: 15, avgSpend: 4850, frequency: 9.8, clv: 6200, retentionRate: 94.2, color: '#6366f1' },
      { name: 'Loyal Regulars', count: 5160, share: 28, avgSpend: 2100, frequency: 5.4, clv: 2900, retentionRate: 86.5, color: '#10b981' },
      { name: 'Potential Loyalists', count: 4240, share: 23, avgSpend: 1150, frequency: 3.2, clv: 1600, retentionRate: 68.0, color: '#3b82f6' },
      { name: 'At Risk / Slipping', count: 3690, share: 20, avgSpend: 820, frequency: 1.8, clv: 950, retentionRate: 42.1, color: '#f59e0b' },
      { name: 'Hibernating / Churned', count: 2600, share: 14, avgSpend: 340, frequency: 1.1, clv: 380, retentionRate: 14.8, color: '#ef4444' }
    ],
    retentionTrends: [
      { month: 'Month 1', retention: 100 },
      { month: 'Month 2', retention: 84.5 },
      { month: 'Month 3', retention: 76.2 },
      { month: 'Month 4', retention: 71.0 },
      { month: 'Month 5', retention: 68.4 },
      { month: 'Month 6', retention: 65.8 },
      { month: 'Month 7', retention: 64.1 },
      { month: 'Month 8', retention: 62.9 },
      { month: 'Month 9', retention: 61.5 },
      { month: 'Month 10', retention: 60.8 },
      { month: 'Month 11', retention: 59.9 },
      { month: 'Month 12', retention: 59.2 }
    ],
    topCustomers: [
      { id: 'CUST-801', name: 'Apex FinTech Global', contact: 'sarah.j@apexfin.com', segment: 'Champions (VIP)', totalSpend: 124500, orders: 48, lastPurchase: '2026-10-28', aov: 2593.75, rfm: '5-5-5' },
      { id: 'CUST-802', name: 'HyperScale Logistics Corp', contact: 'marcus.v@hyperscale.io', segment: 'Champions (VIP)', totalSpend: 98200, orders: 36, lastPurchase: '2026-10-30', aov: 2727.77, rfm: '5-5-5' },
      { id: 'CUST-803', name: 'BioGenomix Analytics', contact: 'elena.r@biogenomix.org', segment: 'Champions (VIP)', totalSpend: 84600, orders: 29, lastPurchase: '2026-10-24', aov: 2917.24, rfm: '5-4-5' },
      { id: 'CUST-804', name: 'Quantum Leap Labs', contact: 'dr.chen@quantumleap.tech', segment: 'Loyal Regulars', totalSpend: 62400, orders: 24, lastPurchase: '2026-10-18', aov: 2600.00, rfm: '4-4-4' },
      { id: 'CUST-805', name: 'CyberShield Systems GmbH', contact: 'k.weber@cybershield.de', segment: 'Champions (VIP)', totalSpend: 58900, orders: 21, lastPurchase: '2026-10-29', aov: 2804.76, rfm: '5-4-4' },
      { id: 'CUST-806', name: 'Nordic Cloud Alliance', contact: 'bjorn.l@nordiccloud.se', segment: 'Loyal Regulars', totalSpend: 46200, orders: 19, lastPurchase: '2026-10-12', aov: 2431.57, rfm: '4-4-4' },
      { id: 'CUST-807', name: 'Vanguard Digital Media', contact: 't.taylor@vanguard.co', segment: 'Potential Loyalists', totalSpend: 31500, orders: 14, lastPurchase: '2026-09-25', aov: 2250.00, rfm: '3-3-3' },
      { id: 'CUST-808', name: 'OmniRetail Solutions', contact: 'j.patel@omniretail.in', segment: 'At Risk / Slipping', totalSpend: 28400, orders: 11, lastPurchase: '2026-08-14', aov: 2581.81, rfm: '2-3-3' }
    ]
  },

  // ==========================================
  // EXAMPLE 20: EXECUTIVE FORECASTING & FINANCIALS
  // ==========================================
  executiveForecasting: {
    kpis: {
      annualRunRate: 17142000,
      netOperatingMargin: 34.2,
      operatingExpenses: 11279000,
      runwayMonths: 28,
      forecastAccuracy: 96.4
    },
    historicalAndForecast: [
      { period: 'Jan 25', actual: 980000, base: 980000, bull: 980000, bear: 980000, isForecast: false },
      { period: 'Feb 25', actual: 1050000, base: 1050000, bull: 1050000, bear: 1050000, isForecast: false },
      { period: 'Mar 25', actual: 1180000, base: 1180000, bull: 1180000, bear: 1180000, isForecast: false },
      { period: 'Apr 25', actual: 1120000, base: 1120000, bull: 1120000, bear: 1120000, isForecast: false },
      { period: 'May 25', actual: 1240000, base: 1240000, bull: 1240000, bear: 1240000, isForecast: false },
      { period: 'Jun 25', actual: 1310000, base: 1310000, bull: 1310000, bear: 1310000, isForecast: false },
      { period: 'Jul 25', actual: 1290000, base: 1290000, bull: 1290000, bear: 1290000, isForecast: false },
      { period: 'Aug 25', actual: 1350000, base: 1350000, bull: 1350000, bear: 1350000, isForecast: false },
      { period: 'Sep 25', actual: 1390000, base: 1390000, bull: 1390000, bear: 1390000, isForecast: false },
      { period: 'Oct 25', actual: 1420000, base: 1420000, bull: 1420000, bear: 1420000, isForecast: false },
      { period: 'Nov 25', actual: 1560000, base: 1560000, bull: 1560000, bear: 1560000, isForecast: false },
      { period: 'Dec 25', actual: 1680000, base: 1680000, bull: 1680000, bear: 1680000, isForecast: false },
      // Projected 2026
      { period: 'Jan 26 (F)', actual: null, base: 1740000, bull: 1880000, bear: 1620000, isForecast: true },
      { period: 'Feb 26 (F)', actual: null, base: 1810000, bull: 1990000, bear: 1670000, isForecast: true },
      { period: 'Mar 26 (F)', actual: null, base: 1920000, bull: 2140000, bear: 1750000, isForecast: true },
      { period: 'Apr 26 (F)', actual: null, base: 1990000, bull: 2260000, bear: 1790000, isForecast: true },
      { period: 'May 26 (F)', actual: null, base: 2100000, bull: 2420000, bear: 1880000, isForecast: true },
      { period: 'Jun 26 (F)', actual: null, base: 2240000, bull: 2610000, bear: 1970000, isForecast: true }
    ],
    opexBreakdown: [
      { category: 'Research & Engineering (R&D)', amount: 4286000, share: 38.0, budget: 4200000, variance: 2.0 },
      { category: 'Sales & Customer Acquisition', amount: 3609000, share: 32.0, budget: 3800000, variance: -5.0 },
      { category: 'General & Administrative (G&A)', amount: 2030000, share: 18.0, budget: 1950000, variance: 4.1 },
      { category: 'Cloud Infrastructure & Security', amount: 1354000, share: 12.0, budget: 1400000, variance: -3.3 }
    ],
    cashflowTrends: [
      { month: 'Q1', operatingInflow: 3210000, opexOutflow: 2540000, capexOutflow: 320000, netCash: 350000 },
      { month: 'Q2', operatingInflow: 3670000, opexOutflow: 2710000, capexOutflow: 410000, netCash: 550000 },
      { month: 'Q3', operatingInflow: 4030000, opexOutflow: 2890000, capexOutflow: 380000, netCash: 760000 },
      { month: 'Q4', operatingInflow: 4660000, opexOutflow: 3139000, capexOutflow: 490000, netCash: 1031000 }
    ]
  }
};

// Export to window
if (typeof window !== 'undefined') {
  window.BIData = BIData;
}
