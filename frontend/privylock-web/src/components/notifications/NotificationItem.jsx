/**
 * NotificationItem Component
 *
 * Individual notification in the list
 */

import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const NotificationItem = ({ notification, onRead, onDelete }) => {
  /**
   * Get icon for notification type
   */
  const getNotificationIcon = () => {
    switch (notification.notification_type) {
      case 'DOCUMENT_EXPIRY':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
        );

      case 'DOCUMENT_EXPIRED':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        );

      case 'STORAGE_WARNING':
      case 'STORAGE_CRITICAL':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
        );

      case 'SECURITY_ALERT':
      case 'NEW_DEVICE_LOGIN':
        return (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        );

      case 'SYSTEM':
      default:
        return (
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        );
    }
  };

  /**
   * Get CSS class for priority
   */
  const getPriorityClass = () => {
    switch (notification.priority) {
      case 'CRITICAL':
        return 'priority-critical';
      case 'HIGH':
        return 'priority-high';
      case 'MEDIUM':
        return 'priority-medium';
      case 'LOW':
        return 'priority-low';
      default:
        return '';
    }
  };

  /**
   * Get time ago string
   */
  const getTimeAgo = () => {
    try {
      return formatDistanceToNow(new Date(notification.created_at), {
        addSuffix: true
      });
    } catch (error) {
      return 'Recently';
    }
  };

  /**
   * Handle notification click
   */
  const handleClick = () => {
    if (!notification.is_read) {
      onRead();
    }

    // Navigate to action URL if exists
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  return (
    <div
      className={`notification-item ${notification.is_read ? 'read' : 'unread'} ${getPriorityClass()}`}
      onClick={handleClick}
    >
      {/* Icon */}
      <div className="notification-icon">
        {getNotificationIcon()}
      </div>

      {/* Content */}
      <div className="notification-content">
        <div className="notification-header">
          <h4 className="notification-title">{notification.title}</h4>
          <span className="notification-time">{getTimeAgo()}</span>
        </div>

        <p className="notification-body">{notification.body}</p>

        {/* Document reference */}
        {notification.document_id && (
          <div className="notification-reference">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span>Related document</span>
          </div>
        )}

        {/* Device reference */}
        {notification.device_id && notification.device_name && (
          <div className="notification-reference">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
              <line x1="12" y1="18" x2="12.01" y2="18" />
            </svg>
            <span>{notification.device_name}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="notification-actions">
        {!notification.is_read && (
          <button
            className="btn-icon"
            onClick={(e) => {
              e.stopPropagation();
              onRead();
            }}
            title="Mark as read"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </button>
        )}

        <button
          className="btn-icon btn-delete"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          title="Delete"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>

      {/* Unread indicator */}
      {!notification.is_read && (
        <div className="unread-indicator"></div>
      )}
    </div>
  );
};

export default NotificationItem;