import { useState, useEffect } from 'react';
import { api } from './api';
import './App.css';

// Format currency
const formatCurrency = (value) => {
  if (value === null || value === undefined) return '₹0';
  return '₹' + Number(value).toLocaleString('en-IN');
};

// KPI Card Component
function KPICard({ title, value, subtitle }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value">{value}</div>
      <div className="kpi-title">{title}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
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
        <div className="alert-details">{alert.warehouse} • Stock: {alert.current_stock}</div>
      </div>
    </div>
  );
}

// Inventory Table Component
function InventoryTable({ items, filter, setFilter }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'OK': return 'status-ok';
      case 'REORDER': return 'status-reorder';
      case 'CRITICAL': return 'status-critical';
      default: return '';
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Inventory</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
          <option value="">All</option>
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
              <th>Stock</th>
              <th>ROP</th>
              <th>EOQ</th>
              <th>Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr><td colSpan="7" className="no-data">No inventory data</td></tr>
            ) : (
              items.map((item, idx) => (
                <tr key={idx}>
                  <td className="product-cell">
                    <div className="product-name">{item.product_name}</div>
                    <div className="product-id">{item.product_id}</div>
                  </td>
                  <td>{item.warehouse_name}</td>
                  <td className="number">{item.current_stock || 0}</td>
                  <td className="number">{item.reorder_point || 0}</td>
                  <td className="number">{item.eoq || 0}</td>
                  <td className="number">{formatCurrency(item.stock_value)}</td>
                  <td>
                    <span className={`status-pill ${getStatusClass(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [kpis, setKpis] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simDays, setSimDays] = useState(7);
  const [simulating, setSimulating] = useState(false);
  const [filter, setFilter] = useState('');
  const [error, setError] = useState(null);

  // Load data
  const loadData = async () => {
    try {
      setError(null);
      const [kpiData, invData, alertData, histData] = await Promise.all([
        api.getKPIs(),
        api.getInventory(null, filter || null),
        api.getAlerts(),
        api.getHistory()
      ]);
      setKpis(kpiData);
      setInventory(invData.items || []);
      setAlerts(alertData || []);
      setHistory(histData.history || []);
      setLoading(false);
    } catch (err) {
      setError('Failed to connect to backend. Make sure the API is running on port 8001.');
      setLoading(false);
    }
  };

  // Initialize on mount
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

  // Reload when filter changes
  useEffect(() => {
    if (!loading) loadData();
  }, [filter]);

  // Run simulation
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

  // Reset system
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

  const criticalCount = alerts.filter(a => a.level === 'critical').length;
  const warningCount = alerts.filter(a => a.level === 'warning').length;

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <span className="logo-text">Inventory Optimizer</span>
        </div>
        <div className="header-controls">
          <div className="sim-control">
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
            {simulating ? 'Running...' : 'Simulate'}
          </button>
          <button onClick={resetSystem} className="btn secondary">Reset</button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          title="Inventory Value"
          value={formatCurrency(kpis?.total_inventory_value)}
          subtitle={`${kpis?.total_products || 0} products`}
        />
        <KPICard
          title="Service Level"
          value={`${(kpis?.average_service_level || 0).toFixed(1)}%`}
          subtitle={`${kpis?.simulation_days || 0} days`}
        />
        <KPICard
          title="Orders Placed"
          value={kpis?.total_orders_placed || 0}
          subtitle={`${kpis?.total_units_fulfilled || 0} units`}
        />
        <KPICard
          title="Total Cost"
          value={formatCurrency(kpis?.total_cost)}
          subtitle={`H: ${formatCurrency(kpis?.total_holding_cost)} | O: ${formatCurrency(kpis?.total_ordering_cost)}`}
        />
      </div>

      <div className="main-grid">
        {/* Alerts Panel */}
        <div className="card alerts-card">
          <div className="card-header">
            <h2>Alerts</h2>
            <div className="alert-badges">
              {criticalCount > 0 && <span className="badge critical">{criticalCount}</span>}
              {warningCount > 0 && <span className="badge warning">{warningCount}</span>}
            </div>
          </div>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="no-alerts">No alerts</div>
            ) : (
              alerts.slice(0, 8).map((alert, idx) => (
                <AlertItem key={idx} alert={alert} />
              ))
            )}
          </div>
        </div>

        {/* History Panel */}
        <div className="card history-card">
          <div className="card-header">
            <h2>History</h2>
            <span className="history-days">{history.length} days</span>
          </div>
          {history.length > 0 ? (
            <div className="history-stats">
              <div className="history-stat">
                <div className="stat-label">Start</div>
                <div className="stat-value">{formatCurrency(history[0]?.total_inventory_value)}</div>
              </div>
              <div className="history-stat">
                <div className="stat-label">End</div>
                <div className="stat-value">{formatCurrency(history[history.length - 1]?.total_inventory_value)}</div>
              </div>
              <div className="history-stat">
                <div className="stat-label">Avg SL</div>
                <div className="stat-value">
                  {(history.reduce((a, b) => a + (b.service_level || 0), 0) / history.length).toFixed(1)}%
                </div>
              </div>
            </div>
          ) : (
            <div className="no-history">Run simulation to see history</div>
          )}
        </div>
      </div>

      {/* Inventory Table */}
      <InventoryTable items={inventory} filter={filter} setFilter={setFilter} />

      {/* Footer */}
      <footer className="footer">
        Multi-Agent Inventory System • {kpis?.total_warehouses || 0} Warehouses • {kpis?.total_suppliers || 0} Suppliers
      </footer>
    </div>
  );
}

export default App
