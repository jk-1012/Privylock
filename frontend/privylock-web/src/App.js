/**
 * Main App Component - WITH GOOGLE OAUTH PROVIDER
 *
 * FIXES APPLIED:
 * ✅ Added GoogleOAuthProvider wrapper (CRITICAL for @react-oauth/google)
 * ✅ Removed PublicRoute redirect (was causing login loop)
 * ✅ Proper ProtectedRoute implementation
 * ✅ Correct navigation flow
 *
 * Routes:
 * - /register - Registration page
 * - /login - Login page
 * - /verify-email/:token - Email verification
 * - /dashboard - Main dashboard (protected)
 * - / - Redirect to dashboard if logged in, else login
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Register from './components/auth/Register';
import Login from './components/auth/Login';
import VerifyEmail from './components/auth/VerifyEmail';
import Dashboard from './components/dashboard/Dashboard';
import './App.css';

/**
 * Protected Route Component
 * ✅ Only redirects to login if NOT authenticated
 */
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  console.log('🔷 ProtectedRoute check:', { user: !!user, loading });

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" replace />;
};

/**
 * Root Redirect Component
 * ✅ Redirects to dashboard if logged in, else login
 */
const RootRedirect = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return user ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />;
};

/**
 * Main App Component
 *
 * ✅ CRITICAL: Wrapped with GoogleOAuthProvider
 * Without this wrapper, GoogleLogin component will NOT work!
 */
function App() {
  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
      <Router>
        <AuthProvider>
          <div className="app">
            <Routes>
              {/* ✅ Public Routes - NO redirect if already logged in */}
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />
              <Route path="/verify-email/:token" element={<VerifyEmail />} />

              {/* ✅ Protected Routes - Require authentication */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />

              {/* ✅ Root Route - Smart redirect */}
              <Route path="/" element={<RootRedirect />} />

              {/* ✅ 404 Route - Redirect to login */}
              <Route path="*" element={<Navigate to="/login" replace />} />
            </Routes>
          </div>
        </AuthProvider>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;