// src/routes/ProtectedRoute.jsx
//
// Guards routes based on authentication and (optionally) role.
// - If auth state is still loading (checking localStorage), renders nothing yet.
// - If not logged in, redirects to /login.
// - If allowedRoles is provided and the user's role isn't in it, redirects
//   to /unauthorized.
// - Otherwise renders the protected content (Outlet for nested routes).

import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ allowedRoles }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return null;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;