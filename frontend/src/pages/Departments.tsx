import React, { useState, useEffect } from 'react';
import {
  Building2, Plus, Pencil, Trash2, Users,
  Loader2, AlertCircle, X, CheckCircle
} from 'lucide-react';
import { departmentAPI } from '../services/api';

const Departments: React.FC = () => {
  const [departments, setDepartments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editData, setEditData] = useState<any>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [form, setForm] = useState({ department_name: '', department_code: '', manager_name: '', description: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { fetchDepartments(); }, []);

  const fetchDepartments = async () => {
    try {
      const res = await departmentAPI.getAll();
      setDepartments(res.data.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const openCreate = () => {
    setEditData(null);
    setForm({ department_name: '', department_code: '', manager_name: '', description: '' });
    setError('');
    setShowModal(true);
  };

  const openEdit = (dept: any) => {
    setEditData(dept);
    setForm({ department_name: dept.department_name, department_code: dept.department_code, manager_name: dept.manager_name, description: dept.description || '' });
    setError('');
    setShowModal(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      if (editData) {
        await departmentAPI.update(editData.department_code, form);
      } else {
        await departmentAPI.create(form);
      }
      setShowModal(false);
      fetchDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save department');
    } finally { setSaving(false); }
  };

  const handleDelete = async (code: string) => {
    try {
      await departmentAPI.delete(code);
      setDepartments(departments.filter(d => d.department_code !== code));
      setDeleteId(null);
    } catch (err) { console.error(err); }
  };

  const colors = ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-yellow-500', 'bg-red-500', 'bg-indigo-500'];

  return (
    <div className="space-y-5">

      {/* Top Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Departments</h2>
          <p className="text-slate-400 text-sm">{departments.length} departments</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition"
        >
          <Plus className="w-4 h-4" />
          New Department
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader2 className="w-7 h-7 animate-spin text-blue-600" />
        </div>
      ) : departments.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 bg-white rounded-2xl border border-slate-200">
          <AlertCircle className="w-10 h-10 text-slate-300" />
          <p className="text-slate-400 text-sm">No departments yet</p>
          <button onClick={openCreate} className="text-blue-600 text-sm font-medium hover:underline">Create first department</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {departments.map((dept: any, i: number) => (
            <div key={dept.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 hover:shadow-md transition">
              <div className="flex items-start justify-between mb-4">
                <div className={`w-11 h-11 ${colors[i % colors.length]} rounded-xl flex items-center justify-center`}>
                  <Building2 className="w-5 h-5 text-white" />
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => openEdit(dept)} className="p-1.5 rounded-lg hover:bg-yellow-50 text-slate-400 hover:text-yellow-600 transition">
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button onClick={() => setDeleteId(dept.department_code)} className="p-1.5 rounded-lg hover:bg-red-50 text-slate-400 hover:text-red-500 transition">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <h3 className="font-bold text-slate-800 mb-1">{dept.department_name}</h3>
              <p className="text-xs text-slate-400 font-mono mb-3">{dept.department_code}</p>
              {dept.description && <p className="text-sm text-slate-500 mb-3 line-clamp-2">{dept.description}</p>}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                  <Users className="w-3.5 h-3.5" />
                  <span>{dept.total_employees} employees</span>
                </div>
                <span className="text-xs text-slate-400">{dept.manager_name}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-bold text-slate-800 text-lg">{editData ? 'Edit Department' : 'New Department'}</h3>
              <button onClick={() => setShowModal(false)} className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 transition">
                <X className="w-5 h-5" />
              </button>
            </div>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-4 text-sm">{error}</div>
            )}
            <form onSubmit={handleSave} className="space-y-4">
              {[
                { label: 'Department Name', key: 'department_name', placeholder: 'e.g. Information Technology' },
                { label: 'Department Code', key: 'department_code', placeholder: 'e.g. IT', disabled: !!editData },
                { label: 'Manager Name', key: 'manager_name', placeholder: 'e.g. John Doe' },
              ].map(({ label, key, placeholder, disabled }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">{label}</label>
                  <input
                    type="text"
                    value={(form as any)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    placeholder={placeholder}
                    disabled={disabled}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition disabled:bg-slate-50 disabled:text-slate-400"
                    required={!disabled}
                  />
                </div>
              ))}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Brief description..."
                  rows={2}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="py-2.5 border border-slate-200 rounded-xl text-sm font-medium text-slate-600 hover:bg-slate-50 transition">
                  Cancel
                </button>
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
            <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 text-center mb-2">Delete Department</h3>
            <p className="text-slate-500 text-sm text-center mb-6">Are you sure? This action cannot be undone.</p>
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

export default Departments;