// src/services/reportsService.js
//
// Wraps /api/reports/* backend calls (CEO Executive Dashboard + Finance reports).

import { api } from './api';

export const reportsService = {
  getExecutiveDashboard: () =>
    api.get('/api/reports/dashboard'),

  getRevenueOverview: () =>
    api.get('/api/reports/revenue'),

  getProfitLoss: (month, year) => {
    const params = new URLSearchParams();
    if (month) params.append('month', month);
    if (year) params.append('year', year);
    const qs = params.toString();
    return api.get('/api/reports/profit-loss' + (qs ? '?' + qs : ''));
  },

  getCashFlow: (month, year) => {
    const params = new URLSearchParams();
    if (month) params.append('month', month);
    if (year) params.append('year', year);
    const qs = params.toString();
    return api.get('/api/reports/cash-flow' + (qs ? '?' + qs : ''));
  },

  getReceivables: () =>
    api.get('/api/reports/receivables'),
};