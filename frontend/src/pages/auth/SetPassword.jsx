import React, { useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { Lock, Loader2, Eye, EyeOff } from 'lucide-react';
import { authService } from '../../services/authService';

const SetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!token) {
      setError('Invite token is missing. Please use the link from your invite email.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await authService.setPasswordViaInvite(token, password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-subtle px-4">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Set Your Password</h1>
        <p className="text-sm text-gray-500 mb-6">Choose a password to activate your account.</p>

        {success ? (
          <div className="px-4 py-3 rounded-control bg-green-50 text-green-700 text-sm">
            Account activated. Redirecting to login...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-9 pr-9 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-gray-400 mt-1">Minimum 8 characters, with uppercase, lowercase, number, and special character.</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Confirm Password</label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Activate Account
            </button>
          </form>
        )}

        <Link to="/login" className="block text-center text-sm text-gray-500 hover:text-gray-700 mt-6">
          Back to login
        </Link>
      </div>
    </div>
  );
};

export default SetPassword;