// src/pages/auth/Login.jsx
//
// Unified login page (split-screen SaaS style). Single email + password
// form for every role. The backend decides whether 2FA is required
// (super_admin / finance_manager) and responds accordingly.

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, Shield, Mail, Lock, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [step, setStep] = useState('credentials'); // 'credentials' | 'otp'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tempToken, setTempToken] = useState(null);
  const [otp, setOtp] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);

  const redirectTo = location.state?.from?.pathname || '/';

  const completeLogin = async (access_token, refresh_token) => {
    localStorage.setItem('access_token', access_token);
    const me = await authService.getMe();
    login(me, { access_token, refresh_token });
    navigate(redirectTo, { replace: true });
  };

  const handleLogin = async (e) => {
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
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await authService.verify2FA(tempToken, otp);
      await completeLogin(res.access_token, res.refresh_token);
    } catch (err) {
      setError(err.message || 'Invalid verification code.');
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
      setError(err.message || 'Failed to resend code.');
    }
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="w-full max-w-5xl bg-white rounded-2xl shadow-2xl overflow-hidden flex min-h-[600px] border border-slate-100">

        {/* LEFT SIDE: Purple Brand Layout */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-purple-600 to-indigo-800 p-12 flex-col justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <h1 className="text-white font-bold text-xl">SYNVEX</h1>
              <p className="text-purple-200 text-xs">Next-Gen Solutions</p>
            </div>
          </div>
          <div>
            <div className="w-20 h-20 bg-white/10 rounded-2xl flex items-center justify-center mb-8 backdrop-blur">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-white text-3xl font-bold mb-4">Synvex Business Management</h2>
            <p className="text-purple-200 text-base leading-relaxed">
              AI-powered face recognition attendance system for modern enterprises.
            </p>
            <div className="mt-8 space-y-3">
              {['Face Recognition Technology', 'Real-time Analytics', 'Geo-Fencing Security'].map((item) => (
                <div key={item} className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-purple-300 rounded-full" />
                  <span className="text-purple-100 text-sm">{item}</span>
                </div>
              ))}
            </div>
          </div>
          <p className="text-purple-300 text-sm">© 2026 Synvex. All rights reserved.</p>
        </div>

        {/* RIGHT SIDE: Dynamic Form Side */}
        <div className="w-full lg:w-1/2 p-12 flex flex-col justify-center">
          <div className="max-w-sm mx-auto w-full">

            {/* Responsive Mobile Header */}
            <div className="lg:hidden flex items-center gap-2 mb-8">
              <Shield className="w-7 h-7 text-purple-600" />
              <span className="font-bold text-xl text-slate-800">SYNVEX</span>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-6 text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            {step === 'credentials' && (
              <>
                <h2 className="text-2xl font-bold text-slate-800 mb-1">Welcome back</h2>
                <p className="text-slate-500 text-sm mb-8">Sign in to your account</p>

                <form onSubmit={handleLogin} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Email Address</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="you@synvex.io"
                        className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                        className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center justify-end">
                    <a href="/forgot-password" className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                      Forgot password?
                    </a>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-xl font-semibold text-sm transition disabled:opacity-60"
                  >
                    {loading ? 'Signing in...' : 'Sign In'}
                  </button>
                </form>
              </>
            )}

            {step === 'otp' && (
              <>
                <h2 className="text-2xl font-bold text-slate-800 mb-1">Verification Required</h2>
                <p className="text-slate-500 text-sm mb-8">Enter the 6-digit code we sent to your email.</p>

                <form onSubmit={handleVerifyOtp} className="space-y-5">
                  <div>
                    <input
                      type="text"
                      required
                      maxLength={6}
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                      className="w-full px-4 py-3 border border-slate-200 rounded-xl text-center text-xl tracking-widest font-bold focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                      placeholder="000000"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading || otp.length !== 6}
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-xl font-semibold text-sm transition disabled:opacity-60"
                  >
                    {loading ? 'Verifying...' : 'Verify & Sign In'}
                  </button>
                </form>

                <div className="mt-6 text-center text-sm text-slate-500">
                  Didn't get a code?{' '}
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={resendCooldown > 0}
                    className="text-purple-600 font-medium hover:underline disabled:text-slate-400 disabled:no-underline"
                  >
                    {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                  </button>
                </div>

                <button
                  type="button"
                  onClick={() => { setStep('credentials'); setOtp(''); setError(''); }}
                  className="mt-3 w-full text-center text-sm text-slate-400 hover:text-slate-600"
                >
                  ← Back to login
                </button>
              </>
            )}

          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;