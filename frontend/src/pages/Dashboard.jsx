import React from 'react';
import { useAuth } from '../context/AuthContext';
import SuperAdminDashboard from './dashboards/SuperAdminDashboard';
import HrManagerDashboard from './dashboards/HrManagerDashboard';

const GenericDashboard = () => {
  const { user } = useAuth();
  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900">
        Welcome back, {user ? user.full_name : ''}
      </h1>
      <p className="text-sm text-gray-500 mt-0.5">
        Logged in as {user ? user.role : ''}
      </p>
      <div className="bg-white rounded-card shadow-soft border border-gray-100 p-5 mt-6">
        <p className="text-sm text-gray-500">
          This is a placeholder dashboard. Role-specific widgets, charts, and pending-action panels will be added in upcoming steps.
        </p>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  if (user.role === 'super_admin') {
    return <SuperAdminDashboard />;
  }

  
   if (user.role === 'hr_manager') {
    return <HrManagerDashboard />;
  }

  return <GenericDashboard />;
};

export default Dashboard;