// src/services/commissionService.js
//
// Wraps /api/sales/commissions* backend calls.

import { api } from './api';

export const commissionService = {
  getCommissions: (status) =>
    api.get(`/api/sales/commissions${status ? `?status=${encodeURIComponent(status)}` : ''}`),

  getSummary: () =>
    api.get('/api/sales/commissions/summary'),

  getRankings: () =>
    api.get('/api/sales/commissions/rankings'),

  approveMilestone: (commissionId, milestoneId, comments) =>
    api.put(`/api/sales/commissions/${commissionId}/approve-milestone`, {
      milestone_id: milestoneId,
      comments: comments || null
    }),

  reverseMilestone: (commissionId, milestoneId) =>
    api.put(`/api/sales/commissions/${commissionId}/reverse-milestone?milestone_id=${encodeURIComponent(milestoneId)}`),
};