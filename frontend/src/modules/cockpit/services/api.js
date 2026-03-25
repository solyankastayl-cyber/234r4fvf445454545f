// Cockpit API Service
const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export const CockpitAPI = {
  // Dashboard / Overview
  async getDashboardState(symbol = 'BTC') {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/state/${symbol}`);
    return res.json();
  },

  async getDashboardMulti() {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/multi`);
    return res.json();
  },

  async getPortfolioSummary() {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/portfolio`);
    return res.json();
  },

  async getRiskSummary() {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/risk`);
    return res.json();
  },

  async getAlerts() {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/alerts`);
    return res.json();
  },

  // Chart / Research
  async getChartFullAnalysis(symbol, timeframe) {
    const res = await fetch(`${API_BASE}/api/v1/chart/full-analysis/${symbol}/${timeframe}`);
    return res.json();
  },

  async getResearchPayload() {
    const res = await fetch(`${API_BASE}/api/v1/research-analytics/full-payload`);
    return res.json();
  },

  async getSignalExplanation(signalId) {
    const res = await fetch(`${API_BASE}/api/v1/signal/explanation/${signalId}`);
    return res.json();
  },

  // Market Regime
  async getMarketRegime() {
    const res = await fetch(`${API_BASE}/api/v1/research/regime`);
    return res.json();
  },

  // Capital Flow
  async getCapitalFlowSummary() {
    const res = await fetch(`${API_BASE}/api/v1/capital-flow/summary`);
    return res.json();
  },

  // Fractal
  async getFractalMatches(symbol) {
    const res = await fetch(`${API_BASE}/api/v1/fractal/matches/${symbol}`);
    return res.json();
  },

  // Microstructure
  async getMicrostructureState(symbol) {
    const res = await fetch(`${API_BASE}/api/v1/microstructure/state/${symbol}`);
    return res.json();
  },

  // Hypotheses
  async getHypothesisList() {
    const res = await fetch(`${API_BASE}/api/v1/hypothesis/list`);
    return res.json();
  },

  // Execution
  async getApprovalPending() {
    const res = await fetch(`${API_BASE}/api/v1/execution/approval/pending`);
    return res.json();
  },

  async approveExecution(orderId) {
    const res = await fetch(`${API_BASE}/api/v1/execution/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId })
    });
    return res.json();
  },

  async rejectExecution(orderId, reason) {
    const res = await fetch(`${API_BASE}/api/v1/execution/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order_id: orderId, reason })
    });
    return res.json();
  },

  async getExecutionDetail(orderId) {
    const res = await fetch(`${API_BASE}/api/v1/execution/detail/${orderId}`);
    return res.json();
  },

  async getActiveOrders() {
    const res = await fetch(`${API_BASE}/api/v1/execution/active`);
    return res.json();
  },

  async getFills() {
    const res = await fetch(`${API_BASE}/api/v1/execution/fills`);
    return res.json();
  },

  // Portfolio
  async getPortfolioState() {
    const res = await fetch(`${API_BASE}/api/v1/portfolio/state`);
    return res.json();
  },

  // Risk
  async getRiskState() {
    const res = await fetch(`${API_BASE}/api/v1/risk/state`);
    return res.json();
  },

  async getRiskBudgetSummary() {
    const res = await fetch(`${API_BASE}/api/v1/risk-budget/summary`);
    return res.json();
  },

  // System
  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/api/v1/system/status/dashboard`);
    return res.json();
  },

  async getValidationReport() {
    const res = await fetch(`${API_BASE}/api/v1/system/validation/report`);
    return res.json();
  },

  // TA Engine (existing)
  async getTARegistry() {
    const res = await fetch(`${API_BASE}/api/ta/registry`);
    return res.json();
  },

  async getTAPatterns() {
    const res = await fetch(`${API_BASE}/api/ta/patterns`);
    return res.json();
  },

  async analyzeTechnical(symbol, timeframe) {
    const res = await fetch(`${API_BASE}/api/ta/analyze?symbol=${symbol}&timeframe=${timeframe}`, {
      method: 'POST'
    });
    return res.json();
  }
};

export default CockpitAPI;
