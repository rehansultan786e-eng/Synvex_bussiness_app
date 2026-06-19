import React, { useState, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import { employeeService } from '../../services/employeeService';

const EMPLOYMENT_TYPES = ['Full-time', 'Part-time', 'Contract'];

const NewEmployeeModal = ({ onClose, onCreated, editingEmployee }) => {
  const isEditMode = !!editingEmployee;

  const [employeeId, setEmployeeId] = useState(editingEmployee ? editingEmployee.employee_id : '');
  const [fullName, setFullName] = useState(editingEmployee ? editingEmployee.full_name : '');
  const [email, setEmail] = useState(editingEmployee ? editingEmployee.email : '');
  const [phone, setPhone] = useState(editingEmployee ? editingEmployee.phone : '');
  const [department, setDepartment] = useState(editingEmployee ? editingEmployee.department : '');
  const [designation, setDesignation] = useState(editingEmployee ? editingEmployee.designation : '');
  const [joiningDate, setJoiningDate] = useState(editingEmployee ? editingEmployee.joining_date : '');
  const [employmentType, setEmploymentType] = useState(editingEmployee ? editingEmployee.employment_type : 'Full-time');
  const [password, setPassword] = useState('');

  const [departments, setDepartments] = useState([]);
  const [deptLoading, setDeptLoading] = useState(true);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadDepartments = async () => {
      setDeptLoading(true);
      try {
        const res = await employeeService.getDepartments();
        setDepartments(res.data || []);
      } catch (err) {
        setError('Could not load departments: ' + err.message);
      } finally {
        setDeptLoading(false);
      }
    };
    loadDepartments();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!fullName || !email || !phone || !department || !designation) {
      setError('Please fill in all required fields.');
      return;
    }

    if (!isEditMode && (!employeeId || !joiningDate || !password)) {
      setError('Please fill in all required fields.');
      return;
    }

    setSubmitting(true);
    try {
      if (isEditMode) {
        const payload = {
          full_name: fullName,
          email: email,
          phone: phone,
          department: department,
          designation: designation,
          employment_type: employmentType
        };
        if (password) {
          payload.password = password;
        }
        await employeeService.updateEmployee(editingEmployee.employee_id, payload);
      } else {
        const payload = {
          employee_id: employeeId,
          full_name: fullName,
          email: email,
          phone: phone,
          department: department,
          designation: designation,
          joining_date: joiningDate,
          employment_type: employmentType,
          password: password
        };
        await employeeService.createEmployee(payload);
      }
      onCreated();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="text-lg font-semibold text-gray-900">{isEditMode ? 'Edit Employee' : 'New Employee'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-5">
          {error && (
            <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Employee ID *</label>
              <input
                type="text"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                disabled={isEditMode}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light disabled:bg-gray-50 disabled:text-gray-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Full Name *</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Official Email *</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Phone *</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Department *</label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                disabled={deptLoading}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              >
                <option value="">{deptLoading ? 'Loading...' : 'Select department'}</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.department_name}>
                    {d.department_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Designation *</label>
              <input
                type="text"
                value={designation}
                onChange={(e) => setDesignation(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Joining Date {isEditMode ? '' : '*'}</label>
              <input
                type="date"
                value={joiningDate}
                onChange={(e) => setJoiningDate(e.target.value)}
                disabled={isEditMode}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light disabled:bg-gray-50 disabled:text-gray-400"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Employment Type</label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value)}
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              >
                {EMPLOYMENT_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              {isEditMode ? 'Reset Password (leave blank to keep current)' : 'Initial Login Password *'}
            </label>
            <input
              type="text"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={isEditMode ? 'Leave blank to keep current password' : "Set an initial password for the employee's login account"}
              className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-control text-sm font-medium text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {isEditMode ? 'Save Changes' : 'Create Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewEmployeeModal;