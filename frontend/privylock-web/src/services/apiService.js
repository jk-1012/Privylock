/**
 * apiService.js - API Service for PrivyLock
 *
 * FEATURES:
 * ✅ Authentication (register, login, Google OAuth)
 * ✅ Email Verification (no mobile OTP)
 * ✅ Category Management
 * ✅ Folder Management
 * ✅ Document Management
 * ✅ Notification System
 * ✅ Auto Token Refresh
 */

import axios from 'axios';

// API Base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

class ApiService {
  constructor() {
    // Create axios instance
    this.api = axios.create({
      baseURL: `${API_URL}/api`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for token refresh
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // If 401 and not already retried, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');

            if (!refreshToken) {
              throw new Error('No refresh token available');
            }

            // Refresh token
            const response = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
              refresh: refreshToken,
            });

            const { access } = response.data;

            // Store new access token
            localStorage.setItem('access_token', access);

            // Update authorization header
            originalRequest.headers.Authorization = `Bearer ${access}`;

            // Retry original request
            return this.api(originalRequest);

          } catch (err) {
            // Refresh failed, clear storage and redirect to login
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login';
            return Promise.reject(err);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // ========================================
  // AUTHENTICATION ENDPOINTS
  // ========================================

  /**
   * Register new user
   *
   * @param {Object} data - Registration data
   * @param {string} data.username - Username hash from email
   * @param {string} data.email - Plain email address
   * @param {string} data.mobile_number - Mobile with country code
   * @param {string} data.password - Password hash
   * @param {string} data.recovery_key_hash - Recovery key hash
   * @param {string} data.device_id - Device identifier
   * @param {string} data.device_name - Device name
   * @returns {Promise}
   */
  register(data) {
    return this.api.post('/auth/register/', data);
  }

  /**
   * Login with username + password
   *
   * @param {string} username - Username hash from email
   * @param {string} password - Password hash
   * @returns {Promise}
   */
  login(username, password) {
    return this.api.post('/auth/login/', {
      username,
      password,
    });
  }

  /**
   * Login with Google OAuth
   *
   * @param {Object} data - Google login data
   * @param {string} data.google_token - Google ID token
   * @param {string} data.device_id - Device identifier
   * @param {string} data.device_name - Device name
   * @returns {Promise}
   */
  googleLogin(data) {
    return this.api.post('/auth/google/', data);
  }

  /**
   * Verify email with token
   *
   * @param {string} token - Email verification token
   * @returns {Promise}
   */
  verifyEmail(token) {
    return this.api.get(`/auth/verify-email/${token}/`);
  }

  /**
   * Resend verification email
   *
   * @param {string} email - User's email
   * @param {string} type - 'email' (mobile not supported)
   * @returns {Promise}
   */
  resendVerification(email, type = 'email') {
    return this.api.post('/auth/resend-verification/', {
      email,
      type,
    });
  }

  /**
   * Get current user info
   *
   * @returns {Promise}
   */
  getUserInfo() {
    return this.api.get('/auth/me/');
  }

  /**
   * Refresh access token
   *
   * @param {string} refreshToken - Refresh token
   * @returns {Promise}
   */
  refreshToken(refreshToken) {
    return axios.post(`${API_URL}/api/auth/token/refresh/`, {
      refresh: refreshToken,
    });
  }

  // ========================================
  // CATEGORY ENDPOINTS
  // ========================================

  /**
   * Get all categories
   *
   * @returns {Promise}
   */
  getCategories() {
    return this.api.get('/vault/categories/');
  }

  /**
   * Get category by ID
   *
   * @param {string} id - Category UUID
   * @returns {Promise}
   */
  getCategory(id) {
    return this.api.get(`/vault/categories/${id}/`);
  }

  // ========================================
  // FOLDER ENDPOINTS
  // ========================================

  /**
   * Get folders
   *
   * @param {string} categoryId - Optional category UUID to filter by
   * @returns {Promise}
   */
  getFolders(categoryId = null) {
    const params = categoryId ? { category: categoryId } : {};
    return this.api.get('/vault/folders/', { params });
  }

  /**
   * Get folder by ID
   *
   * @param {string} id - Folder UUID
   * @returns {Promise}
   */
  getFolder(id) {
    return this.api.get(`/vault/folders/${id}/`);
  }

  /**
   * Create new folder
   *
   * @param {Object} data - Folder data
   * @param {string} data.encrypted_name - Encrypted folder name
   * @param {string} data.category - Category UUID
   * @param {string} data.parent_folder - Optional parent folder UUID
   * @returns {Promise}
   */
  createFolder(data) {
    return this.api.post('/vault/folders/', data);
  }

  /**
   * Update folder
   *
   * @param {string} id - Folder UUID
   * @param {Object} data - Updated folder data
   * @returns {Promise}
   */
  updateFolder(id, data) {
    return this.api.patch(`/vault/folders/${id}/`, data);
  }

  /**
   * Delete folder
   *
   * @param {string} id - Folder UUID
   * @returns {Promise}
   */
  deleteFolder(id) {
    return this.api.delete(`/vault/folders/${id}/`);
  }

  /**
   * Get folder tree (hierarchical structure)
   *
   * @param {string} id - Folder UUID
   * @returns {Promise}
   */
  getFolderTree(id) {
    return this.api.get(`/vault/folders/${id}/tree/`);
  }

  // ========================================
  // DOCUMENT ENDPOINTS
  // ========================================

  /**
   * Get documents
   *
   * @param {Object} params - Query parameters
   * @param {string} params.folder - Filter by folder UUID
   * @param {string} params.category - Filter by category UUID
   * @param {string} params.search - Search query
   * @returns {Promise}
   */
  getDocuments(params = {}) {
    return this.api.get('/vault/documents/', { params });
  }

  /**
   * Get document by ID
   *
   * @param {string} id - Document UUID
   * @returns {Promise}
   */
  getDocument(id) {
    return this.api.get(`/vault/documents/${id}/`);
  }

  /**
   * Upload new document
   *
   * @param {FormData} formData - Form data with encrypted file and metadata
   * @returns {Promise}
   */
  uploadDocument(formData) {
    return this.api.post('/vault/documents/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * Update document metadata
   *
   * @param {string} id - Document UUID
   * @param {Object} data - Updated document data
   * @returns {Promise}
   */
  updateDocument(id, data) {
    return this.api.patch(`/vault/documents/${id}/`, data);
  }

  /**
   * Delete document
   *
   * @param {string} id - Document UUID
   * @returns {Promise}
   */
  deleteDocument(id) {
    return this.api.delete(`/vault/documents/${id}/`);
  }

  /**
   * Download document (encrypted file)
   *
   * @param {string} id - Document UUID
   * @returns {Promise}
   */
  downloadDocument(id) {
    return this.api.get(`/vault/documents/${id}/download/`, {
      responseType: 'blob',
    });
  }

  /**
   * Move documents to folder
   *
   * @param {Array<string>} documentIds - Array of document UUIDs
   * @param {string} folderId - Target folder UUID
   * @returns {Promise}
   */
  moveDocuments(documentIds, folderId) {
    return this.api.post('/vault/documents/move/', {
      document_ids: documentIds,
      folder_id: folderId,
    });
  }

  // ========================================
  // NOTIFICATION ENDPOINTS
  // ========================================

  /**
   * Get notifications
   *
   * @param {Object} params - Query parameters
   * @param {boolean} params.unread_only - Filter for unread only
   * @param {string} params.notification_type - Filter by type
   * @param {string} params.priority - Filter by priority
   * @returns {Promise}
   */
  getNotifications(params = {}) {
    return this.api.get('/notifications/', { params });
  }

  /**
   * Get single notification
   *
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  getNotification(id) {
    return this.api.get(`/notifications/${id}/`);
  }

  /**
   * Mark notification as read
   *
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  markNotificationRead(id) {
    return this.api.patch(`/notifications/${id}/`, {
      is_read: true
    });
  }

  /**
   * Mark notification as unread
   *
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  markNotificationUnread(id) {
    return this.api.patch(`/notifications/${id}/`, {
      is_read: false
    });
  }

  /**
   * Mark multiple notifications as read
   *
   * @param {Array<string>} notificationIds - Array of notification UUIDs
   * @returns {Promise}
   */
  markNotificationsRead(notificationIds) {
    return this.api.post('/notifications/mark_read/', {
      notification_ids: notificationIds
    });
  }

  /**
   * Mark all notifications as read
   *
   * @returns {Promise}
   */
  markAllNotificationsRead() {
    return this.api.post('/notifications/mark_all_read/');
  }

  /**
   * Delete notification
   *
   * @param {string} id - Notification UUID
   * @returns {Promise}
   */
  deleteNotification(id) {
    return this.api.delete(`/notifications/${id}/`);
  }

  /**
   * Delete all read notifications
   *
   * @returns {Promise}
   */
  deleteAllReadNotifications() {
    return this.api.delete('/notifications/delete_all_read/');
  }

  /**
   * Get unread notification count
   *
   * @returns {Promise}
   */
  getUnreadNotificationCount() {
    return this.api.get('/notifications/unread_count/');
  }

  /**
   * Get notification preferences
   *
   * @returns {Promise}
   */
  getNotificationPreferences() {
    return this.api.get('/notifications/preferences/');
  }

  /**
   * Update notification preferences
   *
   * @param {Object} data - Preference data
   * @returns {Promise}
   */
  updateNotificationPreferences(data) {
    return this.api.put('/notifications/preferences/', data);
  }

  // ========================================
  // GENERIC HTTP METHODS
  // ========================================

  /**
   * Generic GET request
   *
   * @param {string} url - URL path
   * @param {Object} config - Axios config
   * @returns {Promise}
   */
  get(url, config = {}) {
    return this.api.get(url, config);
  }

  /**
   * Generic POST request
   *
   * @param {string} url - URL path
   * @param {Object} data - Request data
   * @param {Object} config - Axios config
   * @returns {Promise}
   */
  post(url, data, config = {}) {
    return this.api.post(url, data, config);
  }

  /**
   * Generic PUT request
   *
   * @param {string} url - URL path
   * @param {Object} data - Request data
   * @param {Object} config - Axios config
   * @returns {Promise}
   */
  put(url, data, config = {}) {
    return this.api.put(url, data, config);
  }

  /**
   * Generic PATCH request
   *
   * @param {string} url - URL path
   * @param {Object} data - Request data
   * @param {Object} config - Axios config
   * @returns {Promise}
   */
  patch(url, data, config = {}) {
    return this.api.patch(url, data, config);
  }

  /**
   * Generic DELETE request
   *
   * @param {string} url - URL path
   * @param {Object} config - Axios config
   * @returns {Promise}
   */
  delete(url, config = {}) {
    return this.api.delete(url, config);
  }
}

// Export singleton instance
export default new ApiService();