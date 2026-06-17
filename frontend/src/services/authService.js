// src/services/authService.js
//
// Wraps all /api/auth/* backend calls used by the login/2FA/invite flows.

import { api } from './api';

export const authService = {
  // Manager-role login (super_admin, hr_manager, finance_manager, sales_manager, sales_rep)
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }, { auth: false }),

  // Completes login for 2FA-required roles (super_admin, finance_manager)
  verify2FA: (temp_token, otp) =>
    api.post('/api/auth/verify-2fa', { temp_token, otp }, { auth: false }),

  resend2FA: (temp_token) =>
    api.post('/api/auth/resend-2fa', { temp_token }, { auth: false }),

  // Employee login (uses employee_id, not email)
  employeeLogin: (employee_id, password) =>
    api.post('/api/auth/employee-login', { employee_id, password }, { auth: false }),

  getMe: () => api.get('/api/auth/me'),

  setPassword: (token, password) =>
    api.post('/api/auth/set-password', { token, password }, { auth: false }),

  forgotPassword: (email) =>
    api.post('/api/auth/forgot-password', { email }, { auth: false }),

  resetPassword: (token, new_password) =>
    api.post('/api/auth/reset-password', { token, new_password }, { auth: false }),
};