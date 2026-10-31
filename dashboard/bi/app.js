/**
 * NexusBI Enterprise - Core Dashboard Application Logic
 * Interactive state, Chart.js managers, filtering, modal controllers, and CSV export.
 */

const AppState = {
  activeModule: 16, // 16 to 20
  currency: 'USD',
  theme: localStorage.getItem('nexus_theme') || 'dark',

  // Filters for Example 16 (Sales)
  salesFilters: {
    year: '2025',
    category: 'All',
    region: 'All',
    period: 'All'
  },

  // Filters for Example 17 (Profitability)
  profitFilters: {
    category: 'All',
    sortBy: 'profit', // 'revenue', 'cost', 'profit', 'margin'
    sortOrder: 'desc'
  },

  // Filters for Example 18 (Inventory)
  inventoryFilters: {
    search: '',
    status: 'All', // 'All', 'In Stock', 'Low Stock', 'Out of Stock', 'Overstocked'
    category: 'All',
    sortBy: 'stock',
    sortOrder: 'desc'
  },

  // Filters for Example 19 (Customer Behaviour)
  customerFilters: {
    search: '',
    segment: 'All',
    dateRange: '1Y'
  },

  // Filters for Example 20 (Executive Forecast)
  forecastFilters: {
    horizon: 6, // 3, 6, 12 months
    scenario: 'base' // 'bull', 'base', 'bear'
  },

  // Chart references to prevent memory leaks / overlap
  charts: {}
};

// Currency Formatter
function formatCurrency(val, decimals = 0) {
  if (val === null || val === undefined) return '–';
  const c = BIData.currencies[AppState.currency] || BIData.currencies.USD;
  const converted = val * c.rate;
  if (Math.abs(converted) >= 1e6) {
    return `${c.symbol}${(converted / 1e6).toFixed(1)}M`;
  }
  if (Math.abs(converted) >= 1e3 && decimals === 0) {
    return `${c.symbol}${Math.round(converted).toLocaleString()}`;
  }
  return `${c.symbol}${converted.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`;
}

function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  return Number(num).toLocaleString();
}

