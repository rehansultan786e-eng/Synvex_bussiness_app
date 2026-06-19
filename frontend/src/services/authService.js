// src/services/authService.js
//
// Unified login: all roles (including employee) use email + password
// via /api/auth/login. The separate employee_id login has been removed.

import { api } from './api';

export const authService = {
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }, { auth: false }),

  verify2FA: (temp_token, otp) =>
    api.post('/api/auth/verify-2fa', { temp_token, otp }, { auth: false }),

  resend2FA: (temp_token) =>
    api.post('/api/auth/resend-2fa', { temp_token }, { auth: false }),

  getMe: () => api.get('/api/auth/me'),

  setPassword: (token, password) =>
    api.post('/api/auth/set-password', { token, password }, { auth: false }),

  forgotPassword: (email) =>
    api.post('/api/auth/forgot-password', { email }, { auth: false }),

  resetPassword: (token, new_password) =>
    api.post('/api/auth/reset-password', { token, new_password }, { auth: false }),

  inviteUser: (fullName, email, role) =>
    api.post('/api/auth/invite-user', { full_name: fullName, email: email, role: role }),

  getManagersAndReps: () =>
    api.get('/api/auth/users'),

  setPasswordViaInvite: (token, password) =>
    api.post('/api/auth/set-password', { token, password }),
};