// src/App.js
//
// Root routing. Public routes (login) are outside ProtectedRoute.
// All other routes are wrapped in ProtectedRoute, which checks auth
// state and (optionally) role before rendering MainLayout's children.
// Modules not yet built use the shared ComingSoon placeholder so
// sidebar links never produce a blank/broken page.

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import MainLayout from './layouts/MainLayout';
import Login from './pages/auth/Login';
import Unauthorized from './pages/Unauthorized';
import Dashboard from './pages/Dashboard';
import Contracts from './pages/finance/Contracts';
import ComingSoon from './pages/common/ComingSoon';
import Commissions from './pages/sales/Commissions';
import Employees from './pages/hr/Employees';
import ForgotPassword from './pages/auth/ForgotPassword';
import ResetPassword from './pages/auth/ResetPassword';
import EmployeeProfile from './pages/hr/EmployeeProfile';
import SetPassword from './pages/auth/SetPassword';


function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/unauthorized" element={<Unauthorized />} />

          {/* Protected routes — any authenticated user (no role restriction) */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="contracts" element={<Contracts />} />
              <Route path="/set-password" element={<SetPassword />} />

              {/* Placeholder routes for modules not yet built */}
              <Route path="sales" element={<ComingSoon title="Sales & Leads" />} />
              <Route path="commissions" element={<Commissions />} />
              <Route path="expenses" element={<ComingSoon title="Expenses" />} />
              <Route path="payroll" element={<ComingSoon title="Payroll" />} />
              <Route path="employees" element={<Employees />} />
              <Route path="employees/:employeeId" element={<EmployeeProfile />} />
              <Route path="attendance" element={<ComingSoon title="Attendance" />} />
              <Route path="leave" element={<ComingSoon title="Leave" />} />
              <Route path="assets" element={<ComingSoon title="Assets" />} />
              <Route path="performance" element={<ComingSoon title="Performance" />} />
              <Route path="reports" element={<ComingSoon title="Reports & Analytics" />} />
              <Route path="audit-logs" element={<ComingSoon title="Audit Logs" />} />
              <Route path="self-service" element={<ComingSoon title="My Self-Service" />} />
              <Route path="settings" element={<ComingSoon title="Settings" />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;