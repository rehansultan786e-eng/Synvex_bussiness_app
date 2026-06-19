import React, { useState, useEffect } from 'react';
import { Plus, Users, Loader2, Pencil, Trash2, UserPlus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { employeeService } from '../../services/employeeService';
import { authService } from '../../services/authService';
import { useAuth } from '../../context/AuthContext';
import StatusBadge from '../../components/StatusBadge';
import NewEmployeeModal from './NewEmployeeModal';
import DepartmentModal from './DepartmentModal';
import InviteUserModal from './InviteUserModal';

const ROLE_LABELS = {
  hr_manager: 'HR Manager',
  finance_manager: 'Finance Manager',
  sales_manager: 'Sales Manager',
  sales_rep: 'Sales Representative'
};

const Employees = () => {
  const { user } = useAuth();
  const isSuperAdmin = user && user.role === 'super_admin';

  const [activeTab, setActiveTab] = useState('employees');

  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [managers, setManagers] = useState([]);
  const [managersLoading, setManagersLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [showNewModal, setShowNewModal] = useState(false);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [deletingId, setDeletingId] = useState('');

  const loadEmployees = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await employeeService.getEmployees(undefined, undefined, search || undefined);
      setEmployees(res.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadDepartments = async () => {
    try {
      const res = await employeeService.getDepartments();
      setDepartments(res.data || []);
    } catch (err) {
      // silent fail, dropdown will just show none
    }
  };

  const loadManagers = async () => {
    setManagersLoading(true);
    try {
      const res = await authService.getManagersAndReps();
      setManagers(res.users || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setManagersLoading(false);
    }
  };

  useEffect(() => {
    loadEmployees();
    loadDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (activeTab === 'managers' && managers.length === 0) {
      loadManagers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadEmployees();
  };

  const handleDelete = async (employeeId, fullName) => {
    const confirmed = window.confirm('Delete employee ' + fullName + '? This will also deactivate their login account.');
    if (!confirmed) {
      return;
    }
    setDeletingId(employeeId);
    try {
      await employeeService.deleteEmployee(employeeId);
      loadEmployees();
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId('');
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-6 flex-wrap">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Employees</h1>
          <p className="text-sm text-gray-500 mt-0.5">Employee directory and onboarding</p>
        </div>
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          {isSuperAdmin && (
            <button
              onClick={() => setShowInviteModal(true)}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-control border border-gray-200 text-sm font-medium text-gray-600 hover:bg-surface-subtle"
            >
              <UserPlus className="w-4 h-4" />
              Invite User
            </button>
          )}
          <button
            onClick={() => setShowDeptModal(true)}
            className="px-4 py-2.5 rounded-control border border-gray-200 text-sm font-medium text-gray-600 hover:bg-surface-subtle"
          >
            Departments
          </button>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="hidden sm:inline">New Employee</span>
          </button>
        </div>
      </div>

      <div className="flex items-center gap-1 mb-5 border-b border-gray-100">
        <button
          onClick={() => setActiveTab('employees')}
          className={
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ' +
            (activeTab === 'employees'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-700')
          }
        >
          Employees
        </button>
        <button
          onClick={() => setActiveTab('managers')}
          className={
            'px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ' +
            (activeTab === 'managers'
              ? 'border-primary text-primary'
              : 'border-transparent text-gray-500 hover:text-gray-700')
          }
        >
          Managers &amp; Reps
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      {activeTab === 'employees' && (
        <div>
          <form onSubmit={handleSearchSubmit} className="mb-4 flex gap-2">
            <input
              type="text"
              placeholder="Search by name or employee ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
            />
            <button
              type="submit"
              className="px-4 py-2.5 rounded-control border border-gray-200 text-sm font-medium text-gray-600 hover:bg-surface-subtle"
            >
              Search
            </button>
          </form>

          {loading && (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          )}

          {!loading && employees.length === 0 && (
            <div className="bg-white rounded-card shadow-soft border border-gray-100 p-12 text-center">
              <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">No employees yet. Add your first employee to get started.</p>
            </div>
          )}

          {!loading && employees.length > 0 && (
            <div>
              <div className="hidden md:block bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                      <th className="px-5 py-3">Employee ID</th>
                      <th className="px-5 py-3">Name</th>
                      <th className="px-5 py-3">Department</th>
                      <th className="px-5 py-3">Designation</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map((e) => (
                      <tr key={e.id} className="border-b border-gray-50 last:border-0 hover:bg-surface-subtle transition-colors">
                        <td className="px-5 py-3.5 text-gray-600">{e.employee_id}</td>
                        <td className="px-5 py-3.5 font-medium text-gray-800">
                          <Link to={'/employees/' + e.employee_id} className="hover:text-primary-light hover:underline">
                            {e.full_name}
                          </Link>
                        </td>
                        <td className="px-5 py-3.5 text-gray-600">{e.department}</td>
                        <td className="px-5 py-3.5 text-gray-600">{e.designation}</td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={e.status} />
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="flex items-center justify-end gap-3">
                            <button
                              onClick={() => setEditingEmployee(e)}
                              className="text-gray-400 hover:text-primary-light"
                              title="Edit"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(e.employee_id, e.full_name)}
                              disabled={deletingId === e.employee_id}
                              className="text-gray-400 hover:text-red-500 disabled:opacity-50"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="md:hidden space-y-3">
                {employees.map((e) => (
                  <div key={e.id} className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <Link to={'/employees/' + e.employee_id} className="font-medium text-gray-800 text-sm hover:text-primary-light hover:underline">
                        {e.full_name}
                      </Link>
                      <StatusBadge status={e.status} />
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{e.employee_id}</p>
                    <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                      <span>{e.department}</span>
                      <span>{e.designation}</span>
                    </div>
                    <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-50">
                      <button
                        onClick={() => setEditingEmployee(e)}
                        className="flex items-center gap-1 text-xs font-medium text-primary-light"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(e.employee_id, e.full_name)}
                        disabled={deletingId === e.employee_id}
                        className="flex items-center gap-1 text-xs font-medium text-red-500 disabled:opacity-50"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'managers' && (
        <div>
          {managersLoading && (
            <div className="flex items-center justify-center py-20 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin" />
            </div>
          )}

          {!managersLoading && managers.length === 0 && (
            <div className="bg-white rounded-card shadow-soft border border-gray-100 p-12 text-center">
              <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">No managers or reps invited yet.</p>
            </div>
          )}

          {!managersLoading && managers.length > 0 && (
            <div>
              <div className="hidden md:block bg-white rounded-card shadow-soft border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">
                      <th className="px-5 py-3">Name</th>
                      <th className="px-5 py-3">Email</th>
                      <th className="px-5 py-3">Role</th>
                      <th className="px-5 py-3">Account Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {managers.map((m) => (
                      <tr key={m.id} className="border-b border-gray-50 last:border-0 hover:bg-surface-subtle transition-colors">
                        <td className="px-5 py-3.5 font-medium text-gray-800">{m.full_name}</td>
                        <td className="px-5 py-3.5 text-gray-600">{m.email}</td>
                        <td className="px-5 py-3.5 text-gray-600">{ROLE_LABELS[m.role] || m.role}</td>
                        <td className="px-5 py-3.5">
                          <StatusBadge status={m.is_active ? 'Active' : 'Pending'} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="md:hidden space-y-3">
                {managers.map((m) => (
                  <div key={m.id} className="bg-white rounded-card shadow-soft border border-gray-100 p-4">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-gray-800 text-sm">{m.full_name}</p>
                      <StatusBadge status={m.is_active ? 'Active' : 'Pending'} />
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{m.email}</p>
                    <p className="text-xs text-gray-500 mt-1">{ROLE_LABELS[m.role] || m.role}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {showNewModal && (
        <NewEmployeeModal
          onClose={() => setShowNewModal(false)}
          onCreated={() => {
            setShowNewModal(false);
            loadEmployees();
            loadDepartments();
          }}
        />
      )}

      {editingEmployee && (
        <NewEmployeeModal
          editingEmployee={editingEmployee}
          onClose={() => setEditingEmployee(null)}
          onCreated={() => {
            setEditingEmployee(null);
            loadEmployees();
          }}
        />
      )}

      {showDeptModal && (
        <DepartmentModal
          departments={departments}
          onClose={() => setShowDeptModal(false)}
          onCreated={() => {
            loadDepartments();
          }}
        />
      )}

      {showInviteModal && (
        <InviteUserModal
          onClose={() => setShowInviteModal(false)}
          onInvited={() => {
            loadManagers();
          }}
        />
      )}
    </div>
  );
};

export default Employees;