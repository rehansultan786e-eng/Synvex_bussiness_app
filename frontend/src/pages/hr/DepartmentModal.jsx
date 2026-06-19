import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { employeeService } from '../../services/employeeService';

const DepartmentModal = ({ departments, onClose, onCreated }) => {
  const [departmentName, setDepartmentName] = useState('');
  const [departmentCode, setDepartmentCode] = useState('');
  const [managerName, setManagerName] = useState('');
  const [description, setDescription] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!departmentName || !departmentCode || !managerName) {
      setError('Please fill in all required fields.');
      return;
    }

    const payload = {
      department_name: departmentName,
      department_code: departmentCode,
      manager_name: managerName,
      description: description || null
    };

    setSubmitting(true);
    try {
      await employeeService.createDepartment(payload);
      setDepartmentName('');
      setDepartmentCode('');
      setManagerName('');
      setDescription('');
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="text-lg font-semibold text-gray-900">Manage Departments</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          {departments.length > 0 && (
            <div className="mb-5 space-y-2">
              {departments.map((d) => (
                <div
                  key={d.id}
                  className="flex items-center justify-between bg-surface-subtle rounded-control px-3 py-2.5"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-800">{d.department_name}</p>
                    <p className="text-xs text-gray-400">{d.department_code} &middot; {d.manager_name}</p>
                  </div>
                  <span className="text-xs text-gray-500">{d.total_employees} employees</span>
                </div>
              ))}
            </div>
          )}

          {departments.length === 0 && (
            <p className="text-sm text-gray-500 mb-5">No departments yet. Add your first one below.</p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 pt-4 border-t border-gray-100">
            {error && (
              <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Department Name *</label>
                <input
                  type="text"
                  value={departmentName}
                  onChange={(e) => setDepartmentName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Department Code *</label>
                <input
                  type="text"
                  value={departmentCode}
                  onChange={(e) => setDepartmentCode(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Manager Name *</label>
              <input
                type="text"
                value={managerName}
                onChange={(e) => setManagerName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="submit"
                disabled={submitting}
                className="flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                Add Department
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DepartmentModal;