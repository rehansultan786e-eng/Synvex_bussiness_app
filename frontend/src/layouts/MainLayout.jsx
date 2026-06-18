// src/layouts/MainLayout.jsx
//
// Main app shell: collapsible left sidebar + top navbar + content area
// (rendered via <Outlet />). Sidebar menu items are filtered by the
// logged-in user's role using src/config/navigation.js.
// Updated to the Synvex violet/purple brand palette.

import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getNavItemsForRole } from '../config/navigation';

const ICONS = {
  dashboard: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z',
  sales: 'M3 17l6-6 4 4 8-8M21 7v6h-6',
  commission: 'M12 1v22M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6',
  contracts: 'M9 2h6l5 5v13a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2h3zM9 2v6h6',
  expenses: 'M12 1v22M5 6h14M5 18h14',
  payroll: 'M3 7h18M3 12h18M3 17h18',
  employees: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75',
  attendance: 'M12 8v4l3 3M12 2a10 10 0 110 20 10 10 0 010-20z',
  leave: 'M8 7V3m8 4V3M3 11h18M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z',
  assets: 'M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z',
  performance: 'M18 20V10M12 20V4M6 20v-6',
  reports: 'M3 3v18h18M7 14l4-4 4 4 4-8',
  audit: 'M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11',
  selfservice: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 008.6 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H2a2 2 0 110-4h.09A1.65 1.65 0 003.6 8.6a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H8a1.65 1.65 0 001-1.51V2a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V8a1.65 1.65 0 001.51 1H22a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z',
};

const Icon = ({ name, className }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d={ICONS[name] || ICONS.dashboard} />
  </svg>
);

const roleLabels = {
  super_admin: 'CEO / Super Admin',
  hr_manager: 'HR Manager',
  finance_manager: 'Finance Manager',
  sales_manager: 'Sales Manager',
  sales_rep: 'Sales Representative',
  employee: 'Employee',
};

const MainLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const navItems = user ? getNavItemsForRole(user.role) : [];

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const initials = (user?.full_name || user?.employee_id || '?')
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="flex h-screen bg-surface-subtle">

      {/* Sidebar */}
      <aside
        className={`${collapsed ? 'w-[72px]' : 'w-64'} bg-white border-r border-gray-100 flex flex-col transition-all duration-200`}
      >
        <div className="h-16 flex items-center px-4 border-b border-gray-100 shrink-0">
          
          {!collapsed && (
            <span className="ml-2.5 font-bold text-gray-900 text-sm whitespace-nowrap tracking-tight">SYNVEX MANAGEMENT</span>
          )}
        </div>

        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-control text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-gray-500 hover:bg-surface-subtle hover:text-gray-800'
                }`
              }
            >
              <Icon name={item.icon} className="w-[18px] h-[18px] shrink-0" />
              {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={() => setCollapsed((c) => !c)}
          className="h-12 flex items-center justify-center text-gray-400 hover:text-gray-600 border-t border-gray-100 shrink-0"
        >
          <span className="text-xs">{collapsed ? '»' : '« Collapse'}</span>
        </button>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Topbar */}
        <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-6 shrink-0">
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search across modules..."
              className="w-full px-3.5 py-2 rounded-control border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-light focus:border-primary-light transition-shadow"
            />
          </div>

          <div className="flex items-center gap-4">
            <button className="relative text-gray-400 hover:text-gray-600">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
                <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 01-3.46 0" />
              </svg>
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-red-500" />
            </button>

            <div className="relative">
              <button
                onClick={() => setProfileOpen((p) => !p)}
                className="flex items-center gap-2.5"
              >
                <div className="w-8 h-8 rounded-full bg-primary-light/15 text-primary flex items-center justify-center text-xs font-semibold">
                  {initials}
                </div>
                <div className="hidden sm:block text-left">
                  <p className="text-sm font-medium text-gray-800 leading-tight">
                    {user?.full_name || user?.employee_id}
                  </p>
                  <p className="text-xs text-gray-400 leading-tight">
                    {roleLabels[user?.role] || user?.role}
                  </p>
                </div>
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-44 bg-white rounded-control shadow-elevated border border-gray-100 py-1 z-10">
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;