/**
 * AuthContext.js - COMPLETE FIXED VERSION
 *
 * ✅ PRODUCTION READY - ESLint compliant
 * ✅ FIXED: Removed unused saltHex variable in register function
 * FIXES APPLIED:
 * ✅ Proper Google OAuth error handling (no [object Object])
 * ✅ Google users get deterministic master key (email-based)
 * ✅ Registration flow fixed
 * ✅ Login flow fixed
 * ✅ Comprehensive error extraction
 */

import React, { createContext, useState, useContext, useEffect } from 'react';
import apiService from '../services/apiService';
import encryptionService from '../services/encryptionService';

// Create context
const AuthContext = createContext();

/**
 * Hook to use AuthContext
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

/**
 * ✅ HELPER: Extract error message from various error formats
 * Prevents [object Object] by properly extracting error strings
 */
const extractErrorMessage = (error, defaultMessage = 'An error occurred') => {
  console.log('🔍 Extracting error from:', error);

  // 1. Check Axios response data (most common)
  if (error.response?.data) {
    const data = error.response.data;

    // String error
    if (typeof data === 'string') {
      return data;
    }

    // Common backend error fields
    if (data.error) return data.error;
    if (data.message) return data.message;
    if (data.detail) return data.detail;

    // Django REST Framework validation errors
    if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
      return data.non_field_errors.join(', ');
    }

    // Field-specific errors
    if (typeof data === 'object') {
      const firstError = Object.values(data)[0];
      if (Array.isArray(firstError)) {
        return firstError[0]; // First error message
      }
      if (typeof firstError === 'string') {
        return firstError;
      }
    }
  }

  // 2. Check standard error message
  if (error.message && error.message !== 'Network Error') {
    return error.message;
  }

  // 3. HTTP status-based messages
  if (error.response?.status) {
    switch (error.response.status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 401:
        return 'Invalid credentials. Please try again.';
      case 403:
        return 'Access denied. Please verify your email first.';
      case 404:
        return 'Account not found. Please register first.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return defaultMessage;
    }
  }

  // 4. String error
  if (typeof error === 'string') {
    return error;
  }

  // 5. Fallback
  return defaultMessage;
};

