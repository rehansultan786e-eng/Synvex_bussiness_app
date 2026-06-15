import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
  getMe: () => api.get('/api/auth/me'),
};

export const employeeAPI = {
  getAll: (params?: any) => api.get('/api/employees', { params }),
  getById: (id: string) => api.get(`/api/employees/${id}`),
  create: (data: any) => api.post('/api/employees', data),
  update: (id: string, data: any) => api.put(`/api/employees/${id}`, data),
  delete: (id: string) => api.delete(`/api/employees/${id}`),
  enrollFace: (id: string, images: string[]) =>
    api.post(`/api/employees/${id}/enroll-face`, { images }),
};

export const departmentAPI = {
  getAll: () => api.get('/api/departments'),
  create: (data: any) => api.post('/api/departments', data),
  update: (code: string, data: any) => api.put(`/api/departments/${code}`, data),
  delete: (code: string) => api.delete(`/api/departments/${code}`),
};

export const attendanceAPI = {
  mark: (image_base64: string) =>
    api.post('/api/attendance/mark', { image_base64 }),
  getToday: (department?: string) =>
    api.get('/api/attendance/today', { params: { department } }),
  getByDate: (date: string, department?: string) =>
    api.get(`/api/attendance/date/${date}`, { params: { department } }),
  getEmployeeHistory: (id: string, month?: number, year?: number) =>
    api.get(`/api/attendance/employee/${id}`, { params: { month, year } }),
  correct: (data: any) => api.post('/api/attendance/correct', data),
};

export const leaveAPI = {
  submit: (data: any) => api.post('/api/leaves', data),
  getAll: (status?: string) => api.get('/api/leaves', { params: { status } }),
  getEmployeeLeaves: (id: string) => api.get(`/api/leaves/employee/${id}`),
  updateStatus: (id: string, data: any) => api.put(`/api/leaves/${id}`, data),
};

export const analyticsAPI = {
  getDashboard: () => api.get('/api/analytics/dashboard'),
  getMonthlyTrend: (year: number, month: number) =>
    api.get('/api/analytics/monthly-trend', { params: { year, month } }),
  getDepartmentStats: () => api.get('/api/analytics/department-stats'),
};

export const notificationAPI = {
  getAll: () => api.get('/api/notifications'),
  getUnreadCount: () => api.get('/api/notifications/unread-count'),
  markRead: (id: string) => api.put(`/api/notifications/${id}/read`),
  markAllRead: () => api.put('/api/notifications/mark-all-read'),
};

export default api;