// src/pages/Unauthorized.jsx
//
// Shown when a logged-in user tries to access a route their role
// doesn't have permission for.

import React from 'react';
import { Link } from 'react-router-dom';

const Unauthorized = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">403</h1>
        <p className="text-lg text-gray-600 mb-6">
          You don't have permission to access this page.
        </p>
        <Link
          to="/"
          className="inline-block px-5 py-2.5 rounded-lg bg-[#1B3A6B] text-white font-medium hover:bg-[#15305a] transition-colors"
        >
          Go back home
        </Link>
      </div>
    </div>
  );
};

export default Unauthorized;