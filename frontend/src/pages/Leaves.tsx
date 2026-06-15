import React, { useState, useEffect } from 'react';
import {
  FileText, CheckCircle, XCircle, Clock,
  Loader2, AlertCircle, Filter, ChevronDown
} from 'lucide-react';
import { leaveAPI } from '../services/api';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-600',
};

const leaveTypeColors: Record<string, string> = {
  'Casual Leave': 'bg-blue-100 text-blue-700',
  'Sick Leave': 'bg-red-100 text-red-600',
  'Annual Leave': 'bg-green-100 text-green-700',
  'Emergency Leave': 'bg-orange-100 text-orange-700',
};

const Leaves: React.FC = () => {
  const [leaves, setLeaves] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => { fetchLeaves(); }, [filterStatus]);

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const res = await leaveAPI.getAll(filterStatus || undefined);
      setLeaves(res.data.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const handleAction = async (id: string, status: string) => {
    setActionLoading(id + status);
    try {
      await leaveAPI.updateStatus(id, { status });
      fetchLeaves();
    } catch (err) { console.error(err); }
    finally { setActionLoading(null); }
  };

  const stats = {
    pending: leaves.filter(l => l.status === 'pending').length,
    approved: leaves.filter(l => l.status === 'approved').length,
    rejected: leaves.filter(l => l.status === 'rejected').length,
  };

  return (
    <div className="space-y-5">

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Leave Management</h2>
          <p className="text-slate-400 text-sm">{leaves.length} total requests</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Pending', value: stats.pending, icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'Approved', value: stats.approved, icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Rejected', value: stats.rejected, icon: XCircle, color: 'text-red-500', bg: 'bg-red-50' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex items-center gap-3">
            <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center flex-shrink-0`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800">{value}</p>
              <p className="text-slate-400 text-xs">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
        <div className="relative max-w-xs">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full pl-9 pr-8 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
          >
            <option value="">All Requests</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
          </div>
        ) : leaves.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3">
            <AlertCircle className="w-10 h-10 text-slate-300" />
            <p className="text-slate-400 text-sm">No leave requests found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  {['Employee', 'Leave Date', 'Leave Type', 'Reason', 'Status', 'Actions'].map(h => (
                    <th key={h} className="text-left px-5 py-3.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leaves.map((l: any) => (
                  <tr key={l.id} className="hover:bg-slate-50 transition">
                    <td className="px-5 py-4">
                      <div>
                        <p className="text-sm font-medium text-slate-800">{l.employee_name}</p>
                        <p className="text-xs text-slate-400 font-mono">{l.employee_id}</p>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{l.leave_date}</td>
                    <td className="px-5 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${leaveTypeColors[l.leave_type] || 'bg-slate-100 text-slate-600'}`}>
                        {l.leave_type}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600 max-w-xs">
                      <p className="truncate">{l.reason}</p>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${statusColors[l.status]}`}>
                        {l.status}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {l.status === 'pending' && (
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleAction(l.id, 'approved')}
                            disabled={!!actionLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-xs font-semibold transition disabled:opacity-60"
                          >
                            {actionLoading === l.id + 'approved' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                            Approve
                          </button>
                          <button
                            onClick={() => handleAction(l.id, 'rejected')}
                            disabled={!!actionLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white rounded-lg text-xs font-semibold transition disabled:opacity-60"
                          >
                            {actionLoading === l.id + 'rejected' ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
                            Reject
                          </button>
                        </div>
                      )}
                      {l.status !== 'pending' && (
                        <span className="text-slate-400 text-xs">No action needed</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Leaves;