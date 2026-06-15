import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Bell, ChevronLeft, RefreshCw } from 'lucide-react';
import { notificationAPI } from '../services/api';

interface HeaderProps {
  onMenuClick: () => void;
}

const pageTitles: Record<string, string> = {
  '/admin/dashboard': 'Dashboard',
  '/admin/employees': 'Employee Management',
  '/admin/employees/create': 'Create Employee',
  '/admin/departments': 'Department Management',
  '/admin/schedules': 'Schedule Management',
  '/admin/attendance': 'Attendance Records',
  '/admin/leaves': 'Leave Management',
  '/admin/notifications': 'Notifications',
  '/admin/reports': 'Reports & Analytics',
  '/admin/settings': 'Office Settings',
};

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [unreadCount, setUnreadCount] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());

  const pageTitle = pageTitles[location.pathname] || 'Synvex';
  const canGoBack = location.pathname !== '/admin/dashboard';

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchUnreadCount();
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await notificationAPI.getUnreadCount();
      setUnreadCount(res.data.unread_count);
    } catch {}
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit', minute: '2-digit', hour12: true
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', year: 'numeric'
    });
  };

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
      
      <div className="flex items-center gap-4">
        {/* Mobile menu */}
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Back Button */}
        {canGoBack && (
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 transition font-medium"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
        )}

        <h2 className="text-slate-800 font-semibold text-base">{pageTitle}</h2>
      </div>

      <div className="flex items-center gap-4">
        {/* Date & Time */}
        <div className="hidden md:flex flex-col items-end">
          <span className="text-sm font-semibold text-slate-700">{formatTime(currentTime)}</span>
          <span className="text-xs text-slate-400">{formatDate(currentTime)}</span>
        </div>

        {/* Refresh */}
        <button
          onClick={() => window.location.reload()}
          className="p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/admin/notifications')}
          className="relative p-2 rounded-xl hover:bg-slate-100 text-slate-500 transition"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* Admin Avatar */}
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center">
          <span className="text-white text-xs font-bold">A</span>
        </div>
      </div>
    </header>
  );
};

export default Header;