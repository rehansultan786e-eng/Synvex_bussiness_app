import React, { useState, useEffect } from 'react';
import {
  BarChart3, Download, Filter, Calendar,
  Loader2, TrendingUp, Users, Clock, UserX, ChevronDown
} from 'lucide-react';
import { analyticsAPI, departmentAPI, attendanceAPI } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, LineChart, Line, Legend
} from 'recharts';

const Reports: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState<any[]>([]);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [deptStats, setDeptStats] = useState<any[]>([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [filterDept, setFilterDept] = useState('');
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchData();
  }, [selectedMonth, selectedYear]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, monthlyRes, deptRes, deptListRes] = await Promise.all([
        analyticsAPI.getDashboard(),
        analyticsAPI.getMonthlyTrend(selectedYear, selectedMonth),
        analyticsAPI.getDepartmentStats(),
        departmentAPI.getAll(),
      ]);
      setStats(statsRes.data.data);
      setMonthlyData(monthlyRes.data.data.map((d: any) => ({
        date: d._id?.split('-')[2] || d._id,
        present: d.present,
        late: d.late,
        absent: d.absent,
        on_leave: d.on_leave,
      })));
      setDeptStats(deptRes.data.data);
      setDepartments(deptListRes.data.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const exportCSV = () => {
    const headers = ['Date', 'Present', 'Late', 'Absent', 'On Leave'];
    const rows = monthlyData.map(d => [d.date, d.present, d.late, d.absent, d.on_leave]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_report_${selectedYear}_${selectedMonth}.csv`;
    a.click();
  };

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Reports & Analytics</h2>
          <p className="text-slate-400 text-sm">Attendance insights and statistics</p>
        </div>
        <button
          onClick={exportCSV}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="relative">
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
            >
              {months.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>
          <div className="relative">
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
            >
              {[2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>
          <div className="relative">
            <select
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
            >
              <option value="">All Departments</option>
              {departments.map((d: any) => (
                <option key={d.id} value={d.department_name}>{d.department_name}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Employees', value: stats?.total_employees || 0, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Present Today', value: stats?.present_today || 0, icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Absent Today', value: stats?.absent_today || 0, icon: UserX, color: 'text-red-500', bg: 'bg-red-50' },
          { label: 'Late Today', value: stats?.late_today || 0, icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex items-center gap-3">
            <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <p className="text-xl font-bold text-slate-800">{value}</p>
              <p className="text-slate-400 text-xs">{label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Monthly Trend */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="font-bold text-slate-800">Monthly Attendance Trend</h3>
            <p className="text-slate-400 text-xs">{months[selectedMonth - 1]} {selectedYear}</p>
          </div>
          <TrendingUp className="w-5 h-5 text-blue-600" />
        </div>
        {monthlyData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #E2E8F0', fontSize: '12px' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line type="monotone" dataKey="present" stroke="#22C55E" strokeWidth={2} dot={false} name="Present" />
              <Line type="monotone" dataKey="late" stroke="#F59E0B" strokeWidth={2} dot={false} name="Late" />
              <Line type="monotone" dataKey="absent" stroke="#EF4444" strokeWidth={2} dot={false} name="Absent" />
              <Line type="monotone" dataKey="on_leave" stroke="#2563EB" strokeWidth={2} dot={false} name="On Leave" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-52 flex items-center justify-center text-slate-400 text-sm">
            No data available for this period
          </div>
        )}
      </div>

      {/* Department Stats */}
      {deptStats.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-800">Department Comparison</h3>
              <p className="text-slate-400 text-xs">Today's attendance by department</p>
            </div>
            <BarChart3 className="w-5 h-5 text-purple-600" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={deptStats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="department" tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #E2E8F0', fontSize: '12px' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="total_employees" fill="#E2E8F0" radius={[4, 4, 0, 0]} name="Total" />
              <Bar dataKey="present_today" fill="#2563EB" radius={[4, 4, 0, 0]} name="Present" />
            </BarChart>
          </ResponsiveContainer>

          {/* Department Table */}
          <div className="mt-5 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 rounded-xl">
                  {['Department', 'Total', 'Present', 'Attendance Rate'].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {deptStats.map((d: any) => (
                  <tr key={d.department} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">{d.department}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{d.total_employees}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{d.present_today}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-100 rounded-full h-1.5">
                          <div
                            className="bg-blue-600 h-1.5 rounded-full"
                            style={{ width: `${d.attendance_rate}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-700 w-10">{d.attendance_rate}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;