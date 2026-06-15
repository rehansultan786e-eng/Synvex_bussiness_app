import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Shield, Mail, Lock, ArrowLeft, AlertTriangle } from 'lucide-react';
import { authAPI } from '../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [attempts, setAttempts] = useState(0);
  const [lockUntil, setLockUntil] = useState<number | null>(null);
  const [timeLeft, setTimeLeft] = useState(0);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) navigate('/admin/dashboard', { replace: true });
  }, [navigate]);

  // Load attempts from localStorage
  useEffect(() => {
    const savedAttempts = parseInt(localStorage.getItem('login_attempts') || '0');
    const savedLockUntil = parseInt(localStorage.getItem('lock_until') || '0');
    setAttempts(savedAttempts);
    if (savedLockUntil > Date.now()) {
      setLockUntil(savedLockUntil);
    } else {
      localStorage.removeItem('login_attempts');
      localStorage.removeItem('lock_until');
    }
  }, []);

  // Countdown timer
  useEffect(() => {
    if (!lockUntil) return;
    const interval = setInterval(() => {
      const remaining = Math.ceil((lockUntil - Date.now()) / 1000);
      if (remaining <= 0) {
        setLockUntil(null);
        setAttempts(0);
        setTimeLeft(0);
        localStorage.removeItem('login_attempts');
        localStorage.removeItem('lock_until');
        clearInterval(interval);
      } else {
        setTimeLeft(remaining);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [lockUntil]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    // Check if locked
    if (lockUntil && Date.now() < lockUntil) return;

    setLoading(true);
    setError('');

    try {
      const response = await authAPI.login(email, password);
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.removeItem('login_attempts');
      localStorage.removeItem('lock_until');
      navigate('/admin/dashboard', { replace: true });
    } catch (err: any) {
      const newAttempts = attempts + 1;
      setAttempts(newAttempts);
      localStorage.setItem('login_attempts', String(newAttempts));

      if (newAttempts >= 3) {
        const lockTime = Date.now() + 5 * 60 * 1000; // 5 minutes
        setLockUntil(lockTime);
        localStorage.setItem('lock_until', String(lockTime));
        setError('Too many attempts. Try again in 5 minutes.');
      } else {
        setError(`Invalid email or password. ${3 - newAttempts} attempt(s) remaining.`);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const isLocked = lockUntil !== null && Date.now() < lockUntil;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl bg-white rounded-2xl shadow-2xl overflow-hidden flex min-h-[600px]">

        {/* Left Side */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 to-blue-800 p-12 flex-col justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-white font-bold text-xl">SYNVEX</h1>
              <p className="text-blue-200 text-xs">Next-Gen Solutions</p>
            </div>
          </div>
          <div>
            <div className="w-20 h-20 bg-white/10 rounded-2xl flex items-center justify-center mb-8 backdrop-blur">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-white text-3xl font-bold mb-4">Smart Attendance Management</h2>
            <p className="text-blue-200 text-base leading-relaxed">
              AI-powered face recognition attendance system for modern enterprises.
            </p>
            <div className="mt-8 space-y-3">
              {['Face Recognition Technology', 'Real-time Analytics', 'Geo-Fencing Security'].map((item) => (
                <div key={item} className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-blue-300 rounded-full" />
                  <span className="text-blue-100 text-sm">{item}</span>
                </div>
              ))}
            </div>
          </div>
          <p className="text-blue-300 text-sm">© 2026 Synvex. All rights reserved.</p>
        </div>

        {/* Right Side */}
        <div className="w-full lg:w-1/2 p-12 flex flex-col justify-center">
          <div className="max-w-sm mx-auto w-full">

            {/* Back Button */}
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 text-slate-500 hover:text-blue-600 transition text-sm font-medium mb-8"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Attendance
            </button>

            <div className="lg:hidden flex items-center gap-2 mb-8">
              <Shield className="w-7 h-7 text-blue-600" />
              <span className="font-bold text-xl text-slate-800">SYNVEX</span>
            </div>

            <h2 className="text-2xl font-bold text-slate-800 mb-1">Welcome back</h2>
            <p className="text-slate-500 text-sm mb-8">Sign in to your admin account</p>

            {/* Locked State */}
            {isLocked && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
                <div className="flex items-center gap-2 text-red-600 mb-1">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm font-semibold">Account Temporarily Locked</span>
                </div>
                <p className="text-red-500 text-sm">Too many failed attempts.</p>
                <p className="text-red-700 font-bold text-lg mt-1">
                  Try again in {formatTime(timeLeft)}
                </p>
              </div>
            )}

            {/* Error */}
            {error && !isLocked && (
              <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-3 mb-6 text-sm flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="admin@synvex.com"
                    disabled={isLocked}
                    className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition disabled:bg-slate-50 disabled:text-slate-400"
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
                    disabled={isLocked}
                    className="w-full pl-10 pr-12 py-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition disabled:bg-slate-50 disabled:text-slate-400"
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

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="w-4 h-4 rounded border-slate-300 text-blue-600" />
                  <span className="text-sm text-slate-600">Remember me</span>
                </label>
                <button
                  type="button"
                  onClick={() => alert('Please contact system administrator to reset your password.')}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={loading || isLocked}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-xl font-semibold text-sm transition disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            {/* Attempts indicator */}
            {attempts > 0 && !isLocked && (
              <div className="mt-4 flex justify-center gap-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${i <= attempts ? 'bg-red-400' : 'bg-slate-200'}`}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;