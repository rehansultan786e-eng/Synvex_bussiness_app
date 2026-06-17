// src/config/navigation.js
//
// Sidebar navigation items per role, based on SRS Section 16
// (Glossary of System Roles & Access). Each item: label, path, icon
// (a simple text/emoji-free key used by the Sidebar to pick an icon),
// and the roles allowed to see it.

export const NAV_ITEMS = [
  { label: 'Dashboard', path: '/', icon: 'dashboard', roles: ['super_admin', 'hr_manager', 'finance_manager', 'sales_manager', 'sales_rep', 'employee'] },
  { label: 'Sales & Leads', path: '/sales', icon: 'sales', roles: ['super_admin', 'sales_manager', 'sales_rep'] },
  { label: 'Commissions', path: '/commissions', icon: 'commission', roles: ['super_admin', 'sales_manager', 'sales_rep', 'finance_manager'] },
  { label: 'Contracts & Finance', path: '/contracts', icon: 'contracts', roles: ['super_admin', 'finance_manager'] },
  { label: 'Expenses', path: '/expenses', icon: 'expenses', roles: ['super_admin', 'finance_manager', 'hr_manager', 'sales_manager', 'sales_rep', 'employee'] },
  { label: 'Payroll', path: '/payroll', icon: 'payroll', roles: ['super_admin', 'finance_manager', 'hr_manager'] },
  { label: 'Employees', path: '/employees', icon: 'employees', roles: ['super_admin', 'hr_manager'] },
  { label: 'Attendance', path: '/attendance', icon: 'attendance', roles: ['super_admin', 'hr_manager', 'employee'] },
  { label: 'Leave', path: '/leave', icon: 'leave', roles: ['super_admin', 'hr_manager', 'employee'] },
  { label: 'Assets', path: '/assets', icon: 'assets', roles: ['super_admin', 'hr_manager', 'employee'] },
  { label: 'Performance', path: '/performance', icon: 'performance', roles: ['super_admin', 'hr_manager', 'employee'] },
  { label: 'Reports & Analytics', path: '/reports', icon: 'reports', roles: ['super_admin', 'finance_manager'] },
  { label: 'Audit Logs', path: '/audit-logs', icon: 'audit', roles: ['super_admin'] },
  { label: 'My Self-Service', path: '/self-service', icon: 'selfservice', roles: ['employee'] },
  { label: 'Settings', path: '/settings', icon: 'settings', roles: ['super_admin'] },
];

export const getNavItemsForRole = (role) => NAV_ITEMS.filter((item) => item.roles.includes(role));