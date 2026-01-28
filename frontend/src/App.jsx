import { useState, useEffect } from 'react';
import { api } from './api';
import './App.css';

// Format currency in INR
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '₹0';
  return '₹' + Number(value).toLocaleString('en-IN');
};

// ==================== COMPONENTS ====================

// Navigation Component
function Navigation({ activeTab, setActiveTab, alerts }) {
  const criticalCount = alerts.filter(a => a.level === 'critical').length;

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'inventory', label: 'Inventory' },
    { id: 'orders', label: 'Orders' },
    { id: 'suppliers', label: 'Suppliers' },
    { id: 'warehouses', label: 'Warehouses' },
    { id: 'forecasts', label: 'Forecasts' },
    { id: 'alerts', label: 'Alerts', badge: criticalCount > 0 ? criticalCount : null },
  ];

  return (
    <nav className="nav">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => setActiveTab(tab.id)}
        >
          {tab.label}
          {tab.badge && <span className="nav-badge">{tab.badge}</span>}
        </button>
      ))}
    </nav>
  );
}

// KPI Card Component
function KPICard({ title, value, subtitle, trend }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value">{value}</div>
      <div className="kpi-title">{title}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
      {trend && <div className={`kpi-trend ${trend > 0 ? 'up' : 'down'}`}>{trend > 0 ? '+' : ''}{trend}%</div>}
    </div>
  );
}

// Alert Item Component
function AlertItem({ alert }) {
  const isCritical = alert.level === 'critical';
  return (
    <div className={`alert-item ${isCritical ? 'critical' : 'warning'}`}>
      <span className={`alert-dot ${isCritical ? 'dot-critical' : 'dot-warning'}`}></span>
      <div className="alert-content">
        <div className="alert-product">{alert.product}</div>
        <div className="alert-details">{alert.warehouse} | Stock: {alert.current_stock}</div>
      </div>
      <div className="alert-action">
        <span className="status-pill status-reorder">{alert.type === 'low_stock' ? 'Low Stock' : 'Reorder'}</span>
      </div>
    </div>
  );
}

// ==================== PAGES ====================

// Dashboard Page
function DashboardPage({ kpis, alerts, history, formatCurrency }) {
  const criticalCount = alerts.filter(a => a.level === 'critical').length;
  const warningCount = alerts.filter(a => a.level === 'warning').length;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">Overview of your inventory system</p>
      </div>

      <div className="kpi-grid">
        <KPICard
          title="Inventory Value"
          value={formatCurrency(kpis?.total_inventory_value)}
          subtitle={`${kpis?.total_products || 0} products across ${kpis?.total_warehouses || 0} warehouses`}
        />
        <KPICard
          title="Service Level"
          value={`${(kpis?.average_service_level || 0).toFixed(1)}%`}
          subtitle={`Target: 95% | ${kpis?.simulation_days || 0} days simulated`}
        />
        <KPICard
          title="Orders Placed"
          value={kpis?.total_orders_placed || 0}
          subtitle={`${kpis?.total_units_fulfilled || 0} units fulfilled`}
        />
        <KPICard
          title="Total Cost"
          value={formatCurrency(kpis?.total_cost)}
          subtitle={`Holding: ${formatCurrency(kpis?.total_holding_cost)} | Ordering: ${formatCurrency(kpis?.total_ordering_cost)}`}
        />
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>Active Alerts</h2>
            <div className="alert-badges">
              {criticalCount > 0 && <span className="badge critical">{criticalCount} critical</span>}
              {warningCount > 0 && <span className="badge warning">{warningCount} warnings</span>}
            </div>
          </div>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="empty-state">All systems normal</div>
            ) : (
              alerts.slice(0, 5).map((alert, idx) => (
                <AlertItem key={idx} alert={alert} />
              ))
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Simulation History</h2>
            <span className="badge neutral">{history.length} days</span>
          </div>
          {history.length > 0 ? (
            <div className="history-content">
              <div className="history-stats">
                <div className="history-stat">
                  <div className="stat-value">{formatCurrency(history[0]?.total_inventory_value)}</div>
                  <div className="stat-label">Start Value</div>
                </div>
                <div className="history-stat">
                  <div className="stat-value">{formatCurrency(history[history.length - 1]?.total_inventory_value)}</div>
                  <div className="stat-label">End Value</div>
                </div>
                <div className="history-stat">
                  <div className="stat-value">{(history.reduce((a, b) => a + (b.service_level || 0), 0) / history.length).toFixed(1)}%</div>
                  <div className="stat-label">Avg Service Level</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">Run a simulation to see history data</div>
          )}
        </div>
      </div>
    </div>
  );
}

