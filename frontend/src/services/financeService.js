// src/services/financeService.js
//
// Wraps /api/finance/* and /api/sales/reps backend calls.

import { api } from './api';

export const financeService = {
  // Contracts
  getContracts: (clientName) =>
    api.get(`/api/finance/contracts${clientName ? `?client_name=${encodeURIComponent(clientName)}` : ''}`),

  getContract: (contractId) =>
    api.get(`/api/finance/contracts/${contractId}`),

  createContract: (data) =>
    api.post('/api/finance/contracts', data),

  updateContract: (contractId, data) =>
    api.put(`/api/finance/contracts/${contractId}`, data),

  deleteContract: (contractId) =>
    api.delete(`/api/finance/contracts/${contractId}`),

  // Milestones
  addMilestone: (contractId, data) =>
    api.post(`/api/finance/contracts/${contractId}/milestones`, data),

  updateMilestone: (contractId, milestoneId, data) =>
    api.put(`/api/finance/contracts/${contractId}/milestones/${milestoneId}`, data),

  markMilestoneReceived: (contractId, milestoneId, data) =>
    api.put(`/api/finance/contracts/${contractId}/milestones/${milestoneId}/mark-received`, data),

  getOverdueMilestones: () =>
    api.get('/api/finance/milestones/overdue'),

  getUpcomingMilestones: (days = 7) =>
    api.get(`/api/finance/milestones/upcoming?days=${days}`),

  // Invoices
  generateInvoice: (contractId, milestoneId) =>
    api.post('/api/finance/invoices/generate', { contract_id: contractId, milestone_id: milestoneId }),

  // Sales reps lookup (for assigning a rep to a contract)
  getSalesReps: () =>
    api.get('/api/sales/reps'),
};