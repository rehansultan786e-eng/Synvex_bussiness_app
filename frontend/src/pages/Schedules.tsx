import React, { useState, useEffect } from 'react';
import {
  Calendar, Plus, Pencil, Trash2, Clock,
  Loader2, AlertCircle, X, CheckCircle, ChevronDown
} from 'lucide-react';
import { departmentAPI } from '../services/api';
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const shiftColors: Record<string, string> = {
  'Fixed': 'bg-blue-100 text-blue-700',
  'Morning Shift': 'bg-yellow-100 text-yellow-700',
  'Evening Shift': 'bg-purple-100 text-purple-700',
  'Night Shift': 'bg-slate-100 text-slate-700',
};

const Schedules: React.FC = () => {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    schedule_name: '', department: '', shift_type: 'Fixed',
    start_time: '09:00', end_time: '17:00', grace_time: 10, required_hours: 8
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [schedRes, deptRes] = await Promise.all([
        api.get('/api/schedules'),
        departmentAPI.getAll()
      ]);
      setSchedules(schedRes.data.data);
      setDepartments(deptRes.data.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const openCreate = () => {
    setEditData(null);
    setForm({ schedule_name: '', department: '', shift_type: 'Fixed', start_time: '09:00', end_time: '17:00', grace_time: 10, required_hours: 8 });
    setError('');
    setShowModal(true);
  };

  const openEdit = (s: any) => {
    setEditData(s);
    setForm({ schedule_name: s.schedule_name, department: s.department, shift_type: s.shift_type, start_time: s.start_time, end_time: s.end_time, grace_time: s.grace_time, required_hours: s.required_hours });
    setError('');
    setShowModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (editData) {
        await api.put(`/api/schedules/${editData.id}`, form);
      } else {
        await api.post('/api/schedules', form);
      }
      setShowModal(false);
      fetchData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save schedule');
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/api/schedules/${id}`);
      setSchedules(schedules.filter(s => s.id !== id));
      setDeleteId(null);
    } catch (err) { console.error(err); }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Schedules</h2>
          <p className="text-slate-400 text-sm">{schedules.length} schedules configured</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition">
          <Plus className="w-4 h-4" />
          New Schedule
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48"><Loader2 className="w-7 h-7 animate-spin text-blue-600" /></div>
      ) : schedules.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 bg-white rounded-2xl border border-slate-200">
          <AlertCircle className="w-10 h-10 text-slate-300" />
          <p className="text-slate-400 text-sm">No schedules yet</p>
          <button onClick={openCreate} className="text-blue-600 text-sm font-medium hover:underline">Create first schedule</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                {['Schedule Name', 'Department', 'Shift Type', 'Start Time', 'End Time', 'Grace Time', 'Actions'].map(h => (
                  <th key={h} className="text-left px-5 py-3.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {schedules.map((s: any) => (
                <tr key={s.id} className="hover:bg-slate-50 transition">
                  <td className="px-5 py-4 text-sm font-medium text-slate-800">{s.schedule_name}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{s.department}</td>
                  <td className="px-5 py-4">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${shiftColors[s.shift_type] || 'bg-slate-100 text-slate-700'}`}>
                      {s.shift_type}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">{s.start_time}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{s.end_time}</td>
                  <td className="px-5 py-4 text-sm text-slate-600">{s.grace_time} min</td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <button onClick={() => openEdit(s)} className="p-1.5 rounded-lg hover:bg-yellow-50 text-slate-400 hover:text-yellow-600 transition"><Pencil className="w-4 h-4" /></button>
                      <button onClick={() => setDeleteId(s.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-bold text-slate-800 text-lg">{editData ? 'Edit Schedule' : 'New Schedule'}</h3>
              <button onClick={() => setShowModal(false)} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 transition"><X className="w-5 h-5" /></button>
            </div>
            {error && <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">{error}</div>}
            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Schedule Name</label>
                <input type="text" value={form.schedule_name} onChange={(e) => setForm({ ...form, schedule_name: e.target.value })} placeholder="e.g. Morning Fixed" className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Department</label>
                <div className="relative">
                  <select value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white" required>
                    <option value="">Select department</option>
                    {departments.map((d: any) => <option key={d.id} value={d.department_name}>{d.department_name}</option>)}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Shift Type</label>
                <div className="relative">
                  <select value={form.shift_type} onChange={(e) => setForm({ ...form, shift_type: e.target.value })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition appearance-none bg-white">
                    {['Fixed', 'Morning Shift', 'Evening Shift', 'Night Shift'].map(s => <option key={s}>{s}</option>)}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Start Time</label>
                  <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" required />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">End Time</label>
                  <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Grace Time (min)</label>
                  <input type="number" value={form.grace_time} onChange={(e) => setForm({ ...form, grace_time: parseInt(e.target.value) })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">Required Hours</label>
                  <input type="number" value={form.required_hours} onChange={(e) => setForm({ ...form, required_hours: parseFloat(e.target.value) })} className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition">Cancel</button>
                <button type="submit" disabled={saving} className="py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition disabled:opacity-60 flex items-center justify-center gap-2">
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {deleteId && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
            <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center mx-auto mb-4"><Trash2 className="w-6 h-6 text-red-500" /></div>
            <h3 className="text-lg font-bold text-slate-800 text-center mb-2">Delete Schedule</h3>
            <p className="text-slate-500 text-sm text-center mb-6">Are you sure? This cannot be undone.</p>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => setDeleteId(null)} className="py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition">Cancel</button>
              <button onClick={() => handleDelete(deleteId)} className="py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-semibold transition">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Schedules;