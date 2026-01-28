/**
 * API service for connecting to FastAPI backend
 */

// Use environment variable for API URL (set in Vercel dashboard for production)
const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

export const api = {
    // Initialize system
    async initialize() {
        const res = await fetch(`${API_BASE}/api/initialize`, { method: 'POST' });
        return res.json();
    },

    // Get KPIs
    async getKPIs() {
        const res = await fetch(`${API_BASE}/api/kpis`);
        return res.json();
    },

    // Get inventory
    async getInventory(warehouseId = null, status = null) {
        let url = `${API_BASE}/api/inventory`;
        const params = new URLSearchParams();
        if (warehouseId) params.append('warehouse_id', warehouseId);
        if (status) params.append('status', status);
        if (params.toString()) url += `?${params.toString()}`;
        const res = await fetch(url);
        return res.json();
    },

    // Get alerts
    async getAlerts() {
        const res = await fetch(`${API_BASE}/api/alerts`);
        return res.json();
    },

    // Get warehouses
    async getWarehouses() {
        const res = await fetch(`${API_BASE}/api/warehouses`);
        return res.json();
    },

    // Get suppliers
    async getSuppliers() {
        const res = await fetch(`${API_BASE}/api/suppliers`);
        return res.json();
    },

    // Get history
    async getHistory() {
        const res = await fetch(`${API_BASE}/api/history`);
        return res.json();
    },

    // Get orders
    async getOrders() {
        const res = await fetch(`${API_BASE}/api/orders`);
        return res.json();
    },

    // Get forecasts
    async getForecasts() {
        const res = await fetch(`${API_BASE}/api/forecasts`);
        return res.json();
    },

    // Run simulation
    async runSimulation(days = 30) {
        const res = await fetch(`${API_BASE}/api/simulation/run?days=${days}`, { method: 'POST' });
        return res.json();
    },

    // Step simulation
    async stepSimulation() {
        const res = await fetch(`${API_BASE}/api/simulation/step`, { method: 'POST' });
        return res.json();
    },

    // Reset system
    async reset() {
        const res = await fetch(`${API_BASE}/api/reset`, { method: 'POST' });
        return res.json();
    },

    // Health check
    async health() {
        const res = await fetch(`${API_BASE}/health`);
        return res.json();
    }
};
