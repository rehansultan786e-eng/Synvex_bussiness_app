import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Clock, CalendarDays, AlertTriangle, Loader2 } from 'lucide-react';
import { hrDashboardService } from '../../services/hrDashboardService';
import { useAuth } from '../../context/AuthContext';

const KpiCard = ({ label, value, icon, sublabel, onClick }) => (
  <div
    onClick={onClick}
    className={
      'bg-white rounded-card shadow-soft border border-gray-100 p-4' +
      (onClick ? ' cursor-pointer hover:shadow-elevated hover:border-primary-light transition-all' : '')
    }
  >
    <div className="flex items-center justify-between">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      {icon}
    </div>
    <p className="text-xl font-semibold text-gray-900 mt-2">{value}</p>
    {sublabel && <p className="text-xs text-gray-400 mt-1">{sublabel}</p>}
    <div className="h-1 w-10 bg-primary rounded-full mt-3"></div>
  </div>
);

const ModuleLink = ({ label, description, onClick }) => (
  <button
    onClick={onClick}
    className="text-left bg-white rounded-card shadow-soft border border-gray-100 p-4 hover:shadow-elevated hover:border-primary-light transition-all"
  >
    <p className="text-sm font-semibold text-gray-800">{label}</p>
    <p className="text-xs text-gray-500 mt-1">{description}</p>
  </button>
);

const HrManagerDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeCount, setActiveCount] = useState(0);
  const [todayAttendance, setTodayAttendance] = useState([]);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [warrantyAlerts, setWarrantyAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [empRes, attRes, leaveRes, warrantyRes] = await Promise.allSettled([
          hrDashboardService.getActiveEmployeeCount(),
          hrDashboardService.getTodayAttendance(),
          hrDashboardService.getPendingLeaves(),
          hrDashboardService.getWarrantyExpiring()
        ]);

        if (empRes.status === 'fulfilled') {
          setActiveCount((empRes.value.data || []).length);
        }
        if (attRes.status === 'fulfilled') {
          setTodayAttendance(attRes.value.data || []);
        }
        if (leaveRes.status === 'fulfilled') {
          setPendingLeaves(leaveRes.value.data || []);
        }
        if (warrantyRes.status === 'fulfilled') {
          setWarrantyAlerts(warrantyRes.value.data || []);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const presentToday = todayAttendance.filter((r) => r.status === 'Present' || r.status === 'Late').length;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">
          Welcome back, {user ? user.full_name : ''}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">HR overview and quick actions</p>
      </div>

      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      )}

      {!loading && (
        <div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <KpiCard
              label="Active Employees"
              value={activeCount}
              icon={<Users className="w-4 h-4 text-primary-light" />}
              onClick={() => navigate('/employees')}
            />
            <KpiCard
              label="Present Today"
              value={presentToday + ' / ' + todayAttendance.length}
              icon={<Clock className="w-4 h-4 text-green-500" />}
              onClick={() => navigate('/attendance')}
            />
            <KpiCard
              label="Pending Leave Requests"
              value={pendingLeaves.length}
              icon={<CalendarDays className="w-4 h-4 text-amber-400" />}
              onClick={() => navigate('/leave')}
            />
            <KpiCard
              label="Warranty Expiring Soon"
              value={warrantyAlerts.length}
              sublabel="Within 30 days"
              icon={<AlertTriangle className="w-4 h-4 text-red-500" />}
              onClick={() => navigate('/assets')}
            />
          </div>

          <h2 className="text-sm font-semibold text-gray-700 mb-3">HR Modules</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <ModuleLink
              label="Employees"
              description="Directory, onboarding, profiles"
              onClick={() => navigate('/employees')}
            />
            <ModuleLink
              label="Attendance"
              description="Daily register, manual override, reports"
              onClick={() => navigate('/attendance')}
            />
            <ModuleLink
              label="Leave Management"
              description="Approve or reject leave requests"
              onClick={() => navigate('/leave')}
            />
            <ModuleLink
              label="Assets"
              description="Inventory, assignment, warranty"
              onClick={() => navigate('/assets')}
            />
            <ModuleLink
              label="Performance"
              description="Review cycles, KPIs, ratings"
              onClick={() => navigate('/performance')}
            />
            <ModuleLink
              label="Payroll"
              description="Salary structures, payroll runs"
              onClick={() => navigate('/payroll')}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default HrManagerDashboard;