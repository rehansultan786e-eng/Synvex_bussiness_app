import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Mail, Phone, Calendar, Loader2 } from 'lucide-react';
import { employeeService } from '../../services/employeeService';
import StatusBadge from '../../components/StatusBadge';

const TABS = ['Overview', 'Attendance', 'Leave', 'Assets'];

const formatDate = (value) => {
  if (!value) {
    return '—';
  }
  return value;
};

const EmployeeProfile = () => {
  const { employeeId } = useParams();
  const [activeTab, setActiveTab] = useState('Overview');

  const [employee, setEmployee] = useState(null);
  const [attendanceHistory, setAttendanceHistory] = useState([]);
  const [attendanceSummary, setAttendanceSummary] = useState(null);
  const [leaves, setLeaves] = useState([]);
  const [leaveBalance, setLeaveBalance] = useState(null);
  const [assets, setAssets] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      setError('');
      try {
        const now = new Date();
        const month = now.getMonth() + 1;
        const year = now.getFullYear();

        const empRes = await employeeService.getEmployee(employeeId);
        setEmployee(empRes.data);

        const [attHistRes, attSumRes, leaveRes, balanceRes, assetsRes] = await Promise.allSettled([
          employeeService.getAttendanceHistory(employeeId, month, year),
          employeeService.getAttendanceSummary(employeeId, month, year),
          employeeService.getEmployeeLeaves(employeeId),
          employeeService.getLeaveBalance(employeeId, year),
          employeeService.getEmployeeAssets(employeeId)
        ]);

        if (attHistRes.status === 'fulfilled') {
          setAttendanceHistory(attHistRes.value.data || []);
        }
        if (attSumRes.status === 'fulfilled') {
          setAttendanceSummary(attSumRes.value.data);
        }
        if (leaveRes.status === 'fulfilled') {
          setLeaves(leaveRes.value.data || []);
        }
        if (balanceRes.status === 'fulfilled') {
          setLeaveBalance(balanceRes.value.data);
        }
        if (assetsRes.status === 'fulfilled') {
          setAssets(assetsRes.value.data || []);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadAll();
  }, [employeeId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-gray-400">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
        {error || 'Employee not found.'}
      </div>
    );
  }

  return (
    <div>
      <Link to="/employees" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="w-4 h-4" />
        Back to Employees
      </Link>

      <div className="bg-white rounded-card shadow-soft border border-gray-100 p-5 mb-6">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{employee.full_name}</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {employee.designation} &middot; {employee.department} &middot; {employee.employee_id}
            </p>
          </div>
          <StatusBadge status={employee.status} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-5 pt-5 border-t border-gray-50">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Mail className="w-4 h-4 text-gray-400" />
            {employee.email}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Phone className="w-4 h-4 text-gray-400" />
            {employee.phone}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar className="w-4 h-4 text-gray-400" />
            Joined {formatDate(employee.joining_date)}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-1 mb-5 border-b border-gray-100 overflow-x-auto">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={
              'px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ' +
              (activeTab === tab
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700')
            }
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Employment Type</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{employee.employment_type}</p>
          </div>
          <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">CNIC</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{employee.cnic || '—'}</p>
          </div>
          <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Reporting Manager</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{employee.reporting_manager || '—'}</p>
          </div>
          <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Assigned Assets</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{assets.length}</p>
          </div>
        </div>
      )}

      {activeTab === 'Attendance' && (
        <div>
          {attendanceSummary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
              <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Present</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">{attendanceSummary.present_days ?? '—'}</p>
              </div>
              <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Absent</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">{attendanceSummary.absent_days ?? '—'}</p>
              </div>
              <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Late</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">{attendanceSummary.late_days ?? '—'}</p>
              </div>
              <div className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">On Leave</p>
                <p className="text-lg font-semibold text-gray-900 mt-2">{attendanceSummary.leave_days ?? '—'}</p>
              </div>
            </div>
          )}

          <div className="bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
            {attendanceHistory.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-10">No attendance records this month.</p>
            )}
            {attendanceHistory.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                    <th className="px-5 py-3">Date</th>
                    <th className="px-5 py-3">Check In</th>
                    <th className="px-5 py-3">Check Out</th>
                    <th className="px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceHistory.map((rec, idx) => (
                    <tr key={idx} className="border-b border-gray-50 last:border-0">
                      <td className="px-5 py-3.5 text-gray-600">{formatDate(rec.date)}</td>
                      <td className="px-5 py-3.5 text-gray-600">{rec.check_in_time || '—'}</td>
                      <td className="px-5 py-3.5 text-gray-600">{rec.check_out_time || '—'}</td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={rec.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {activeTab === 'Leave' && (
        <div>
          {leaveBalance && (
            <div className="bg-white rounded-card shadow-soft border border-gray-100 p-5 mb-5">
              <h2 className="text-sm font-semibold text-gray-800 mb-3">Leave Balance</h2>
              <div className="flex flex-wrap gap-4">
                {Object.keys(leaveBalance).map((key) => {
                  if (typeof leaveBalance[key] !== 'number') {
                    return null;
                  }
                  return (
                    <div key={key} className="text-sm">
                      <span className="text-gray-400">{key}: </span>
                      <span className="font-medium text-gray-800">{leaveBalance[key]}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
            {leaves.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-10">No leave requests found.</p>
            )}
            {leaves.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                    <th className="px-5 py-3">Type</th>
                    <th className="px-5 py-3">From</th>
                    <th className="px-5 py-3">To</th>
                    <th className="px-5 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {leaves.map((lv) => (
                    <tr key={lv.id || lv.leave_id} className="border-b border-gray-50 last:border-0">
                      <td className="px-5 py-3.5 text-gray-600">{lv.leave_type}</td>
                      <td className="px-5 py-3.5 text-gray-600">{formatDate(lv.from_date)}</td>
                      <td className="px-5 py-3.5 text-gray-600">{formatDate(lv.to_date)}</td>
                      <td className="px-5 py-3.5">
                        <StatusBadge status={lv.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {activeTab === 'Assets' && (
        <div className="bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
          {assets.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-10">No assets assigned.</p>
          )}
          {assets.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                  <th className="px-5 py-3">Asset</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Condition</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((a) => (
                  <tr key={a.asset_id} className="border-b border-gray-50 last:border-0">
                    <td className="px-5 py-3.5 font-medium text-gray-800">{a.name}</td>
                    <td className="px-5 py-3.5 text-gray-600">{a.category}</td>
                    <td className="px-5 py-3.5 text-gray-600">{a.condition}</td>
                    <td className="px-5 py-3.5">
                      <StatusBadge status={a.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
};

export default EmployeeProfile;