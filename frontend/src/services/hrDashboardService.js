// src/services/hrDashboardService.js
//
// Combines /api/attendance/*, /api/leaves/*, /api/assets/* calls
// needed for the HR Manager Dashboard widgets.

import { api } from './api';

export const hrDashboardService = {
  getActiveEmployeeCount: () =>
    api.get('/api/employees/?status=active'),

  getTodayAttendance: () =>
    api.get('/api/attendance/today'),

  getPendingLeaves: () =>
    api.get('/api/leaves/?status=Pending'),

  getWarrantyExpiring: () =>
    api.get('/api/assets/warranty-expiring?days=30'),
};