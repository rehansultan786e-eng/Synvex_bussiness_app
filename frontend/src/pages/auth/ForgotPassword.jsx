import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Loader2, ArrowLeft } from 'lucide-react';
import { authService } from '../../services/authService';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-subtle px-4">
      <div className="bg-white rounded-card shadow-elevated w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-gray-900 mb-1">Forgot Password</h1>
        <p className="text-sm text-gray-500 mb-6">
          Enter your email and we will send you a link to reset your password.
        </p>

        {sent ? (
          <div className="px-4 py-3 rounded-control bg-green-50 text-green-700 text-sm">
            If an account exists with this email, a password reset link has been sent. Please check your inbox.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-1.5 bg-primary hover:bg-primary-dark text-white px-4 py-2.5 rounded-control text-sm font-medium transition-colors disabled:opacity-60"
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin" />}
              Send Reset Link
            </button>
          </form>
        )}

        <Link to="/login" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mt-6">
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>
      </div>
    </div>
  );
};

export default ForgotPassword;