import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { authService } from '../../services/authService';

const ROLES = [
  { value: 'hr_manager', label: 'HR Manager' },
  { value: 'finance_manager', label: 'Finance Manager' },
  { value: 'sales_manager', label: 'Sales Manager' },
  { value: 'sales_rep', label: 'Sales Representative' }
];

const InviteUserModal = ({ onClose, onInvited }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('hr_manager');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!fullName || !email) {
      setError('Please fill in all fields.');
      return;
    }

    setSubmitting(true);
    try {
      await authService.inviteUser(fullName, email, role);
      setSuccess(true);
      onInvited();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="text-lg font-semibold text-gray-900">Invite User</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          {success ? (
            <div className="px-4 py-3 rounded-control bg-green-50 text-green-700 text-sm">
              Invite sent. Since this is a local development environment, no real email was sent —
              check the backend terminal for the "Set Your Password" link and open it in the browser.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Full Name *</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Email *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">Role *</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
                Send Invite
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default InviteUserModal;