/**
 * AuthProvider Component
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Check authentication status on mount
   */
  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Check if user is authenticated
   */
  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const masterKey = sessionStorage.getItem('masterKey');

      if (!token || !masterKey) {
        setLoading(false);
        return;
      }

      // Get user info from backend
      const response = await apiService.getUserInfo();
      setUser(response.data);

      console.log('✅ User authenticated:', response.data.email);

    } catch (error) {
      console.error('❌ Auth check failed:', error);
      // Clear invalid tokens
      localStorage.clear();
      sessionStorage.clear();
    } finally {
      setLoading(false);
    }
  };

  /**
   * Register new user
   *
   * ✅ NO AUTO-LOGIN! User must verify email and login manually.
   * ✅ FIXED: Removed unused saltHex variable
   */
  const register = async (email, mobileNumber, password) => {
    try {
      setError(null);
      console.log('📝 Starting registration...');

      // Normalize email
      const normalizedEmail = email.toLowerCase().trim();

      // Generate username from email hash
      const emailHash = await encryptionService.hashPassword(normalizedEmail);
      const username = emailHash.substring(0, 30);

      console.log('🔐 Username generated from email');

      // Hash password
      const passwordHash = await encryptionService.hashPassword(password);

      // Generate recovery key
      const recoveryKey = encryptionService.generateRecoveryKey();
      const recoveryKeyHash = await encryptionService.hashPassword(recoveryKey);

      // Device info
      const deviceId = encryptionService.generateDeviceId();
      const deviceName = encryptionService.getDeviceName();

      // Registration data
      const registrationData = {
        username: username,
        email: normalizedEmail,
        mobile_number: mobileNumber,
        password: passwordHash,
        recovery_key_hash: recoveryKeyHash,
        device_id: deviceId,
        device_name: deviceName,
      };

      console.log('📤 Sending registration request...');
      const response = await apiService.register(registrationData);
      console.log('✅ Registration successful!');

      // ✅ DO NOT auto-login!
      return {
        success: true,
        user_id: response.data.user_id,
        recovery_key: recoveryKey,
        email_verified: response.data.email_verified || false,
        mobile_verified: response.data.mobile_verified || true,
        message: response.data.message || 'Registration successful. Please verify your email to login.',
      };

    } catch (error) {
      console.error('❌ Registration failed:', error);
      const errorMessage = extractErrorMessage(error, 'Registration failed');
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  /**
   * Login with email + password
   */
  const login = async (email, password) => {
    try {
      setError(null);
      console.log('🔐 Starting login...');

      // Normalize email
      const normalizedEmail = email.toLowerCase().trim();

      // Generate salt from email
      const emailHash = await encryptionService.hashPassword(normalizedEmail);
      const saltHex = emailHash.substring(0, 32);
      const saltBytes = encryptionService.hexToUint8Array(saltHex);

      console.log('🔐 Salt generated from email');

      // Derive master key
      console.log('🔑 Deriving master key...');
      const masterKey = await encryptionService.deriveMasterKey(password, saltBytes);
      console.log('✅ Master key derived');

      // Generate username
      const username = emailHash.substring(0, 30);

      // Hash password
      const passwordHash = await encryptionService.hashPassword(password);

      // Send login request
      console.log('📤 Sending login request...');
      const response = await apiService.login(username, passwordHash);
      console.log('✅ Login API successful!');

      // Store tokens
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      console.log('💾 Tokens stored');

      // ✅ CRITICAL: Store master key
      encryptionService.storeMasterKey(masterKey);
      sessionStorage.setItem('salt', btoa(saltHex));
      console.log('🔑 Master key stored');

      // Fetch user info
      console.log('📥 Fetching user info...');
      const userInfo = await apiService.getUserInfo();
      setUser(userInfo.data);
      console.log('✅ User loaded:', userInfo.data.email);

      return { success: true };

    } catch (error) {
      console.error('❌ Login failed:', error);
      const errorMessage = extractErrorMessage(error, 'Invalid email or password');
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  /**
   * ✅ FIXED: Google OAuth Login
   *
   * Now generates deterministic master key from Google email
   * This allows cross-device access (same email = same key)
   */
  const googleLogin = async (googleToken) => {
    try {
      setError(null);
      console.log('🌐 Starting Google OAuth login...');

      const deviceId = encryptionService.generateDeviceId();
      const deviceName = encryptionService.getDeviceName();

      // Send to backend
      console.log('📤 Sending Google token to backend...');
      const response = await apiService.googleLogin({
        google_token: googleToken,
        device_id: deviceId,
        device_name: deviceName,
      });

      console.log('✅ Google login API successful!');

      // Store tokens
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      console.log('💾 Tokens stored');

      // ✅ FIXED: Generate deterministic master key from Google email
      // This ensures same key on all devices for the same Google account
      const userEmail = response.data.user.email;
      const normalizedEmail = userEmail.toLowerCase().trim();

      // Generate salt from email (same as password login)
      const emailHash = await encryptionService.hashPassword(normalizedEmail);
      const saltHex = emailHash.substring(0, 32);
      const saltBytes = encryptionService.hexToUint8Array(saltHex);

      // Derive master key using email as "password"
      // This is deterministic: same email always produces same key
      const masterKey = await encryptionService.deriveMasterKey(normalizedEmail, saltBytes);

      // Store master key
      encryptionService.storeMasterKey(masterKey);
      sessionStorage.setItem('salt', btoa(saltHex));
      console.log('🔑 Master key derived from Google email');

      // Set user
      setUser(response.data.user);
      console.log('✅ Google login complete:', userEmail);

      return {
        success: true,
        is_new_user: response.data.is_new_user
      };

    } catch (error) {
      console.error('❌ Google login failed:', error);
      console.error('Full error:', JSON.stringify(error, null, 2));

      // ✅ FIXED: Proper error extraction
      const errorMessage = extractErrorMessage(error, 'Google sign-in failed');
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  /**
   * Verify email
   */
  const verifyEmail = async (token) => {
    try {
      console.log('📧 Verifying email...');
      const response = await apiService.verifyEmail(token);
      console.log('✅ Email verified!');

      return {
        success: true,
        message: response.data.message || 'Email verified! You can now login.'
      };

    } catch (error) {
      console.error('❌ Email verification failed:', error);
      const errorMessage = extractErrorMessage(error, 'Email verification failed');
      throw new Error(errorMessage);
    }
  };

  /**
   * Resend verification email
   */
  const resendVerification = async (email) => {
    try {
      console.log('📧 Resending verification email...');
      await apiService.resendVerification(email, 'email');
      console.log('✅ Verification email sent!');
      return { success: true };

    } catch (error) {
      console.error('❌ Failed to resend verification:', error);
      const errorMessage = extractErrorMessage(error, 'Failed to resend verification');
      throw new Error(errorMessage);
    }
  };

  /**
   * Logout user
   */
  const logout = () => {
    console.log('👋 Logging out...');
    localStorage.clear();
    sessionStorage.clear();
    encryptionService.clearKeys();
    setUser(null);
    setError(null);
    console.log('✅ Logged out');
  };

  /**
   * Clear error
   */
  const clearError = () => {
    setError(null);
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    register,
    login,
    googleLogin,
    verifyEmail,
    resendVerification,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;