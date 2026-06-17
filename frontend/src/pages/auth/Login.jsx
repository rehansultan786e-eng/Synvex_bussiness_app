// src/pages/auth/Login.jsx
//
// Login page. Two modes: "Manager Login" (email-based, for super_admin /
// hr_manager / finance_manager / sales_manager / sales_rep) and
// "Employee Login" (employee_id-based). Handles the 2FA step inline
// when the backend responds with requires_2fa: true.

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [mode, setMode] = useState('manager'); // 'manager' | 'employee'
  const [step, setStep] = useState('credentials'); // 'credentials' | 'otp'

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [employeeId, setEmployeeId] = useState('');

  const [tempToken, setTempToken] = useState(null);
  const [pendingRole, setPendingRole] = useState(null);
  const [otp, setOtp] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const redirectTo = location.state?.from?.pathname || '/';

  const handleManagerLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authService.login(email, password);

      if (res.requires_2fa) {
        setTempToken(res.temp_token);
        setStep('otp');
      } else {
        await completeLogin(res.access_token, res.refresh_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEmployeeLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authService.employeeLogin(employeeId, password);
      const userData = {
        employee_id: res.employee.employee_id,
        full_name: res.employee.full_name,
        department: res.employee.department,
        designation: res.employee.designation,
        role: 'employee',
      };
      login(userData, { access_token: res.access_token, refresh_token: res.refresh_token });
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const completeLogin = async (access_token, refresh_token) => {
    localStorage.setItem('access_token', access_token);
    const me = await authService.getMe();
    login(me, { access_token, refresh_token });
    navigate(redirectTo, { replace: true });
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authService.verify2FA(tempToken, otp);
      await completeLogin(res.access_token, res.refresh_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendCooldown > 0) return;
    setError('');
    try {
      const res = await authService.resend2FA(tempToken);
      setTempToken(res.temp_token);
      setResendCooldown(30);
      const interval = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      setError(err.message);
    }
  };

  const switchMode = (newMode) => {
    setMode(newMode);
    setStep('credentials');
    setError('');
    setEmail('');
    setPassword('');
    setEmployeeId('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-subtle px-4">
      <div className="w-full max-w-md">

        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-control bg-primary text-white font-semibold text-lg mb-4">
            S
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Synvex</h1>
          <p className="text-sm text-gray-500 mt-1">Business Management System</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-card shadow-elevated border border-gray-100 p-8">

          {step === 'credentials' && (
            <>
              {/* Mode toggle */}
              <div className="flex gap-1 mb-6 p-1 bg-surface-subtle rounded-control">
                <button
                  type="button"
                  onClick={() => switchMode('manager')}
                  className={`flex-1 py-2 text-sm font-medium rounded-control transition-colors ${
                    mode === 'manager'
                      ? 'bg-white text-primary shadow-soft'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Manager Login
                </button>
                <button
                  type="button"
                  onClick={() => switchMode('employee')}
                  className={`flex-1 py-2 text-sm font-medium rounded-control transition-colors ${
                    mode === 'employee'
                      ? 'bg-white text-primary shadow-soft'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Employee Login
                </button>
              </div>

              {error && (
                <div className="mb-4 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                  {error}
                </div>
              )}

              {mode === 'manager' ? (
                <form onSubmit={handleManagerLogin} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Email
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
                      placeholder="you@synvex.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
                      placeholder="••••••••"
                    />
                  </div>
                  <div className="text-right">
                    <a href="/forgot-password" className="text-sm text-primary-light hover:underline">
                      Forgot password?
                    </a>
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 rounded-control bg-primary text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60 transition-colors"
                  >
                    {loading ? 'Signing in...' : 'Sign In'}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleEmployeeLogin} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Employee ID
                    </label>
                    <input
                      type="text"
                      required
                      value={employeeId}
                      onChange={(e) => setEmployeeId(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
                      placeholder="EMP001"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1.5">
                      Password
                    </label>
                    <input
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
                      placeholder="••••••••"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full py-2.5 rounded-control bg-primary text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60 transition-colors"
                  >
                    {loading ? 'Signing in...' : 'Sign In'}
                  </button>
                </form>
              )}
            </>
          )}

          {step === 'otp' && (
            <>
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Verification required</h2>
              <p className="text-sm text-gray-500 mb-6">
                Enter the 6-digit code we sent to your email.
              </p>

              {error && (
                <div className="mb-4 px-4 py-2.5 rounded-control bg-red-50 text-red-700 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-3.5 py-2.5 rounded-control border border-gray-200 text-center text-lg tracking-widest focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
                  placeholder="000000"
                />
                <button
                  type="submit"
                  disabled={loading || otp.length !== 6}
                  className="w-full py-2.5 rounded-control bg-primary text-white text-sm font-medium hover:bg-primary-dark disabled:opacity-60 transition-colors"
                >
                  {loading ? 'Verifying...' : 'Verify & Sign In'}
                </button>
              </form>

              <div className="mt-4 text-center text-sm text-gray-500">
                Didn't get a code?{' '}
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resendCooldown > 0}
                  className="text-primary-light font-medium hover:underline disabled:text-gray-400 disabled:no-underline"
                >
                  {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                </button>
              </div>

              <button
                type="button"
                onClick={() => { setStep('credentials'); setOtp(''); setError(''); }}
                className="mt-3 w-full text-center text-sm text-gray-400 hover:text-gray-600"
              >
                ← Back to login
              </button>
            </>
          )}
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Synvex Private Limited — Internal Use Only
        </p>
      </div>
    </div>
  );
};

export default Login;