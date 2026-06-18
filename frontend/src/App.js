// src/App.js
//
// Root routing. Public routes (login) are outside ProtectedRoute.
// All other routes are wrapped in ProtectedRoute, which checks auth
// state and (optionally) role before rendering MainLayout's children.

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import MainLayout from './layouts/MainLayout';
import Login from './pages/auth/Login';
import Unauthorized from './pages/Unauthorized';
import Dashboard from './pages/Dashboard';


function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          

          {/* Protected routes — any authenticated user (no role restriction) */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Dashboard />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;