// Toast Notification
function showToast(title, message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const bg = type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
             type === 'warning' ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' :
             'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';

  toast.className = `flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-2xl transition-all duration-300 transform translate-y-4 opacity-0 ${bg}`;
  toast.innerHTML = `
    <div class="mt-0.5 text-lg">
      ${type === 'success' ? '✓' : type === 'warning' ? '⚠' : 'ℹ'}
    </div>
    <div class="flex-1">
      <h4 class="text-sm font-semibold text-slate-100">${title}</h4>
      <p class="text-xs text-slate-400 mt-0.5">${message}</p>
    </div>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-4', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('opacity-0', 'translate-x-8');
    setTimeout(() => toast.remove(), 350);
  }, 4000);
}

// Global Theme Handler
function toggleTheme() {
  AppState.theme = AppState.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('nexus_theme', AppState.theme);
  applyTheme();
}

function applyTheme() {
  const isDark = AppState.theme === 'dark';
  if (isDark) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  const themeBtn = document.getElementById('theme-toggle-btn');
  if (themeBtn) {
    themeBtn.innerHTML = isDark
      ? '<i data-lucide="sun" class="w-4 h-4 text-amber-400"></i><span class="hidden sm:inline text-xs font-medium">Light</span>'
      : '<i data-lucide="moon" class="w-4 h-4 text-indigo-400"></i><span class="hidden sm:inline text-xs font-medium">Dark</span>';
    if (window.lucide) lucide.createIcons();
  }

  // Refresh active charts with appropriate grid & label colors
  renderActiveModule();
}

// Module Switcher
function switchModule(moduleNumber) {
  AppState.activeModule = Number(moduleNumber);
  document.querySelectorAll('.module-nav-item').forEach(el => {
    const active = Number(el.dataset.module) === AppState.activeModule;
    if (active) {
      el.className = el.className.replace(/text-slate-400.*?bg-transparent/g, '') + ' bg-indigo-600/10 text-indigo-400 border-indigo-500/30';
    } else {
      el.className = el.className.replace(/bg-indigo-600\/10 text-indigo-400 border-indigo-500\/30/g, '') + ' text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border-transparent';
    }
  });

  document.querySelectorAll('.bi-module-view').forEach(view => {
    view.classList.add('hidden');
  });

  const activeView = document.getElementById(`module-${AppState.activeModule}-view`);
  if (activeView) {
    activeView.classList.remove('hidden');
  }

  renderActiveModule();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderActiveModule() {
  if (window.lucide) lucide.createIcons();

  switch (AppState.activeModule) {
    case 16:
      renderModule16();
      break;
    case 17:
      renderModule17();
      break;
    case 18:
      renderModule18();
      break;
    case 19:
      renderModule19();
      break;
    case 20:
      renderModule20();
      break;
  }
}

// Chart Helpers
function getChartColors() {
  const isDark = AppState.theme === 'dark';
  return {
    grid: isDark ? 'rgba(51, 65, 85, 0.35)' : 'rgba(226, 232, 240, 0.8)',
    text: isDark ? '#94a3b8' : '#64748b',
    tooltipBg: isDark ? '#0f172a' : '#ffffff',
    tooltipBorder: isDark ? '#334155' : '#cbd5e1',
    tooltipText: isDark ? '#f8fafc' : '#0f172a',
    primary: '#6366f1',
    secondary: '#10b981',
    amber: '#f59e0b',
    rose: '#f43f5e',
    cyan: '#06b6d4',
    purple: '#a855f7'
  };
}

function destroyChart(id) {
  if (AppState.charts[id]) {
    AppState.charts[id].destroy();
    delete AppState.charts[id];
  }
}

// ===================================================================
// MODULE 16: MONTHLY SALES PERFORMANCE
// ===================================================================
function renderModule16() {
  const data = BIData.salesPerformance;
  const filteredMonths = data.monthlyData.filter(d => {
    if (AppState.salesFilters.period === 'Q1') return ['Jan', 'Feb', 'Mar'].includes(d.month);
    if (AppState.salesFilters.period === 'Q2') return ['Apr', 'May', 'Jun'].includes(d.month);
    if (AppState.salesFilters.period === 'Q3') return ['Jul', 'Aug', 'Sep'].includes(d.month);
    if (AppState.salesFilters.period === 'Q4') return ['Oct', 'Nov', 'Dec'].includes(d.month);
    return true;
  });

  const totalRevenue = filteredMonths.reduce((acc, m) => acc + m.revenue, 0);
  const totalOrders = filteredMonths.reduce((acc, m) => acc + m.orders, 0);
  const avgAOV = totalOrders > 0 ? (totalRevenue / totalOrders) : 0;
  const priorRevenue = filteredMonths.reduce((acc, m) => acc + m.priorYear, 0);
  const momGrowth = priorRevenue > 0 ? (((totalRevenue - priorRevenue) / priorRevenue) * 100) : 0;

  // Update KPIs
  document.getElementById('m16-kpi-revenue').textContent = formatCurrency(totalRevenue);
  document.getElementById('m16-kpi-orders').textContent = formatNumber(totalOrders);
  document.getElementById('m16-kpi-aov').textContent = formatCurrency(avgAOV, 2);
  const growthEl = document.getElementById('m16-kpi-growth');
  growthEl.textContent = `${momGrowth >= 0 ? '+' : ''}${momGrowth.toFixed(1)}%`;
  growthEl.className = `text-xs font-semibold px-2 py-0.5 rounded-full ${momGrowth >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`;

  // 1. Monthly Revenue Comparison Chart (Current vs Prior)
  const colors = getChartColors();
  destroyChart('m16-revenue-comparison');
  const ctx1 = document.getElementById('m16-chart-revenue-comparison');
  if (ctx1) {
    AppState.charts['m16-revenue-comparison'] = new Chart(ctx1, {
      type: 'line',
      data: {
        labels: filteredMonths.map(d => d.month),
        datasets: [
          {
            label: `Current (${AppState.salesFilters.year})`,
            data: filteredMonths.map(d => d.revenue * (BIData.currencies[AppState.currency]?.rate || 1)),
            borderColor: colors.primary,
            backgroundColor: 'rgba(99, 102, 241, 0.12)',
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointBackgroundColor: colors.primary,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: 'Prior Year',
            data: filteredMonths.map(d => d.priorYear * (BIData.currencies[AppState.currency]?.rate || 1)),
            borderColor: colors.text,
            borderDash: [5, 5],
            backgroundColor: 'transparent',
            tension: 0.35,
            borderWidth: 2,
            pointRadius: 2,
            pointHoverRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: colors.text, font: { size: 12, family: 'Inter' } } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // 2. Sales Performance by Category
  destroyChart('m16-category-chart');
  const ctx2 = document.getElementById('m16-chart-category');
  if (ctx2) {
    const cats = data.categoryBreakdown;
    AppState.charts['m16-category-chart'] = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: cats.map(c => c.category),
        datasets: [{
          label: 'Revenue',
          data: cats.map(c => c.revenue * (BIData.currencies[AppState.currency]?.rate || 1)),
          backgroundColor: [
            'rgba(99, 102, 241, 0.85)',
            'rgba(16, 185, 129, 0.85)',
            'rgba(6, 182, 212, 0.85)',
            'rgba(168, 85, 247, 0.85)',
            'rgba(245, 158, 11, 0.85)'
          ],
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `Revenue: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          },
          y: { grid: { display: false }, ticks: { color: colors.text } }
        }
      }
    });
  }

  // 3. Sales by Region Donut
  destroyChart('m16-region-chart');
  const ctx3 = document.getElementById('m16-chart-region');
  if (ctx3) {
    const regs = data.regionBreakdown;
    AppState.charts['m16-region-chart'] = new Chart(ctx3, {
      type: 'doughnut',
      data: {
        labels: regs.map(r => r.region),
        datasets: [{
          data: regs.map(r => r.revenue * (BIData.currencies[AppState.currency]?.rate || 1)),
          backgroundColor: ['#6366f1', '#10b981', '#06b6d4', '#f59e0b', '#ec4899'],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        cutout: '72%'
      }
    });
  }

  // 4. Top 5 Best-Selling Products Table
  const tbody = document.getElementById('m16-top-products-tbody');
  if (tbody) {
    tbody.innerHTML = data.topSellingProducts.map((p, idx) => `
      <tr class="border-b border-slate-700/30 hover:bg-slate-800/20 transition-colors">
        <td class="py-3 px-4 text-xs font-semibold text-slate-400">#0${idx + 1}</td>
        <td class="py-3 px-4">
          <div class="font-medium text-slate-100 text-sm">${p.name}</div>
          <div class="text-xs text-slate-400">${p.category}</div>
        </td>
        <td class="py-3 px-4 text-right font-medium text-slate-200 text-sm">${formatCurrency(p.revenue)}</td>
        <td class="py-3 px-4 text-right text-xs text-slate-400">${formatNumber(p.units)} units</td>
        <td class="py-3 px-4 text-right">
          <span class="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${p.trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}">
            ${p.trend === 'up' ? '↑' : '↓'} ${Math.abs(p.growth)}%
          </span>
        </td>
      </tr>
    `).join('');
  }
}

// Download CSV for Module 16
function downloadSalesCSV() {
  const months = BIData.salesPerformance.monthlyData;
  let csv = 'Month,Year,Revenue,PriorYearRevenue,Orders,AverageOrderValue,GrowthRate\n';
  months.forEach(m => {
    csv += `${m.month},${m.year},${m.revenue},${m.priorYear},${m.orders},${m.aov.toFixed(2)},${m.growth}%\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sales_performance_report_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast('Export Successful', 'Monthly sales performance report downloaded as CSV.', 'success');
}

// ===================================================================
// MODULE 17: PRODUCT PROFITABILITY
// ===================================================================
function renderModule17() {
  let products = [...BIData.productsProfitability];

  // Category filter
  if (AppState.profitFilters.category !== 'All') {
    products = products.filter(p => p.category === AppState.profitFilters.category);
  }

  // Sorting
  products.sort((a, b) => {
    const valA = a[AppState.profitFilters.sortBy];
    const valB = b[AppState.profitFilters.sortBy];
    return AppState.profitFilters.sortOrder === 'desc' ? valB - valA : valA - valB;
  });

  // KPIs
  const totalRevenue = products.reduce((acc, p) => acc + p.revenue, 0);
  const totalCost = products.reduce((acc, p) => acc + p.cost, 0);
  const grossProfit = totalRevenue - totalCost;
  const grossMargin = totalRevenue > 0 ? ((grossProfit / totalRevenue) * 100) : 0;

  document.getElementById('m17-kpi-revenue').textContent = formatCurrency(totalRevenue);
  document.getElementById('m17-kpi-cost').textContent = formatCurrency(totalCost);
  document.getElementById('m17-kpi-profit').textContent = formatCurrency(grossProfit);
  document.getElementById('m17-kpi-margin').textContent = `${grossMargin.toFixed(1)}%`;

  // 1. Revenue vs Cost Comparison (Grouped Bar Chart)
  const colors = getChartColors();
  destroyChart('m17-rev-cost-chart');
  const ctx1 = document.getElementById('m17-chart-rev-cost');
  if (ctx1) {
    const top7 = products.slice(0, 7);
    AppState.charts['m17-rev-cost-chart'] = new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: top7.map(p => p.name.length > 18 ? p.name.slice(0, 18) + '…' : p.name),
        datasets: [
          {
            label: 'Revenue',
            data: top7.map(p => p.revenue * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(99, 102, 241, 0.85)',
            borderRadius: 6
          },
          {
            label: 'Cost (COGS)',
            data: top7.map(p => p.cost * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(244, 63, 94, 0.85)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // 2. Product-level Profit Margin Visualization (Ranked with Benchmark threshold line)
  destroyChart('m17-margin-chart');
  const ctx2 = document.getElementById('m17-chart-margin');
  if (ctx2) {
    const marginSorted = [...products].sort((a, b) => b.margin - a.margin);
    AppState.charts['m17-margin-chart'] = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: marginSorted.map(p => p.name.length > 16 ? p.name.slice(0, 16) + '…' : p.name),
        datasets: [{
          label: 'Gross Profit Margin %',
          data: marginSorted.map(p => p.margin),
          backgroundColor: marginSorted.map(p => p.margin >= 50 ? 'rgba(16, 185, 129, 0.85)' : p.margin >= 25 ? 'rgba(245, 158, 11, 0.85)' : 'rgba(239, 68, 68, 0.85)'),
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `Gross Margin: ${ctx.raw.toFixed(1)}%`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text, maxRotation: 45 } },
          y: {
            grid: { color: colors.grid },
            ticks: { color: colors.text, callback: (v) => `${v}%` }
          }
        }
      }
    });
  }

  // Table render with interactive product inspection
  const tbody = document.getElementById('m17-products-tbody');
  if (tbody) {
    tbody.innerHTML = products.map(p => `
      <tr class="border-b border-slate-700/30 hover:bg-slate-800/30 cursor-pointer transition-colors group" onclick="openProductModal('${p.id}')">
        <td class="py-3 px-4">
          <div class="font-medium text-slate-100 group-hover:text-indigo-400 transition-colors">${p.name}</div>
          <div class="text-xs text-slate-400">${p.id} • ${p.category}</div>
        </td>
        <td class="py-3 px-4 text-right font-medium text-slate-200">${formatCurrency(p.revenue)}</td>
        <td class="py-3 px-4 text-right text-slate-400">${formatCurrency(p.cost)}</td>
        <td class="py-3 px-4 text-right font-semibold ${p.profit >= 0 ? 'text-emerald-400' : 'text-rose-400'}">${formatCurrency(p.profit)}</td>
        <td class="py-3 px-4 text-right">
          <span class="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${p.margin >= 50 ? 'bg-emerald-500/10 text-emerald-400' : p.margin >= 20 ? 'bg-amber-500/10 text-amber-400' : 'bg-rose-500/10 text-rose-400'}">
            ${p.margin.toFixed(1)}%
          </span>
        </td>
        <td class="py-3 px-4 text-center">
          <button class="text-xs text-slate-400 hover:text-indigo-400 p-1.5 rounded-lg hover:bg-slate-700/50 transition-colors">
            Inspect →
          </button>
        </td>
      </tr>
    `).join('');
  }
}

// Open Product Profitability Modal
function openProductModal(productId) {
  const p = BIData.productsProfitability.find(x => x.id === productId);
  if (!p) return;

  const modal = document.getElementById('product-detail-modal');
  const title = document.getElementById('modal-product-title');
  const body = document.getElementById('modal-product-body');

  title.textContent = p.name;
  body.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Retail Unit Price</div>
        <div class="text-lg font-bold text-slate-100 mt-1">${formatCurrency(p.unitPrice, 2)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Unit COGS Cost</div>
        <div class="text-lg font-bold text-rose-400 mt-1">${formatCurrency(p.unitCost, 2)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Unit Gross Profit</div>
        <div class="text-lg font-bold text-emerald-400 mt-1">${formatCurrency(p.unitPrice - p.unitCost, 2)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Gross Margin</div>
        <div class="text-lg font-bold text-indigo-400 mt-1">${p.margin.toFixed(1)}%</div>
      </div>
    </div>

    <div class="space-y-3 p-4 bg-slate-800/30 rounded-xl border border-slate-700/40 mb-6">
      <h5 class="text-xs font-semibold uppercase tracking-wider text-slate-400">Unit Economics & Allocation</h5>
      <div class="space-y-2 text-xs">
        <div class="flex justify-between py-1 border-b border-slate-700/30">
          <span class="text-slate-400">Direct Infrastructure / Server Allocation</span>
          <span class="font-medium text-slate-200">${formatCurrency(p.unitCost * 0.65, 2)}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-slate-700/30">
          <span class="text-slate-400">Customer Support & SLAs</span>
          <span class="font-medium text-slate-200">${formatCurrency(p.unitCost * 0.20, 2)}</span>
        </div>
        <div class="flex justify-between py-1 border-b border-slate-700/30">
          <span class="text-slate-400">Payment Gateway & Transaction Fees (2.5%)</span>
          <span class="font-medium text-slate-200">${formatCurrency(p.unitPrice * 0.025, 2)}</span>
        </div>
        <div class="flex justify-between py-1">
          <span class="text-slate-400">Net Contribution per Unit</span>
          <span class="font-semibold text-emerald-400">${formatCurrency((p.unitPrice - p.unitCost) - (p.unitPrice * 0.025), 2)}</span>
        </div>
      </div>
    </div>

    <div class="p-4 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
      <div class="flex items-center gap-2 text-indigo-400 text-sm font-semibold mb-1">
        <span>AI Profitability Recommendation</span>
      </div>
      <p class="text-xs text-slate-300">
        ${p.margin < 30 ? 'Target COGS reduction via contract renegotiation with infrastructure providers. A price increase of 8% will boost gross margin to healthy 38% without hurting customer conversion.' : 'High-margin asset. Double-down on marketing spend and feature in bundle promotions to accelerate enterprise adoption.'}
      </p>
    </div>
  `;

  modal.classList.remove('hidden');
}

function closeProductModal() {
  document.getElementById('product-detail-modal').classList.add('hidden');
}

// ===================================================================
// MODULE 18: INVENTORY MANAGEMENT
// ===================================================================
function renderModule18() {
  let catalog = [...BIData.inventoryCatalog];

  // Search filter
  if (AppState.inventoryFilters.search) {
    const q = AppState.inventoryFilters.search.toLowerCase();
    catalog = catalog.filter(i => i.name.toLowerCase().includes(q) || i.sku.toLowerCase().includes(q));
  }

  // Status filter
  if (AppState.inventoryFilters.status !== 'All') {
    catalog = catalog.filter(i => i.status === AppState.inventoryFilters.status);
  }

  // Category filter
  if (AppState.inventoryFilters.category !== 'All') {
    catalog = catalog.filter(i => i.category === AppState.inventoryFilters.category);
  }

  // Sorting
  catalog.sort((a, b) => {
    const valA = a[AppState.inventoryFilters.sortBy];
    const valB = b[AppState.inventoryFilters.sortBy];
    return AppState.inventoryFilters.sortOrder === 'desc' ? valB - valA : valA - valB;
  });

  // KPIs across all inventory
  const allItems = BIData.inventoryCatalog;
  const totalValue = allItems.reduce((acc, i) => acc + (i.stock * i.unitCost), 0);
  const totalUnits = allItems.reduce((acc, i) => acc + i.stock, 0);
  const lowStockCount = allItems.filter(i => i.status === 'Low Stock').length;
  const outOfStockCount = allItems.filter(i => i.status === 'Out of Stock').length;
  const overstockedCount = allItems.filter(i => i.status === 'Overstocked').length;

  document.getElementById('m18-kpi-value').textContent = formatCurrency(totalValue);
  document.getElementById('m18-kpi-units').textContent = formatNumber(totalUnits);
  document.getElementById('m18-kpi-low').textContent = lowStockCount;
  document.getElementById('m18-kpi-out').textContent = outOfStockCount;
  document.getElementById('m18-kpi-over').textContent = overstockedCount;

  // 1. Stock Status Distribution Donut Chart
  const colors = getChartColors();
  destroyChart('m18-stock-dist-chart');
  const ctx1 = document.getElementById('m18-chart-stock-dist');
  if (ctx1) {
    const inStock = allItems.filter(i => i.status === 'In Stock').length;
    AppState.charts['m18-stock-dist-chart'] = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: ['In Stock', 'Low Stock', 'Out of Stock', 'Overstocked'],
        datasets: [{
          data: [inStock, lowStockCount, outOfStockCount, overstockedCount],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText
          }
        },
        cutout: '70%'
      }
    });
  }

  // 2. Inventory Value by Category Bar Chart
  destroyChart('m18-category-val-chart');
  const ctx2 = document.getElementById('m18-chart-category-val');
  if (ctx2) {
    const catMap = {};
    allItems.forEach(i => {
      catMap[i.category] = (catMap[i.category] || 0) + (i.stock * i.unitCost);
    });

    AppState.charts['m18-category-val-chart'] = new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: Object.keys(catMap),
        datasets: [{
          label: 'Asset Value',
          data: Object.values(catMap).map(v => v * (BIData.currencies[AppState.currency]?.rate || 1)),
          backgroundColor: 'rgba(99, 102, 241, 0.85)',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `Value: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // Table render with highlighted low/out of stock
  const tbody = document.getElementById('m18-inventory-tbody');
  if (tbody) {
    tbody.innerHTML = catalog.map(item => {
      const isOut = item.status === 'Out of Stock';
      const isLow = item.status === 'Low Stock';
      const isOver = item.status === 'Overstocked';
      const badgeClass = isOut ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                         isLow ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                         isOver ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' :
                         'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30';

      return `
        <tr class="border-b border-slate-700/30 hover:bg-slate-800/20 cursor-pointer transition-colors" onclick="openInventoryModal('${item.sku}')">
          <td class="py-3 px-4">
            <div class="font-medium text-slate-100 hover:text-indigo-400 transition-colors">${item.name}</div>
            <div class="text-xs text-slate-400 font-mono">${item.sku} • ${item.category}</div>
          </td>
          <td class="py-3 px-4 text-center">
            <span class="inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full ${badgeClass}">
              ${item.status}
            </span>
          </td>
          <td class="py-3 px-4 text-right font-medium ${isOut ? 'text-rose-400 font-bold' : isLow ? 'text-amber-400' : 'text-slate-200'}">
            ${formatNumber(item.stock)}
          </td>
          <td class="py-3 px-4 text-right text-xs text-slate-400">${item.minSafety}</td>
          <td class="py-3 px-4 text-right font-medium text-slate-300">${formatCurrency(item.unitCost * item.stock)}</td>
          <td class="py-3 px-4 text-right text-xs text-slate-400">${item.turnover}x / yr</td>
          <td class="py-3 px-4 text-center">
            <button class="text-xs font-medium px-2.5 py-1 rounded-lg ${isLow || isOut ? 'bg-indigo-600 text-white hover:bg-indigo-500' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'} transition-all" onclick="event.stopPropagation(); triggerReorder('${item.sku}')">
              ${isLow || isOut ? 'Reorder' : 'View'}
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }
}

// Inventory Modal
function openInventoryModal(sku) {
  const item = BIData.inventoryCatalog.find(x => x.sku === sku);
  if (!item) return;

  const modal = document.getElementById('inventory-detail-modal');
  const title = document.getElementById('modal-inventory-title');
  const body = document.getElementById('modal-inventory-body');

  title.textContent = item.name;
  body.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Current Stock</div>
        <div class="text-lg font-bold ${item.stock === 0 ? 'text-rose-400' : item.stock < item.minSafety ? 'text-amber-400' : 'text-slate-100'} mt-1">
          ${item.stock} units
        </div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Safety Buffer</div>
        <div class="text-lg font-bold text-slate-200 mt-1">${item.minSafety} units</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Unit Asset Cost</div>
        <div class="text-lg font-bold text-slate-200 mt-1">${formatCurrency(item.unitCost)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Restock Lead Time</div>
        <div class="text-lg font-bold text-indigo-400 mt-1">${item.leadTimeDays} days</div>
      </div>
    </div>

    <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/40 space-y-3 mb-6 text-xs">
      <div class="flex justify-between py-1 border-b border-slate-700/30">
        <span class="text-slate-400">Warehouse Location</span>
        <span class="font-mono text-slate-200">Zone-A / Rack-4B / Bin-12</span>
      </div>
      <div class="flex justify-between py-1 border-b border-slate-700/30">
        <span class="text-slate-400">Annual Inventory Velocity</span>
        <span class="font-semibold text-emerald-400">${item.turnover}x (High Demand)</span>
      </div>
      <div class="flex justify-between py-1 border-b border-slate-700/30">
        <span class="text-slate-400">Recommended Order Quantity (EOQ)</span>
        <span class="font-bold text-slate-100">${item.reorderQty} units</span>
      </div>
      <div class="flex justify-between py-1">
        <span class="text-slate-400">Estimated Restock Investment</span>
        <span class="font-bold text-indigo-400">${formatCurrency(item.reorderQty * item.unitCost)}</span>
      </div>
    </div>

    <div class="flex justify-end gap-3">
      <button class="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors" onclick="closeInventoryModal()">
        Cancel
      </button>
      <button class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition-all" onclick="triggerReorder('${item.sku}')">
        Generate Purchase Order (${item.reorderQty} units)
      </button>
    </div>
  `;

  modal.classList.remove('hidden');
}

function closeInventoryModal() {
  document.getElementById('inventory-detail-modal').classList.add('hidden');
}

function triggerReorder(sku) {
  const item = BIData.inventoryCatalog.find(x => x.sku === sku);
  if (!item) return;

  closeInventoryModal();
  showToast(
    'Purchase Order Created',
    `PO #PO-${Math.floor(100000 + Math.random() * 900000)} issued for ${item.reorderQty} units of ${item.name} (${formatCurrency(item.reorderQty * item.unitCost)}).`,
    'success'
  );
}

// ===================================================================
// MODULE 19: CUSTOMER PURCHASE BEHAVIOUR
// ===================================================================
function renderModule19() {
  const custData = BIData.customerAnalytics;
  const metrics = custData.metrics;

  document.getElementById('m19-kpi-total').textContent = formatNumber(metrics.totalCustomers);
  document.getElementById('m19-kpi-new').textContent = formatNumber(metrics.newCustomers);
  document.getElementById('m19-kpi-returning').textContent = formatNumber(metrics.returningCustomers);
  document.getElementById('m19-kpi-clv').textContent = formatCurrency(metrics.avgCLV);
  document.getElementById('m19-kpi-freq').textContent = `${metrics.avgPurchaseFrequency}x / yr`;
  document.getElementById('m19-kpi-aov').textContent = formatCurrency(metrics.avgOrderValue, 2);
  document.getElementById('m19-kpi-repeat').textContent = `${metrics.repeatPurchaseRate}%`;

  // 1. Customer Segmentation Distribution Chart
  const colors = getChartColors();
  destroyChart('m19-segment-chart');
  const ctx1 = document.getElementById('m19-chart-segment');
  if (ctx1) {
    AppState.charts['m19-segment-chart'] = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: custData.segments.map(s => s.name),
        datasets: [{
          data: custData.segments.map(s => s.count),
          backgroundColor: custData.segments.map(s => s.color),
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.label}: ${formatNumber(ctx.raw)} (${((ctx.raw / metrics.totalCustomers) * 100).toFixed(1)}%)`
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  // 2. Customer Retention Cohort Curve Line Chart
  destroyChart('m19-retention-chart');
  const ctx2 = document.getElementById('m19-chart-retention');
  if (ctx2) {
    AppState.charts['m19-retention-chart'] = new Chart(ctx2, {
      type: 'line',
      data: {
        labels: custData.retentionTrends.map(r => r.month),
        datasets: [{
          label: 'Customer Retention Rate %',
          data: custData.retentionTrends.map(r => r.retention),
          borderColor: colors.secondary,
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: colors.secondary
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `Retention: ${ctx.raw.toFixed(1)}%`
            }
          }
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            min: 0,
            max: 100,
            ticks: { color: colors.text, callback: (v) => `${v}%` }
          }
        }
      }
    });
  }

  // 3. Purchase Behaviour by Customer Segment Bar Chart
  destroyChart('m19-segment-behavior-chart');
  const ctx3 = document.getElementById('m19-chart-segment-behavior');
  if (ctx3) {
    AppState.charts['m19-segment-behavior-chart'] = new Chart(ctx3, {
      type: 'bar',
      data: {
        labels: custData.segments.map(s => s.name.split(' ')[0]),
        datasets: [
          {
            label: 'Avg Spend / Year',
            data: custData.segments.map(s => s.avgSpend * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(99, 102, 241, 0.85)',
            borderRadius: 6
          },
          {
            label: 'Predicted CLV',
            data: custData.segments.map(s => s.clv * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // Top Customers Table
  let topCustomers = [...custData.topCustomers];
  if (AppState.customerFilters.segment !== 'All') {
    topCustomers = topCustomers.filter(c => c.segment.includes(AppState.customerFilters.segment));
  }
  if (AppState.customerFilters.search) {
    const q = AppState.customerFilters.search.toLowerCase();
    topCustomers = topCustomers.filter(c => c.name.toLowerCase().includes(q) || c.contact.toLowerCase().includes(q));
  }

  const tbody = document.getElementById('m19-customers-tbody');
  if (tbody) {
    tbody.innerHTML = topCustomers.map(c => `
      <tr class="border-b border-slate-700/30 hover:bg-slate-800/30 cursor-pointer transition-colors" onclick="openCustomerModal('${c.id}')">
        <td class="py-3 px-4">
          <div class="font-medium text-slate-100 hover:text-indigo-400 transition-colors">${c.name}</div>
          <div class="text-xs text-slate-400">${c.contact}</div>
        </td>
        <td class="py-3 px-4">
          <span class="inline-flex text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            ${c.segment}
          </span>
        </td>
        <td class="py-3 px-4 text-right font-bold text-emerald-400">${formatCurrency(c.totalSpend)}</td>
        <td class="py-3 px-4 text-right font-medium text-slate-300">${c.orders}</td>
        <td class="py-3 px-4 text-right text-xs text-slate-400 font-mono">${c.lastPurchase}</td>
        <td class="py-3 px-4 text-center">
          <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
            ${c.rfm}
          </span>
        </td>
        <td class="py-3 px-4 text-center">
          <button class="text-xs text-indigo-400 hover:underline">Profile →</button>
        </td>
      </tr>
    `).join('');
  }
}

// Open Customer 360 Profile Modal
function openCustomerModal(customerId) {
  const c = BIData.customerAnalytics.topCustomers.find(x => x.id === customerId);
  if (!c) return;

  const modal = document.getElementById('customer-detail-modal');
  const title = document.getElementById('modal-customer-title');
  const body = document.getElementById('modal-customer-body');

  title.textContent = c.name;
  body.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Total Spend</div>
        <div class="text-lg font-bold text-emerald-400 mt-1">${formatCurrency(c.totalSpend)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Orders Completed</div>
        <div class="text-lg font-bold text-slate-100 mt-1">${c.orders} orders</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">Average Order Value</div>
        <div class="text-lg font-bold text-indigo-400 mt-1">${formatCurrency(c.aov, 2)}</div>
      </div>
      <div class="p-3 bg-slate-800/50 rounded-xl border border-slate-700/40">
        <div class="text-xs text-slate-400">RFM Score</div>
        <div class="text-lg font-bold text-amber-400 mt-1">${c.rfm}</div>
      </div>
    </div>

    <div class="p-4 bg-slate-800/30 rounded-xl border border-slate-700/40 mb-6">
      <h5 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Recent Purchase History</h5>
      <div class="space-y-2 text-xs">
        <div class="flex justify-between py-2 border-b border-slate-700/30">
          <div>
            <div class="font-medium text-slate-200">PO #ORD-98421 • Enterprise Cloud Cluster Node</div>
            <div class="text-slate-400">${c.lastPurchase} • Delivery Approved</div>
          </div>
          <span class="font-bold text-slate-100">${formatCurrency(c.aov * 1.4)}</span>
        </div>
        <div class="flex justify-between py-2 border-b border-slate-700/30">
          <div>
            <div class="font-medium text-slate-200">PO #ORD-94102 • Sentinel Zero-Trust License (Annual)</div>
            <div class="text-slate-400">2026-09-12 • Verified</div>
          </div>
          <span class="font-bold text-slate-100">${formatCurrency(c.aov * 0.9)}</span>
        </div>
        <div class="flex justify-between py-2">
          <div>
            <div class="font-medium text-slate-200">PO #ORD-89240 • Vector AI Inference Subscription</div>
            <div class="text-slate-400">2026-07-05 • Completed</div>
          </div>
          <span class="font-bold text-slate-100">${formatCurrency(c.aov * 0.7)}</span>
        </div>
      </div>
    </div>

    <div class="flex justify-end gap-3">
      <button class="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors" onclick="closeCustomerModal()">
        Close
      </button>
      <button class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition-colors" onclick="showToast('Customer Contacted', 'Account Executive notified for scheduled quarterly review.', 'info')">
        Schedule VIP Check-in
      </button>
    </div>
  `;

  modal.classList.remove('hidden');
}

function closeCustomerModal() {
  document.getElementById('customer-detail-modal').classList.add('hidden');
}

// ===================================================================
// MODULE 20: EXECUTIVE FORECASTING & FINANCIALS
// ===================================================================
function renderModule20() {
  const data = BIData.executiveForecasting;
  const kpis = data.kpis;

  document.getElementById('m20-kpi-arr').textContent = formatCurrency(kpis.annualRunRate);
  document.getElementById('m20-kpi-margin').textContent = `${kpis.netOperatingMargin}%`;
  document.getElementById('m20-kpi-opex').textContent = formatCurrency(kpis.operatingExpenses);
  document.getElementById('m20-kpi-runway').textContent = `${kpis.runwayMonths} Mo`;
  document.getElementById('m20-kpi-acc').textContent = `${kpis.forecastAccuracy}%`;

  // 1. Predictive Revenue Forecasting Chart (Historic + Bull / Base / Bear Projections)
  const colors = getChartColors();
  destroyChart('m20-forecast-chart');
  const ctx1 = document.getElementById('m20-chart-forecast');
  if (ctx1) {
    const horizonCount = 12 + Number(AppState.forecastFilters.horizon);
    const slice = data.historicalAndForecast.slice(0, horizonCount);

    const scenarioKey = AppState.forecastFilters.scenario; // 'bull', 'base', 'bear'
    const scenarioColor = scenarioKey === 'bull' ? colors.secondary : scenarioKey === 'bear' ? colors.amber : colors.primary;

    AppState.charts['m20-forecast-chart'] = new Chart(ctx1, {
      type: 'line',
      data: {
        labels: slice.map(d => d.period),
        datasets: [
          {
            label: 'Historical Actual Revenue',
            data: slice.map(d => d.actual ? d.actual * (BIData.currencies[AppState.currency]?.rate || 1) : null),
            borderColor: colors.text,
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: colors.text
          },
          {
            label: `Forecast Projection (${scenarioKey.toUpperCase()} Scenario)`,
            data: slice.map(d => (d[scenarioKey] || d.actual) * (BIData.currencies[AppState.currency]?.rate || 1)),
            borderColor: scenarioColor,
            borderDash: [6, 4],
            backgroundColor: `${scenarioColor}18`,
            fill: true,
            borderWidth: 2.5,
            pointRadius: slice.map(d => d.isForecast ? 5 : 0),
            pointBackgroundColor: scenarioColor
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: colors.text } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // 2. OpEx Breakdown Donut Chart
  destroyChart('m20-opex-chart');
  const ctx2 = document.getElementById('m20-chart-opex');
  if (ctx2) {
    AppState.charts['m20-opex-chart'] = new Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: data.opexBreakdown.map(o => o.category.split(' ')[0]),
        datasets: [{
          data: data.opexBreakdown.map(o => o.amount),
          backgroundColor: ['#6366f1', '#06b6d4', '#f59e0b', '#ec4899'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.label}: ${formatCurrency(ctx.raw)}`
            }
          }
        },
        cutout: '70%'
      }
    });
  }

  // 3. Cash Flow Trajectory Bar Chart
  destroyChart('m20-cashflow-chart');
  const ctx3 = document.getElementById('m20-chart-cashflow');
  if (ctx3) {
    AppState.charts['m20-cashflow-chart'] = new Chart(ctx3, {
      type: 'bar',
      data: {
        labels: data.cashflowTrends.map(c => c.month),
        datasets: [
          {
            label: 'Operating Cash Inflow',
            data: data.cashflowTrends.map(c => c.operatingInflow * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(16, 185, 129, 0.85)',
            borderRadius: 6
          },
          {
            label: 'OpEx Outflow',
            data: data.cashflowTrends.map(c => c.opexOutflow * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(239, 68, 68, 0.85)',
            borderRadius: 6
          },
          {
            label: 'Net Free Cash',
            data: data.cashflowTrends.map(c => c.netCash * (BIData.currencies[AppState.currency]?.rate || 1)),
            backgroundColor: 'rgba(99, 102, 241, 0.85)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { color: colors.text, boxWidth: 12 } },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            borderColor: colors.tooltipBorder,
            borderWidth: 1,
            titleColor: colors.tooltipText,
            bodyColor: colors.tooltipText,
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw / (BIData.currencies[AppState.currency]?.rate || 1))}`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: colors.text } },
          y: {
            grid: { color: colors.grid },
            ticks: {
              color: colors.text,
              callback: (v) => formatCurrency(v / (BIData.currencies[AppState.currency]?.rate || 1))
            }
          }
        }
      }
    });
  }

  // OpEx Table
  const tbody = document.getElementById('m20-opex-tbody');
  if (tbody) {
    tbody.innerHTML = data.opexBreakdown.map(o => `
      <tr class="border-b border-slate-700/30 hover:bg-slate-800/20 transition-colors">
        <td class="py-3 px-4 font-medium text-slate-100 text-sm">${o.category}</td>
        <td class="py-3 px-4 text-right font-medium text-slate-200">${formatCurrency(o.amount)}</td>
        <td class="py-3 px-4 text-right text-xs text-slate-400">${formatCurrency(o.budget)}</td>
        <td class="py-3 px-4 text-right">
          <span class="inline-flex text-xs font-semibold px-2 py-0.5 rounded-full ${o.variance <= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}">
            ${o.variance <= 0 ? '' : '+'}${o.variance}%
          </span>
        </td>
      </tr>
    `).join('');
  }
}

// Global Initialization
document.addEventListener('DOMContentLoaded', () => {
  applyTheme();

  // Currency Selector
  const currSelect = document.getElementById('currency-selector');
  if (currSelect) {
    currSelect.value = AppState.currency;
    currSelect.addEventListener('change', (e) => {
      AppState.currency = e.target.value;
      renderActiveModule();
      showToast('Currency Updated', `All financial figures converted to ${AppState.currency}.`, 'info');
    });
  }

  // Module Nav Listeners
  document.querySelectorAll('.module-nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const mod = item.dataset.module;
      if (mod) switchModule(mod);
    });
  });

  // Example 16 Listeners
  const m16Period = document.getElementById('m16-filter-period');
  if (m16Period) {
    m16Period.addEventListener('change', (e) => {
      AppState.salesFilters.period = e.target.value;
      renderModule16();
    });
  }

  // Example 17 Listeners
  const m17Category = document.getElementById('m17-filter-category');
  if (m17Category) {
    m17Category.addEventListener('change', (e) => {
      AppState.profitFilters.category = e.target.value;
      renderModule17();
    });
  }
  const m17Sort = document.getElementById('m17-sort-by');
  if (m17Sort) {
    m17Sort.addEventListener('change', (e) => {
      AppState.profitFilters.sortBy = e.target.value;
      renderModule17();
    });
  }

  // Example 18 Listeners
  const m18Search = document.getElementById('m18-search-input');
  if (m18Search) {
    m18Search.addEventListener('input', (e) => {
      AppState.inventoryFilters.search = e.target.value;
      renderModule18();
    });
  }
  const m18Status = document.getElementById('m18-filter-status');
  if (m18Status) {
    m18Status.addEventListener('change', (e) => {
      AppState.inventoryFilters.status = e.target.value;
      renderModule18();
    });
  }

  // Example 19 Listeners
  const m19Segment = document.getElementById('m19-filter-segment');
  if (m19Segment) {
    m19Segment.addEventListener('change', (e) => {
      AppState.customerFilters.segment = e.target.value;
      renderModule19();
    });
  }
  const m19Search = document.getElementById('m19-search-input');
  if (m19Search) {
    m19Search.addEventListener('input', (e) => {
      AppState.customerFilters.search = e.target.value;
      renderModule19();
    });
  }

  // Example 20 Listeners
  const m20Horizon = document.getElementById('m20-horizon-select');
  if (m20Horizon) {
    m20Horizon.addEventListener('change', (e) => {
      AppState.forecastFilters.horizon = Number(e.target.value);
      renderModule20();
    });
  }
  const m20Scenario = document.getElementById('m20-scenario-select');
  if (m20Scenario) {
    m20Scenario.addEventListener('change', (e) => {
      AppState.forecastFilters.scenario = e.target.value;
      renderModule20();
    });
  }

  // Initial render
  switchModule(16);
});
