import React, { useState, useEffect } from 'react';
import {
  ClipboardList, Search, Filter, ChevronDown,
  Loader2, AlertCircle, Clock, UserCheck, UserX, Calendar
} from 'lucide-react';
import { attendanceAPI, departmentAPI } from '../services/api';

const statusColors: Record<string, string> = {
  present: 'bg-green-100 text-green-700',
  late: 'bg-yellow-100 text-yellow-700',
  absent: 'bg-red-100 text-red-600',
  on_leave: 'bg-blue-100 text-blue-700',
  half_day: 'bg-orange-100 text-orange-700',
};

const Attendance: React.FC = () => {
  const [records, setRecords] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [filterDept, setFilterDept] = useState('');

  useEffect(() => {
    departmentAPI.getAll().then(res => setDepartments(res.data.data)).catch(() => {});
  }, []);

  useEffect(() => { fetchAttendance(); }, [selectedDate, filterDept]);

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const res = await attendanceAPI.getByDate(selectedDate, filterDept || undefined);
      setRecords(res.data.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const stats = {
    present: records.filter(r => r.status === 'present').length,
    late: records.filter(r => r.status === 'late').length,
    absent: records.filter(r => r.status === 'absent').length,
    on_leave: records.filter(r => r.status === 'on_leave').length,
  };

  return (
    <div className="space-y-5">

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Attendance Records</h2>
          <p className="text-slate-400 text-sm">{records.length} records found</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Present', value: stats.present, icon: UserCheck, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Late', value: stats.late, icon: Clock, color: 'text-yellow-600', bg: 'bg-yellow-50' },
          { label: 'Absent', value: stats.absent, icon: UserX, color: 'text-red-500', bg: 'bg-red-50' },
          { label: 'On Leave', value: stats.on_leave, icon: Calendar, color: 'text-blue-600', bg: 'bg-blue-50' },
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

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
              className="w-full pl-9 pr-8 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white"
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

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3">
            <AlertCircle className="w-10 h-10 text-slate-300" />
            <p className="text-slate-400 text-sm">No attendance records for this date</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  {['Employee ID', 'Name', 'Department', 'Check In', 'Check Out', 'Work Hours', 'Status'].map(h => (
                    <th key={h} className="text-left px-5 py-3.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((r: any) => (
                  <tr key={r.id} className="hover:bg-slate-50 transition">
                    <td className="px-5 py-4 text-sm font-mono font-medium text-slate-700">{r.employee_id}</td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
                          <span className="text-blue-600 text-xs font-bold">{r.employee_name?.charAt(0)}</span>
                        </div>
                        <span className="text-sm font-medium text-slate-800">{r.employee_name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-sm text-slate-600">{r.department}</td>
                    <td className="px-5 py-4 text-sm text-slate-600">{r.check_in || '—'}</td>
                    <td className="px-5 py-4 text-sm text-slate-600">{r.check_out || '—'}</td>
                    <td className="px-5 py-4 text-sm text-slate-600">{r.work_hours ? `${r.work_hours}h` : '—'}</td>
                    <td className="px-5 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold capitalize ${statusColors[r.status] || 'bg-slate-100 text-slate-600'}`}>
                        {r.status?.replace('_', ' ')}
                      </span>
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

export default Attendance;