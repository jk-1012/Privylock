/**
 * Register Component - COMPLETE FIX
 *
 * FIXES APPLIED:
 * ✅ Proper error extraction from backend response
 * ✅ After saving recovery key → Redirect to LOGIN page
 * ✅ Better validation error messages
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { GoogleLogin } from '@react-oauth/google';
import './Register.css';

const Register = () => {
  const navigate = useNavigate();
  const { register, googleLogin } = useAuth();

  // Form state
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Recovery key state
  const [showRecoveryKey, setShowRecoveryKey] = useState(false);
  const [recoveryKey, setRecoveryKey] = useState('');
  const [recoveryKeySaved, setRecoveryKeySaved] = useState(false);

  /**
   * Handle registration
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!email || !mobileNumber || !password || !confirmPassword) {
      setError('All fields are required');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    // Validate mobile number
    const mobileRegex = /^\+?1?\d{9,15}$/;
    if (!mobileRegex.test(mobileNumber.replace(/[\s-]/g, ''))) {
      setError('Invalid mobile number. Use country code (e.g., +911234567890)');
      return;
    }

    setLoading(true);

    try {
      console.log('📝 Registering user...');

      // Call register (NO auto-login!)
      const result = await register(email, mobileNumber, password);

      console.log('✅ Registration successful!');
      console.log('🔑 Recovery key:', result.recovery_key);

      // Show recovery key modal
      setRecoveryKey(result.recovery_key);
      setShowRecoveryKey(true);

    } catch (err) {
      console.error('❌ Registration failed:', err);
      console.error('Full error object:', err);
      console.error('Error response:', err.response);
      console.error('Error response data:', err.response?.data);
      
      let errorMessage = 'Registration failed. Please try again.';
      
      if (err.response?.data) {
        const data = err.response.data;
        console.log('📋 Error data type:', typeof data);
        console.log('📋 Error data:', data);
        
        // Handle different error formats
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.errors) {
          // Django validation errors format
          const firstKey = Object.keys(data.errors)[0];
          const firstValue = data.errors[firstKey];
          errorMessage = Array.isArray(firstValue) ? firstValue[0] : firstValue;
        } else if (data.username) {
          const msg = Array.isArray(data.username) ? data.username[0] : data.username;
          errorMessage = msg.includes('user with this email') ? 'This email is already registered' : msg;
        } else if (data.email) {
          errorMessage = Array.isArray(data.email) ? data.email[0] : data.email;
        } else if (data.mobile_number) {
          errorMessage = Array.isArray(data.mobile_number) ? data.mobile_number[0] : data.mobile_number;
        } else if (data.password) {
          errorMessage = Array.isArray(data.password) ? data.password[0] : data.password;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else {
          // Last resort - show first field error
          const keys = Object.keys(data);
          if (keys.length > 0) {
            const firstKey = keys[0];
            const firstValue = data[firstKey];
            const msg = Array.isArray(firstValue) ? firstValue[0] : firstValue;
            errorMessage = `${firstKey}: ${msg}`;
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      console.error('📝 Final error message:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle Google OAuth
   */
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setLoading(true);
      setError('');

      console.log('🌐 Google Sign-In successful');

      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google');
      }

      await googleLogin(credentialResponse.credential);

      console.log('✅ Google registration successful!');

      // Google users go directly to dashboard
      navigate('/dashboard');

    } catch (err) {
      console.error('❌ Google registration failed:', err);
      console.error('Error response data:', err.response?.data);
      
      let errorMessage = 'Google sign-in failed. Please try again.';
      
      if (err.response?.data) {
        const data = err.response.data;
        
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.mobile_number) {
          const msg = Array.isArray(data.mobile_number) ? data.mobile_number[0] : data.mobile_number;
          errorMessage = msg;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (typeof data === 'object') {
          const keys = Object.keys(data);
          if (keys.length > 0) {
            const firstKey = keys[0];
            const firstValue = data[firstKey];
            const msg = Array.isArray(firstValue) ? firstValue[0] : firstValue;
            errorMessage = typeof msg === 'string' ? msg : `${firstKey}: ${JSON.stringify(msg)}`;
          }
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleFailure = () => {
    console.error('❌ Google Sign-In error');
    setError('Google sign-in failed. Please try email registration.');
  };

  /**
   * Download recovery key
   */
  const downloadRecoveryKey = () => {
    const blob = new Blob([recoveryKey], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'privylock-recovery-key.txt';
    link.click();
    window.URL.revokeObjectURL(url);
  };

  /**
   * Copy recovery key
   */
  const copyRecoveryKey = () => {
    navigator.clipboard.writeText(recoveryKey);
    alert('Recovery key copied to clipboard!');
  };

  /**
   * Redirect to LOGIN page after saving recovery key
   */
  const confirmRecoveryKeySaved = () => {
    if (!recoveryKeySaved) {
      alert('Please confirm that you have saved your recovery key!');
      return;
    }

    console.log('✅ Recovery key saved, redirecting to login...');

    alert('Registration successful! Please check your email to verify your account, then login.');

    navigate('/login', {
      state: {
        message: 'Registration successful! Please verify your email (check inbox) and login.',
        email: email
      }
    });
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <div className="register-header">
          <h1 className="logo">🔐 PrivyLock</h1>
          <h2>Create Your Account</h2>
          <p>Join PrivyLock and secure your documents</p>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {!showRecoveryKey ? (
          <>
            <form onSubmit={handleSubmit} className="register-form">
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
                  disabled={loading}
                />
              </div>

              {/* Mobile */}
              <div className="form-group">
                <label htmlFor="mobile">Mobile Number</label>
                <input
                  type="tel"
                  id="mobile"
                  placeholder="+911234567890"
                  value={mobileNumber}
                  onChange={(e) => setMobileNumber(e.target.value)}
                  required
                  pattern="^\+?1?\d{9,15}$"
                  disabled={loading}
                />
                <small className="form-hint">
                  Include country code (e.g., +91 for India)
                </small>
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
                    minLength={8}
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
                <small className="form-hint">
                  At least 8 characters
                </small>
              </div>

              {/* Confirm Password */}
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  disabled={loading}
                />
              </div>

              {/* Submit Button */}
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
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
                onError={handleGoogleFailure}
                text="signup_with"
                shape="rectangular"
                size="large"
                theme="outline"
                logo_alignment="left"
              />
            </div>

            {/* Login Link */}
            <div className="form-footer">
              <p>
                Already have an account?{' '}
                <Link to="/login" className="link">
                  Sign In
                </Link>
              </p>
            </div>
          </>
        ) : (
          /* Recovery Key Modal */
          <div className="recovery-key-modal">
            <div className="recovery-key-icon">🔑</div>
            <h3>Save Your Recovery Key</h3>
            <p className="warning-text">
              ⚠️ <strong>CRITICAL:</strong> Save this recovery key securely.
              <br/><br/>
              <strong>We cannot recover your account without this key!</strong>
            </p>

            <div className="recovery-key-display">
              <code>{recoveryKey}</code>
            </div>

            <div className="recovery-key-actions">
              <button onClick={downloadRecoveryKey} className="btn-secondary">
                📥 Download Key
              </button>
              <button onClick={copyRecoveryKey} className="btn-secondary">
                📋 Copy to Clipboard
              </button>
            </div>

            <div className="recovery-key-confirm">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={recoveryKeySaved}
                  onChange={(e) => setRecoveryKeySaved(e.target.checked)}
                />
                <span>I have saved my recovery key safely</span>
              </label>
            </div>

            <button
              onClick={confirmRecoveryKeySaved}
              className="btn-primary"
              disabled={!recoveryKeySaved}
            >
              Continue to Login
            </button>
          </div>
        )}
      </div>

      <div className="security-info">
        <p>
          🔒 <strong>Zero-Knowledge Encryption</strong>
          <br/>
          Your documents are encrypted on your device.
          <br/>
          We cannot access your files - only you can.
        </p>
      </div>
    </div>
  );
};

export default Register;