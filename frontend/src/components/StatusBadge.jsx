// src/components/StatusBadge.jsx
//
// Small colored pill used across modules to show status
// (contract milestones, expenses, payroll, leave, commissions, etc.)

import React from 'react';

const STATUS_STYLES = {
  // Milestone / generic
  Upcoming: 'bg-gray-100 text-gray-600',
  Due: 'bg-amber-50 text-amber-700',
  Received: 'bg-green-50 text-green-700',
  Overdue: 'bg-red-50 text-red-700',
  // Approval-style
  Pending: 'bg-amber-50 text-amber-700',
  'pending': 'bg-amber-50 text-amber-700',
  Approved: 'bg-green-50 text-green-700',
  'approved': 'bg-green-50 text-green-700',
  Rejected: 'bg-red-50 text-red-700',
  'rejected': 'bg-red-50 text-red-700',
  Paid: 'bg-blue-50 text-blue-700',
  Cancelled: 'bg-gray-100 text-gray-500',
  'cancelled': 'bg-gray-100 text-gray-500',
  Reversed: 'bg-red-50 text-red-700',
};

const StatusBadge = ({ status }) => {
  const style = STATUS_STYLES[status] || 'bg-gray-100 text-gray-600';
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${style}`}>
      {status}
    </span>
  );
};

export default StatusBadge;