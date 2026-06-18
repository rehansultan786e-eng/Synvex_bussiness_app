// src/pages/Dashboard.jsx
//
// Placeholder dashboard shown right after login. Full role-specific
// Executive/HR/Finance/Sales dashboards will replace this in later steps.
// Updated to the Synvex violet/purple brand palette.

import React from 'react';
import { useAuth } from '../context/AuthContext';

const roleLabels = {
  super_admin: 'CEO',
  hr_manager: 'HR Manager',
  finance_manager: 'Finance Manager',
  sales_manager: 'Sales Manager',
  sales_rep: 'Sales Representative',
  employee: 'Employee',
};

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900">
        Welcome back, {user?.full_name || user?.employee_id}
      </h1>
      <p className="text-sm text-gray-500 mt-1">
        Logged in as {roleLabels[user?.role] || user?.role}
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
        {['Revenue', 'Active Employees', 'Pending Approvals', 'Open Leads'].map((label) => (
          <div key={label} className="bg-white rounded-card shadow-soft border border-gray-100 p-5">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
            <p className="text-2xl font-semibold text-gray-900 mt-2">—</p>
            <div className="mt-3 h-1 w-10 rounded-full bg-primary/20" />
          </div>
        ))}
      </div>

      <div className="mt-6 bg-white rounded-card shadow-soft border border-gray-100 p-5">
        <p className="text-sm text-gray-500">
          This is a placeholder dashboard. Role-specific widgets, charts, and
          pending-action panels will be added in upcoming steps.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;