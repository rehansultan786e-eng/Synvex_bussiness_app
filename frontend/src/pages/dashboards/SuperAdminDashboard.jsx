import React, { useState, useEffect } from 'react';
import { DollarSign, Users, AlertCircle, TrendingUp, Loader2, Package } from 'lucide-react';
import { reportsService } from '../../services/reportsService';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const formatMoney = (value) => {
  return Number(value || 0).toLocaleString();
};

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

const SuperAdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await reportsService.getExecutiveDashboard();
        setSummary(res.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">
          Welcome back, {user ? user.full_name : ''}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">Company-wide overview</p>
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

      {!loading && summary && (
        <div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
           <KpiCard
              label="Revenue Received"
              value={formatMoney(summary.revenue.total_received)}
              sublabel={summary.revenue.collection_rate + '% collected'}
              icon={<DollarSign className="w-4 h-4 text-green-500" />}
              onClick={() => navigate('/contracts')}
            />
            <KpiCard
              label="Active Employees"
              value={summary.headcount}
              icon={<Users className="w-4 h-4 text-primary-light" />}
              onClick={() => navigate('/employees')}
            />
            <KpiCard
              label="Pending Expenses"
              value={summary.pending_expenses_count}
              icon={<AlertCircle className="w-4 h-4 text-amber-400" />}
              onClick={() => navigate('/expenses')}
            />
            <KpiCard
              label="Open Leads"
              value={summary.leads.open}
              sublabel={summary.leads.won + ' won'}
              icon={<TrendingUp className="w-4 h-4 text-blue-400" />}
              onClick={() => navigate('/sales')}
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <KpiCard
              label="Pending Receivables"
              value={formatMoney(summary.revenue.total_pending)}
              icon={<DollarSign className="w-4 h-4 text-gray-400" />}
              onClick={() => navigate('/contracts')}
            />
            <KpiCard
              label="Overdue Receivables"
              value={formatMoney(summary.revenue.total_overdue)}
              icon={<AlertCircle className="w-4 h-4 text-red-500" />}
              onClick={() => navigate('/contracts')}
            />
            <KpiCard
              label="Commission Liability"
              value={formatMoney(summary.pending_commission_liability)}
              icon={<DollarSign className="w-4 h-4 text-amber-400" />}
              onClick={() => navigate('/commissions')}
            />
            <KpiCard
              label="Total Assets"
              value={summary.total_assets}
              icon={<Package className="w-4 h-4 text-gray-400" />}
              onClick={() => navigate('/assets')}
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            <KpiCard
              label="Pending Receivables"
              value={formatMoney(summary.revenue.total_pending)}
              icon={<DollarSign className="w-4 h-4 text-gray-400" />}
            />
            <KpiCard
              label="Overdue Receivables"
              value={formatMoney(summary.revenue.total_overdue)}
              icon={<AlertCircle className="w-4 h-4 text-red-500" />}
            />
            <KpiCard
              label="Commission Liability"
              value={formatMoney(summary.pending_commission_liability)}
              icon={<DollarSign className="w-4 h-4 text-amber-400" />}
            />
            <KpiCard
              label="Total Assets"
              value={summary.total_assets}
              icon={<Package className="w-4 h-4 text-gray-400" />}
            />
          </div>

          {summary.pending_payroll_batches > 0 && (
            <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
              <p className="text-sm text-gray-700">
                {summary.pending_payroll_batches} payroll batch(es) awaiting review or approval.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SuperAdminDashboard;