// Inventory Page
function InventoryPage({ inventory, filter, setFilter, formatCurrency }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'OK': return 'status-ok';
      case 'REORDER': return 'status-reorder';
      case 'CRITICAL': return 'status-critical';
      default: return '';
    }
  };

  const statusCounts = {
    total: inventory.length,
    ok: inventory.filter(i => i.status === 'OK').length,
    reorder: inventory.filter(i => i.status === 'REORDER').length,
    critical: inventory.filter(i => i.status === 'CRITICAL').length,
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Inventory</h1>
        <p className="page-subtitle">Manage and monitor stock levels</p>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <div className="stat-number">{statusCounts.total}</div>
          <div className="stat-text">Total Products</div>
        </div>
        <div className="stat-box ok">
          <div className="stat-number">{statusCounts.ok}</div>
          <div className="stat-text">OK</div>
        </div>
        <div className="stat-box warning">
          <div className="stat-number">{statusCounts.reorder}</div>
          <div className="stat-text">Reorder</div>
        </div>
        <div className="stat-box critical">
          <div className="stat-number">{statusCounts.critical}</div>
          <div className="stat-text">Critical</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Stock Levels</h2>
          <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
            <option value="">All Status</option>
            <option value="OK">OK</option>
            <option value="REORDER">Reorder</option>
            <option value="CRITICAL">Critical</option>
          </select>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Warehouse</th>
                <th>Current Stock</th>
                <th>Reorder Point</th>
                <th>Safety Stock</th>
                <th>EOQ</th>
                <th>Days of Supply</th>
                <th>Value</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {inventory.length === 0 ? (
                <tr><td colSpan="9" className="no-data">No inventory data</td></tr>
              ) : (
                inventory.map((item, idx) => (
                  <tr key={idx} className={item.status === 'CRITICAL' ? 'row-critical' : ''}>
                    <td className="product-cell">
                      <div className="product-name">{item.product_name}</div>
                      <div className="product-id">{item.product_id}</div>
                    </td>
                    <td>{item.warehouse_name}</td>
                    <td className="number">{item.current_stock || 0}</td>
                    <td className="number">{item.reorder_point || 0}</td>
                    <td className="number">{item.safety_stock || 0}</td>
                    <td className="number">{item.eoq || 0}</td>
                    <td className="number">{(item.days_of_supply || 0).toFixed(1)}</td>
                    <td className="number">{formatCurrency(item.stock_value)}</td>
                    <td>
                      <span className={`status-pill ${getStatusClass(item.status)}`}>{item.status}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Orders Page
function OrdersPage({ kpis, orders }) {
  return (
    <div className="page">
      <div className="page-header">
        <h1>Orders</h1>
        <p className="page-subtitle">Track orders and deliveries</p>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <div className="stat-number">{kpis?.total_orders_placed || 0}</div>
          <div className="stat-text">Total Orders</div>
        </div>
        <div className="stat-box ok">
          <div className="stat-number">{kpis?.total_units_fulfilled || 0}</div>
          <div className="stat-text">Units Fulfilled</div>
        </div>
        <div className="stat-box critical">
          <div className="stat-number">{kpis?.total_stockouts || 0}</div>
          <div className="stat-text">Stockouts</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Recent Orders</h2>
          <span className="badge neutral">{orders.length} orders</span>
        </div>
        {orders.length === 0 ? (
          <div className="empty-state">
            <p>No orders yet</p>
            <p className="empty-subtitle">Run a simulation to generate orders when inventory falls below reorder points</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Day</th>
                  <th>Warehouse</th>
                  <th>Product</th>
                  <th>Quantity</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.slice().reverse().map((order, idx) => (
                  <tr key={idx}>
                    <td>Day {order.day}</td>
                    <td>{order.warehouse}</td>
                    <td>{order.product_id}</td>
                    <td className="number">{order.quantity}</td>
                    <td>
                      <span className="status-pill status-reorder">{order.status || 'Ordered'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Suppliers Page
function SuppliersPage({ suppliers }) {
  const totalOrders = suppliers.reduce((a, s) => a + (s.orders_received || 0), 0);
  const totalFulfilled = suppliers.reduce((a, s) => a + (s.orders_fulfilled || 0), 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Suppliers</h1>
        <p className="page-subtitle">Supplier configuration and order fulfillment metrics</p>
      </div>

      <div className="stats-row">
        <div className="stat-box">
          <div className="stat-number">{suppliers.length}</div>
          <div className="stat-text">Total Suppliers</div>
        </div>
        <div className="stat-box ok">
          <div className="stat-number">{totalOrders}</div>
          <div className="stat-text">Orders Received</div>
        </div>
        <div className="stat-box">
          <div className="stat-number">{totalFulfilled}</div>
          <div className="stat-text">Orders Fulfilled</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Supplier Performance</h2>
          <span className="badge neutral">Lead time &amp; reliability are configured values</span>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Supplier</th>
                <th>Lead Time (days)</th>
                <th>Reliability</th>
                <th>Orders Received</th>
                <th>Orders Fulfilled</th>
                <th>Total Units</th>
              </tr>
            </thead>
            <tbody>
              {(!suppliers || suppliers.length === 0) ? (
                <tr><td colSpan="6" className="no-data">No supplier data available</td></tr>
              ) : (
                suppliers.map((s, idx) => (
                  <tr key={idx}>
                    <td className="product-cell">
                      <div className="product-name">{s.name}</div>
                      <div className="product-id">{s.supplier_id}</div>
                    </td>
                    <td className="number">{s.lead_time_days}</td>
                    <td className="number">{(s.reliability * 100).toFixed(0)}%</td>
                    <td className="number">{s.orders_received || 0}</td>
                    <td className="number">{s.orders_fulfilled || 0}</td>
                    <td className="number">{s.total_units_supplied || 0}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Warehouses Page
function WarehousesPage({ warehouses, inventory }) {
  // Group inventory by warehouse
  const warehouseData = {};
  inventory.forEach(item => {
    if (!warehouseData[item.warehouse_id]) {
      warehouseData[item.warehouse_id] = {
        name: item.warehouse_name,
        id: item.warehouse_id,
        products: 0,
        totalValue: 0,
        critical: 0,
        reorder: 0,
        ok: 0
      };
    }
    warehouseData[item.warehouse_id].products++;
    warehouseData[item.warehouse_id].totalValue += item.stock_value || 0;
    if (item.status === 'CRITICAL') warehouseData[item.warehouse_id].critical++;
    else if (item.status === 'REORDER') warehouseData[item.warehouse_id].reorder++;
    else warehouseData[item.warehouse_id].ok++;
  });

  return (
    <div className="page">
      <div className="page-header">
        <h1>Warehouses</h1>
        <p className="page-subtitle">Monitor warehouse capacity and status</p>
      </div>

      <div className="warehouse-grid">
        {Object.values(warehouseData).map((wh, idx) => (
          <div key={idx} className="warehouse-card">
            <div className="warehouse-header">
              <h3>{wh.name}</h3>
              <span className="warehouse-id">{wh.id}</span>
            </div>
            <div className="warehouse-stats">
              <div className="wh-stat">
                <div className="wh-stat-value">{wh.products}</div>
                <div className="wh-stat-label">Products</div>
              </div>
              <div className="wh-stat">
                <div className="wh-stat-value">{formatCurrency(wh.totalValue)}</div>
                <div className="wh-stat-label">Total Value</div>
              </div>
            </div>
            <div className="warehouse-status">
              <span className="wh-status ok">{wh.ok} OK</span>
              <span className="wh-status warning">{wh.reorder} Reorder</span>
              <span className="wh-status critical">{wh.critical} Critical</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Forecasts Page
function ForecastsPage({ forecasts }) {
  const horizon = forecasts[0]?.forecast_horizon_days || 7;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Forecasts</h1>
        <p className="page-subtitle">Demand predictions for the next {horizon} days based on sales history</p>
      </div>

      <div className="card">
        <div className="card-header">
          <h2>Demand Forecasts</h2>
          <span className="badge neutral">Prediction Window: {horizon} days</span>
        </div>
        {(!forecasts || forecasts.length === 0) ? (
          <div className="empty-state">
            <p>No forecast data available</p>
            <p className="empty-subtitle">Run a simulation to generate sales data, then forecasts will be calculated</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Daily Avg Demand</th>
                  <th>Forecast ({forecasts[0]?.forecast_horizon_days || 7} days)</th>
                  <th>Confidence Range</th>
                  <th>Data Points</th>
                </tr>
              </thead>
              <tbody>
                {forecasts.map((f, idx) => (
                  <tr key={idx}>
                    <td className="product-cell">
                      <div className="product-name">{f.product_name || f.product_id}</div>
                      <div className="product-id">{f.warehouse || f.product_id}</div>
                    </td>
                    <td className="number">{f.daily_avg || 0}</td>
                    <td className="number">{f.predicted_total || 0}</td>
                    <td className="number">{f.confidence_lower || 0} - {f.confidence_upper || 0}</td>
                    <td className="number">{f.data_points || 0} days</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// Alerts Page
function AlertsPage({ alerts }) {
  const criticalAlerts = alerts.filter(a => a.level === 'critical');
  const warningAlerts = alerts.filter(a => a.level === 'warning');

  return (
    <div className="page">
      <div className="page-header">
        <h1>Alerts</h1>
        <p className="page-subtitle">System notifications and warnings</p>
      </div>

      <div className="stats-row">
        <div className="stat-box critical">
          <div className="stat-number">{criticalAlerts.length}</div>
          <div className="stat-text">Critical</div>
        </div>
        <div className="stat-box warning">
          <div className="stat-number">{warningAlerts.length}</div>
          <div className="stat-text">Warnings</div>
        </div>
        <div className="stat-box">
          <div className="stat-number">{alerts.length}</div>
          <div className="stat-text">Total Alerts</div>
        </div>
      </div>

      {criticalAlerts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2>Critical Alerts</h2>
            <span className="badge critical">{criticalAlerts.length}</span>
          </div>
          <div className="alerts-list full">
            {criticalAlerts.map((alert, idx) => (
              <AlertItem key={idx} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {warningAlerts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2>Warnings</h2>
            <span className="badge warning">{warningAlerts.length}</span>
          </div>
          <div className="alerts-list full">
            {warningAlerts.map((alert, idx) => (
              <AlertItem key={idx} alert={alert} />
            ))}
          </div>
        </div>
      )}

      {alerts.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <p>No alerts</p>
            <p className="empty-subtitle">All inventory levels are within acceptable ranges</p>
          </div>
        </div>
      )}
    </div>
  );
}

// ==================== MAIN APP ====================

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [kpis, setKpis] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [forecasts, setForecasts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simDays, setSimDays] = useState(7);
  const [simulating, setSimulating] = useState(false);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setError(null);
      const [kpiData, invData, alertData, histData, suppData, forecastData, orderData] = await Promise.all([
        api.getKPIs(),
        api.getInventory(null, filter || null),
        api.getAlerts(),
        api.getHistory(),
        api.getSuppliers(),
        api.getForecasts().catch(() => ({ forecasts: [] })),
        api.getOrders().catch(() => ({ orders: [] }))
      ]);
      setKpis(kpiData);
      setInventory(invData.items || []);
      setAlerts(alertData || []);
      setHistory(histData.history || []);
      setSuppliers(suppData.suppliers || []);
      setForecasts(forecastData.forecasts || []);
      setOrders(orderData.orders || []);
      setLoading(false);
    } catch (err) {
      setError('Failed to connect to backend. Make sure the API is running on port 8001.');
      setLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        await api.initialize();
        await loadData();
      } catch (err) {
        setError('Failed to initialize. Make sure the backend is running.');
        setLoading(false);
      }
    };
    init();
  }, []);

  useEffect(() => {
    if (!loading) loadData();
  }, [filter]);

  const runSimulation = async () => {
    setSimulating(true);
    try {
      await api.runSimulation(simDays);
      await loadData();
    } catch (err) {
      setError('Simulation failed');
    }
    setSimulating(false);
  };

  const resetSystem = async () => {
    setLoading(true);
    await api.reset();
    await api.initialize();
    await loadData();
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <p>Loading Inventory System...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage kpis={kpis} alerts={alerts} history={history} formatCurrency={formatCurrency} />;
      case 'inventory':
        return <InventoryPage inventory={inventory} filter={filter} setFilter={setFilter} formatCurrency={formatCurrency} />;
      case 'orders':
        return <OrdersPage kpis={kpis} orders={orders} />;
      case 'suppliers':
        return <SuppliersPage suppliers={suppliers} />;
      case 'warehouses':
        return <WarehousesPage warehouses={{}} inventory={inventory} />;
      case 'forecasts':
        return <ForecastsPage forecasts={forecasts} />;
      case 'alerts':
        return <AlertsPage alerts={alerts} />;
      default:
        return <DashboardPage kpis={kpis} alerts={alerts} history={history} formatCurrency={formatCurrency} />;
    }
  };

  return (
    <div className="app-container">
      <header className="top-header">
        <div className="logo">
          <span className="logo-text">Inventory Optimizer</span>
        </div>
        <div className="header-controls">
          <div className="sim-control">
            <label>Simulate</label>
            <input
              type="number"
              value={simDays}
              onChange={(e) => setSimDays(Number(e.target.value))}
              min="1"
              max="365"
              className="days-input"
            />
            <span className="days-label">days</span>
          </div>
          <button onClick={runSimulation} disabled={simulating} className="btn primary">
            {simulating ? 'Running...' : 'Run'}
          </button>
          <button onClick={resetSystem} className="btn secondary">Reset</button>
        </div>
      </header>

      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} alerts={alerts} />

      <main className="main-content">
        {renderPage()}
      </main>

      <footer className="footer">
        Multi-Agent Inventory Optimization System | {kpis?.total_warehouses || 0} Warehouses | {kpis?.total_suppliers || 0} Suppliers
      </footer>
    </div>
  );
}

export default App;
