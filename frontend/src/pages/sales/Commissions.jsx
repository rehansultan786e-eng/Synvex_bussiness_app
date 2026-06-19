import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, Clock, CheckCircle2, Loader2 } from 'lucide-react';
import { commissionService } from '../../services/commissionService';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/StatusBadge';

const formatMoney = (value) => {
  return Number(value || 0).toLocaleString();
};

const SummaryCard = ({ label, value, icon }) => (
  <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
    <div className="flex items-center justify-between">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      {icon}
    </div>
    <p className="text-xl font-semibold text-gray-900 mt-2">{formatMoney(value)}</p>
    <div className="h-1 w-10 bg-primary rounded-full mt-3"></div>
  </div>
);

const Commissions = () => {
  const { user } = useAuth();
  const isManagerView = user && (user.role === 'super_admin' || user.role === 'sales_manager');

  const [summary, setSummary] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [commissions, setCommissions] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionError, setActionError] = useState('');
  const [busyKey, setBusyKey] = useState('');

  const loadAll = async () => {
    setLoading(true);
    setError('');
    try {
      const summaryRes = await commissionService.getSummary();
      setSummary(summaryRes.data);

      const commissionsRes = await commissionService.getCommissions(statusFilter || undefined);
      setCommissions(commissionsRes.data || []);

      if (isManagerView) {
        const rankingsRes = await commissionService.getRankings();
        setRankings(rankingsRes.data || []);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleApprove = async (commissionId, milestoneId) => {
    const key = commissionId + '-' + milestoneId;
    setBusyKey(key);
    setActionError('');
    try {
      await commissionService.approveMilestone(commissionId, milestoneId);
      await loadAll();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyKey('');
    }
  };

  const handleReverse = async (commissionId, milestoneId) => {
    const key = commissionId + '-' + milestoneId + '-reverse';
    setBusyKey(key);
    setActionError('');
    try {
      await commissionService.reverseMilestone(commissionId, milestoneId);
      await loadAll();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyKey('');
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Commissions</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          {isManagerView ? 'Team commission tracking and milestone approvals' : 'Your commission earnings'}
        </p>
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
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <SummaryCard label="Pending" value={summary.total_pending} icon={<Clock className="w-4 h-4 text-amber-400" />} />
          <SummaryCard label="Approved" value={summary.total_approved} icon={<CheckCircle2 className="w-4 h-4 text-blue-400" />} />
          <SummaryCard label="Paid" value={summary.total_paid} icon={<DollarSign className="w-4 h-4 text-green-500" />} />
          <SummaryCard label="Total Liability" value={summary.total_liability} icon={<TrendingUp className="w-4 h-4 text-primary-light" />} />
        </div>
      )}

      {!loading && isManagerView && rankings.length > 0 && (
        <div className="bg-white rounded-card shadow-soft border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-4">Rep Rankings</h2>
          <div className="space-y-3">
            {rankings.map((r, index) => (
              <div key={r.sales_rep_id} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 flex items-center justify-center rounded-full bg-surface-subtle text-xs font-medium text-gray-500">
                    {index + 1}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-gray-800">{r.sales_rep_name}</p>
                    <p className="text-xs text-gray-400">{r.deal_count} deals</p>
                  </div>
                </div>
                <p className="text-sm font-semibold text-gray-800">{formatMoney(r.total_calculated)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && (
        <div className="bg-white rounded-card shadow-soft border border-gray-100 p-5">
          <div className="flex items-center justify-between mb-4 gap-3">
            <h2 className="text-sm font-semibold text-gray-800">Commission Ledger</h2>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-control border border-gray-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-light"
            >
              <option value="">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Paid">Paid</option>
              <option value="Cancelled">Cancelled</option>
              <option value="Reversed">Reversed</option>
            </select>
          </div>

          {actionError && (
            <div className="mb-3 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
              {actionError}
            </div>
          )}

          {commissions.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-10">No commission records found.</p>
          )}

          <div className="space-y-4">
            {commissions.map((c) => (
              <div key={c.id} className="border border-gray-100 rounded-control p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{c.sales_rep_name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Lead {c.lead_id} &middot; Rate {c.rate}% &middot; Total {formatMoney(c.total_commission_calculated)}
                    </p>
                  </div>
                  <StatusBadge status={c.overall_status} />
                </div>

                {c.milestone_payouts && c.milestone_payouts.length > 0 && (
                  <div className="space-y-2 mt-3">
                    {c.milestone_payouts.map((mp) => {
                      const approveKey = c.commission_id + '-' + mp.milestone_id;
                      const reverseKey = approveKey + '-reverse';
                      return (
                        <div
                          key={mp.milestone_id}
                          className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-surface-subtle rounded-control px-3 py-2.5"
                        >
                          <div className="flex items-center gap-3">
                            <StatusBadge status={mp.status} />
                            <span className="text-xs text-gray-600">
                              Milestone {mp.milestone_id} &middot; Share {formatMoney(mp.commission_share)}
                            </span>
                          </div>

                          {isManagerView && mp.status === 'Pending' && (
                            <button
                              onClick={() => handleApprove(c.commission_id, mp.milestone_id)}
                              disabled={busyKey === approveKey}
                              className="self-start sm:self-auto text-xs font-medium text-primary-light hover:underline disabled:opacity-50"
                            >
                              {busyKey === approveKey ? 'Approving...' : 'Approve'}
                            </button>
                          )}

                          {isManagerView && (mp.status === 'Approved' || mp.status === 'Paid') && (
                            <button
                              onClick={() => handleReverse(c.commission_id, mp.milestone_id)}
                              disabled={busyKey === reverseKey}
                              className="self-start sm:self-auto text-xs font-medium text-red-500 hover:underline disabled:opacity-50"
                            >
                              {busyKey === reverseKey ? 'Reversing...' : 'Reverse'}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Commissions;