/**
 * Login Component - COMPLETE FIX
 *
 * FIXES APPLIED:
 * ✅ Proper error extraction from backend response
 * ✅ Fixed "verify email" showing for non-existent users
 * ✅ Fixed [object Object] error for Google login
 * ✅ Better error handling
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { GoogleLogin } from '@react-oauth/google';
import './Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, googleLogin, user, loading: authLoading } = useAuth();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  /**
   * If already logged in, redirect to dashboard
   */
  useEffect(() => {
    if (!authLoading && user) {
      console.log('✅ Already logged in, redirecting to dashboard');
      navigate('/dashboard', { replace: true });
    }
  }, [user, authLoading, navigate]);

  /**
   * Check for success message from registration
   */
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      if (location.state?.email) {
        setEmail(location.state.email);
      }
      // Clear location state
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  /**
   * Handle email/password login
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    // Validation
    if (!email || !password) {
      setError('Email and password are required');
      return;
    }

    setLoading(true);

    try {
      console.log('🔐 Logging in with email...');

      await login(email, password);

      console.log('✅ Login successful!');
      console.log('🔄 Redirecting to dashboard...');

      navigate('/dashboard', { replace: true });

    } catch (err) {
      console.error('❌ Login failed:', err);
      console.error('Error response:', err.response);
      console.error('Error response data:', err.response?.data);

      let errorMessage = 'Login failed. Please try again.';

      if (err.response?.data) {
        const data = err.response.data;
        
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.message) {
          errorMessage = data.message;
        }
      } else if (err.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }

      console.error('📝 Final error message:', errorMessage);

      // Handle specific error types based on ACTUAL error message
      const lowerMsg = errorMessage.toLowerCase();
      
      if (lowerMsg.includes('verify') && lowerMsg.includes('email')) {
        setError('Please verify your email before logging in. Check your inbox for the verification link.');
      } else if (lowerMsg.includes('invalid credentials') || lowerMsg.includes('invalid email')) {
        setError('Invalid email or password. Please try again.');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Google OAuth Success
   */
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setLoading(true);
      setError('');
      setSuccessMessage('');

      console.log('🌐 Google Sign-In response received');
      console.log('Credential:', credentialResponse.credential ? 'Present' : 'Missing');

      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google. Please try again.');
      }

      console.log('📤 Sending credential to backend...');

      await googleLogin(credentialResponse.credential);

      console.log('✅ Google login successful!');
      console.log('🔄 Redirecting to dashboard...');

      navigate('/dashboard', { replace: true });

    } catch (err) {
      console.error('❌ Google login failed:', err);
      console.error('Error response:', err.response);
      console.error('Error response data:', err.response?.data);

      let errorMessage = 'Google sign-in failed. Please try again.';

      if (err.response?.data) {
        const data = err.response.data;
        console.log('📋 Google error data type:', typeof data);
        console.log('📋 Google error data:', data);

        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.mobile_number) {
          // Mobile number required error
          const msg = Array.isArray(data.mobile_number) ? data.mobile_number[0] : data.mobile_number;
          errorMessage = msg;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.non_field_errors) {
          const msg = Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors;
          errorMessage = msg;
        } else if (typeof data === 'object') {
          // Get first error from any field
          const keys = Object.keys(data);
          if (keys.length > 0) {
            const firstKey = keys[0];
            const firstValue = data[firstKey];
            const msg = Array.isArray(firstValue) ? firstValue[0] : firstValue;
            
            // Make it user-friendly
            if (typeof msg === 'string') {
              errorMessage = msg;
            } else {
              errorMessage = `${firstKey}: ${JSON.stringify(msg)}`;
            }
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      }

      console.error('📝 Final Google error:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Google OAuth Error
   */
  const handleGoogleError = () => {
    console.error('❌ Google Sign-In failed');
    setError('Google sign-in failed. Please try email login or check your internet connection.');
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1 className="logo">🔐 PrivyLock</h1>
          <h2>Welcome Back</h2>
          <p>Sign in to access your encrypted documents</p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="success-message">
            ✓ {successMessage}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {/* Email */}
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={loading}
              autoFocus
            />
          </div>

          {/* Password */}
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="password-input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={loading}
              />
              <button
                type="button"
                className="toggle-password"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {/* Forgot Password */}
          <div className="form-options">
            <Link to="/forgot-password" className="link-small">
              Forgot password?
            </Link>
          </div>

          {/* Submit Button */}
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner"></span>
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="divider">
          <span>or</span>
        </div>

        {/* Google OAuth */}
        <div className="google-signin">
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap
            text="signin_with"
            shape="rectangular"
            size="large"
            theme="outline"
            logo_alignment="left"
          />
        </div>

        {/* Register Link */}
        <div className="form-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/register" className="link">
              Sign Up
            </Link>
          </p>
        </div>
      </div>

      <div className="security-info">
        <p>
          🔒 <strong>Zero-Knowledge Encryption</strong>
          <br/>
          Your password never leaves your device.
          <br/>
          We cannot access your files - only you can.
        </p>
      </div>
    </div>
  );
};

export default Login;