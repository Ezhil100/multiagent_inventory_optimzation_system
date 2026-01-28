import { useState, useEffect } from 'react';
import { api } from './api';
import './App.css';

// KPI Card Component
function KPICard({ title, value, subtitle, color = '#4a90d9' }) {
  return (
    <div className="kpi-card" style={{ borderTop: `4px solid ${color}` }}>
      <div className="kpi-title">{title}</div>
      <div className="kpi-value">{value}</div>
      {subtitle && <div className="kpi-subtitle">{subtitle}</div>}
    </div>
  );
}

// Alert Item Component
function AlertItem({ alert }) {
  const bgColor = alert.level === 'critical' ? '#fee2e2' : '#fef3c7';
  const textColor = alert.level === 'critical' ? '#dc2626' : '#d97706';

  return (
    <div className="alert-item" style={{ backgroundColor: bgColor, borderLeft: `4px solid ${textColor}` }}>
      <div className="alert-header">
        <span className="alert-level" style={{ color: textColor }}>
          {alert.level === 'critical' ? '⚠ CRITICAL' : '⚡ WARNING'}
        </span>
        <span className="alert-warehouse">{alert.warehouse}</span>
      </div>
      <div className="alert-message">{alert.message}</div>
    </div>
  );
}

// Inventory Table Component
function InventoryTable({ items, filter, setFilter }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'OK': return '#22c55e';
      case 'REORDER': return '#eab308';
      case 'CRITICAL': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="inventory-section">
      <div className="section-header">
        <h2>Inventory Status</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} className="filter-select">
          <option value="">All Status</option>
          <option value="OK">OK</option>
          <option value="REORDER">Reorder</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>
      <div className="table-container">
        <table className="inventory-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Warehouse</th>
              <th>Stock</th>
              <th>ROP</th>
              <th>Safety</th>
              <th>EOQ</th>
              <th>Days Supply</th>
              <th>Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, idx) => (
              <tr key={idx}>
                <td><strong>{item.product_name}</strong><br /><small>{item.product_id}</small></td>
                <td>{item.warehouse_name}</td>
                <td>{item.current_stock}</td>
                <td>{item.reorder_point}</td>
                <td>{item.safety_stock}</td>
                <td>{item.eoq}</td>
                <td>{item.days_of_supply?.toFixed(1)}</td>
                <td>${item.stock_value?.toLocaleString()}</td>
                <td>
                  <span className="status-badge" style={{ backgroundColor: getStatusColor(item.status) }}>
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
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
        <h1>📦 Inventory Optimization Dashboard</h1>
        <div className="header-actions">
          <span className="sim-days">
            Days:
            <input
              type="number"
              value={simDays}
              onChange={(e) => setSimDays(Number(e.target.value))}
              min="1"
              max="365"
            />
          </span>
          <button onClick={runSimulation} disabled={simulating} className="btn-primary">
            {simulating ? 'Running...' : '▶ Run Simulation'}
          </button>
          <button onClick={resetSystem} className="btn-secondary">↻ Reset</button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KPICard
          title="Total Inventory Value"
          value={`$${kpis?.total_inventory_value?.toLocaleString() || 0}`}
          subtitle={`${kpis?.total_products || 0} products`}
          color="#3b82f6"
        />
        <KPICard
          title="Service Level"
          value={`${kpis?.average_service_level?.toFixed(1) || 0}%`}
          subtitle={`${kpis?.simulation_days || 0} days simulated`}
          color="#22c55e"
        />
        <KPICard
          title="Total Orders"
          value={kpis?.total_orders_placed || 0}
          subtitle={`${kpis?.total_units_fulfilled || 0} units fulfilled`}
          color="#8b5cf6"
        />
        <KPICard
          title="Total Cost"
          value={`$${kpis?.total_cost?.toLocaleString() || 0}`}
          subtitle={`Holding: $${kpis?.total_holding_cost?.toFixed(0) || 0} | Order: $${kpis?.total_ordering_cost?.toFixed(0) || 0}`}
          color="#f59e0b"
        />
      </div>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="alerts-section">
          <h2>
            Alerts
            <span className="alert-counts">
              {criticalCount > 0 && <span className="critical-count">{criticalCount} critical</span>}
              {warningCount > 0 && <span className="warning-count">{warningCount} warnings</span>}
            </span>
          </h2>
          <div className="alerts-grid">
            {alerts.slice(0, 6).map((alert, idx) => (
              <AlertItem key={idx} alert={alert} />
            ))}
          </div>
          {alerts.length > 6 && (
            <p className="more-alerts">+ {alerts.length - 6} more alerts</p>
          )}
        </div>
      )}

      {/* Inventory Table */}
      <InventoryTable items={inventory} filter={filter} setFilter={setFilter} />

      {/* History Chart (Simple) */}
      {history.length > 0 && (
        <div className="history-section">
          <h2>Simulation History ({history.length} days)</h2>
          <div className="history-stats">
            <div className="stat">
              <span>Start Value:</span>
              <strong>${history[0]?.total_inventory_value?.toLocaleString()}</strong>
            </div>
            <div className="stat">
              <span>End Value:</span>
              <strong>${history[history.length - 1]?.total_inventory_value?.toLocaleString()}</strong>
            </div>
            <div className="stat">
              <span>Avg Service Level:</span>
              <strong>{(history.reduce((a, b) => a + b.service_level, 0) / history.length).toFixed(1)}%</strong>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer">
        <p>Multi-Agent Inventory Optimization System | {kpis?.total_warehouses || 0} Warehouses | {kpis?.total_suppliers || 0} Suppliers</p>
      </footer>
    </div>
  );
}

export default App
