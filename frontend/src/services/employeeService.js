// src/services/employeeService.js
//
// Wraps /api/employees/*, /api/departments/*, /api/attendance/*,
// /api/leaves/*, and /api/assets/* (employee-scoped) backend calls.

import { api } from './api';

export const employeeService = {
  getEmployees: (department, status, search) => {
    const params = new URLSearchParams();
    if (department) params.append('department', department);
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    const qs = params.toString();
    return api.get('/api/employees/' + (qs ? '?' + qs : ''));
  },

  getEmployee: (employeeId) =>
    api.get('/api/employees/' + employeeId),

  createEmployee: (data) =>
    api.post('/api/employees/', data),

  updateEmployee: (employeeId, data) =>
    api.put('/api/employees/' + employeeId, data),

  deleteEmployee: (employeeId) =>
    api.delete('/api/employees/' + employeeId),

  getDepartments: () =>
    api.get('/api/departments/'),

  createDepartment: (data) =>
    api.post('/api/departments/', data),

  // History tab data (used by EmployeeProfile)
  getAttendanceHistory: (employeeId, month, year) => {
    const params = new URLSearchParams();
    if (month) params.append('month', month);
    if (year) params.append('year', year);
    const qs = params.toString();
    return api.get('/api/attendance/employee/' + employeeId + (qs ? '?' + qs : ''));
  },

  getAttendanceSummary: (employeeId, month, year) =>
    api.get('/api/attendance/employee/' + employeeId + '/summary?month=' + month + '&year=' + year),

  getEmployeeLeaves: (employeeId) =>
    api.get('/api/leaves/employee/' + employeeId),

  getLeaveBalance: (employeeId, year) =>
    api.get('/api/leaves/balance/' + employeeId + (year ? '?year=' + year : '')),

  getEmployeeAssets: (employeeId) =>
    api.get('/api/assets/?assigned_to=' + encodeURIComponent(employeeId)),
};