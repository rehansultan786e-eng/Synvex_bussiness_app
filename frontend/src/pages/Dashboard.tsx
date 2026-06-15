import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, UserCheck, UserX, Clock, Building2,
  TrendingUp, Bell, ChevronRight, AlertCircle, Loader2
} from 'lucide-react';
import { analyticsAPI, notificationAPI } from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar, Legend
} from 'recharts';

const StatCard: React.FC<{
  title: string; value: number; icon: any;
  color: string; bgColor: string; onClick?: () => void;
}> = ({ title, value, icon: Icon, color, bgColor, onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white rounded-2xl p-5 border border-slate-200 shadow-sm ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
  >
    <div className="flex items-center justify-between mb-3">
      <div className={`w-10 h-10 ${bgColor} rounded-xl flex items-center justify-center`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      {onClick && <ChevronRight className="w-4 h-4 text-slate-400" />}
    </div>
    <p className="text-2xl font-bold text-slate-800">{value}</p>
    <p className="text-slate-500 text-sm mt-0.5">{title}</p>
  </div>
);

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [deptData, setDeptData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, notifRes, monthlyRes, deptRes] = await Promise.all([
        analyticsAPI.getDashboard(),
        notificationAPI.getAll(),
        analyticsAPI.getMonthlyTrend(new Date().getFullYear(), new Date().getMonth() + 1),
        analyticsAPI.getDepartmentStats(),
      ]);
      setStats(statsRes.data.data);
      setNotifications(notifRes.data.data.slice(0, 5));
      setMonthlyData(monthlyRes.data.data.map((d: any) => ({
        date: d._id?.split('-')[2] || d._id,
        present: d.present,
        late: d.late,
        absent: d.absent,
      })));
      setDeptData(deptRes.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
    </div>
  );

  return (
    <div className="space-y-6">

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard title="Total Employees" value={stats?.total_employees || 0} icon={Users} color="text-blue-600" bgColor="bg-blue-50" onClick={() => navigate('/admin/employees')} />
        <StatCard title="Present Today" value={stats?.present_today || 0} icon={UserCheck} color="text-green-600" bgColor="bg-green-50" onClick={() => navigate('/admin/attendance')} />
        <StatCard title="Absent Today" value={stats?.absent_today || 0} icon={UserX} color="text-red-500" bgColor="bg-red-50" onClick={() => navigate('/admin/attendance')} />
        <StatCard title="Late Today" value={stats?.late_today || 0} icon={Clock} color="text-yellow-600" bgColor="bg-yellow-50" onClick={() => navigate('/admin/attendance')} />
        <StatCard title="Departments" value={stats?.total_departments || 0} icon={Building2} color="text-purple-600" bgColor="bg-purple-50" onClick={() => navigate('/admin/departments')} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Monthly Trend Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-800">Monthly Attendance Trend</h3>
              <p className="text-slate-400 text-xs mt-0.5">Current month overview</p>
            </div>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </div>
          {monthlyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #E2E8F0', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Line type="monotone" dataKey="present" stroke="#22C55E" strokeWidth={2} dot={false} name="Present" />
                <Line type="monotone" dataKey="late" stroke="#F59E0B" strokeWidth={2} dot={false} name="Late" />
                <Line type="monotone" dataKey="absent" stroke="#EF4444" strokeWidth={2} dot={false} name="Absent" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-52 flex items-center justify-center text-slate-400 text-sm">
              No attendance data for this month
            </div>
          )}
        </div>

        {/* Notifications Panel */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-800">Recent Notifications</h3>
              <p className="text-slate-400 text-xs mt-0.5">Latest updates</p>
            </div>
            <button onClick={() => navigate('/admin/notifications')} className="text-blue-600 text-xs font-medium hover:underline">
              View all
            </button>
          </div>
          <div className="space-y-3">
            {notifications.length > 0 ? notifications.map((n: any) => (
              <div key={n.id} className={`flex items-start gap-3 p-3 rounded-xl ${!n.is_read ? 'bg-blue-50' : 'bg-slate-50'}`}>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 ${!n.is_read ? 'bg-blue-100' : 'bg-slate-200'}`}>
                  <Bell className={`w-3.5 h-3.5 ${!n.is_read ? 'text-blue-600' : 'text-slate-500'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-slate-800 text-xs font-medium truncate">{n.title}</p>
                  <p className="text-slate-500 text-xs mt-0.5 line-clamp-2">{n.message}</p>
                </div>
              </div>
            )) : (
              <div className="text-center py-8">
                <AlertCircle className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-400 text-sm">No notifications</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Department Stats */}
      {deptData.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-bold text-slate-800">Department Attendance</h3>
              <p className="text-slate-400 text-xs mt-0.5">Today's comparison</p>
            </div>
            <Building2 className="w-5 h-5 text-purple-600" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={deptData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="department" tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} />
              <Tooltip contentStyle={{ borderRadius: '12px', border: '1px solid #E2E8F0', fontSize: '12px' }} />
              <Bar dataKey="present_today" fill="#2563EB" radius={[4, 4, 0, 0]} name="Present" />
              <Bar dataKey="total_employees" fill="#E2E8F0" radius={[4, 4, 0, 0]} name="Total" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default Dashboard;