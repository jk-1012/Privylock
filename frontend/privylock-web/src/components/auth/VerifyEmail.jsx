/**
 * Email Verification Component - FOR PRIVYLOCK
 *
 * This component handles email verification when users click the link
 * from their verification email.
 *
 * Flow:
 * 1. User receives email with verification link
 * 2. Link contains token: /verify-email/{token}
 * 3. This component extracts token from URL
 * 4. Sends token to backend for verification
 * 5. Shows success/error message
 * 6. Redirects to login after 3 seconds
 *
 * FEATURES:
 * ✅ Automatic token extraction from URL
 * ✅ Loading state during verification
 * ✅ Success/error messages
 * ✅ Auto-redirect to login
 * ✅ Resend verification option
 * ✅ PrivyLock branding
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import apiService from '../../services/apiService';
import './VerifyEmail.css';

const VerifyEmail = () => {
  const { token } = useParams(); // Extract token from URL
  const navigate = useNavigate();

  const [status, setStatus] = useState('verifying'); // verifying | success | error
  const [message, setMessage] = useState('Verifying your email...');
  const [countdown, setCountdown] = useState(3);
  const [resendEmail, setResendEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState('');

  useEffect(() => {
    if (token) {
      verifyEmail(token);
    } else {
      setStatus('error');
      setMessage('Invalid verification link. No token provided.');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    // Auto-redirect countdown
    if (status === 'success' && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);

      return () => clearTimeout(timer);
    }

    if (status === 'success' && countdown === 0) {
      navigate('/login');
    }
  }, [status, countdown, navigate]);

  /**
   * Verify email with token
   */
  const verifyEmail = async (verificationToken) => {
    try {
      console.log('📧 Verifying email with token:', verificationToken);

      const response = await apiService.verifyEmail(verificationToken);

      console.log('✅ Email verified:', response.data);

      setStatus('success');
      setMessage(`Email verified successfully! You can now log in to PrivyLock.`);

    } catch (error) {
      console.error('❌ Email verification failed:', error);

      setStatus('error');

      if (error.response?.data?.errors?.token) {
        setMessage(error.response.data.errors.token[0]);
      } else if (error.response?.data?.error) {
        setMessage(error.response.data.error);
      } else {
        setMessage('Email verification failed. The link may be expired or invalid.');
      }
    }
  };

  /**
   * Resend verification email
   */
  const handleResend = async (e) => {
    e.preventDefault();

    if (!resendEmail) {
      setResendMessage('Please enter your email address');
      return;
    }

    try {
      setResendLoading(true);
      setResendMessage('');

      console.log('📧 Resending verification to:', resendEmail);

      await apiService.resendVerification(resendEmail);

      console.log('✅ Verification email resent');

      setResendMessage('Verification email sent! Please check your inbox.');
      setResendEmail('');

    } catch (error) {
      console.error('❌ Resend failed:', error);

      if (error.response?.data?.errors?.email) {
        setResendMessage(error.response.data.errors.email[0]);
      } else if (error.response?.data?.error) {
        setResendMessage(error.response.data.error);
      } else {
        setResendMessage('Failed to resend verification email. Please try again.');
      }
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="verify-email-page">
      <div className="verify-email-container">
        <div className="verify-email-card">
          {/* Header */}
          <div className="verify-email-header">
            <h1>🔐 PrivyLock</h1>
            <h2>Email Verification</h2>
          </div>

          {/* Status Display */}
          <div className="verify-email-content">
            {status === 'verifying' && (
              <div className="verify-status verifying">
                <div className="loading-spinner"></div>
                <p>{message}</p>
              </div>
            )}

            {status === 'success' && (
              <div className="verify-status success">
                <div className="success-icon">✓</div>
                <h3>Email Verified!</h3>
                <p>{message}</p>
                <p className="redirect-message">
                  Redirecting to login in {countdown} second{countdown !== 1 ? 's' : ''}...
                </p>
                <Link to="/login" className="btn-primary">
                  Go to Login Now
                </Link>
              </div>
            )}

            {status === 'error' && (
              <div className="verify-status error">
                <div className="error-icon">✗</div>
                <h3>Verification Failed</h3>
                <p>{message}</p>

                {/* Resend Form */}
                <div className="resend-section">
                  <p className="resend-text">
                    Need a new verification link?
                  </p>

                  <form onSubmit={handleResend} className="resend-form">
                    <input
                      type="email"
                      placeholder="Enter your email"
                      value={resendEmail}
                      onChange={(e) => setResendEmail(e.target.value)}
                      disabled={resendLoading}
                      required
                    />

                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={resendLoading}
                    >
                      {resendLoading ? 'Sending...' : 'Resend Verification'}
                    </button>
                  </form>

                  {resendMessage && (
                    <p className={`resend-message ${resendMessage.includes('sent') ? 'success' : 'error'}`}>
                      {resendMessage}
                    </p>
                  )}
                </div>

                <Link to="/login" className="btn-secondary">
                  Back to Login
                </Link>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="verify-email-footer">
            <p>
              Need help? <a href="mailto:support@privylock.com">Contact Support</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;