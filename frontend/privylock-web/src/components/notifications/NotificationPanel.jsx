/**
 * NotificationPanel Component
 *
 * Dropdown panel showing list of notifications
 */

import React from 'react';
import NotificationItem from './NotificationItem';

const NotificationPanel = ({
  notifications,
  loading,
  onNotificationRead,
  onNotificationDelete,
  onMarkAllRead,
  onDeleteAllRead,
  onClose
}) => {
  const unreadNotifications = notifications.filter(n => !n.is_read);
  const hasUnread = unreadNotifications.length > 0;
  const hasRead = notifications.some(n => n.is_read);

  return (
    <div className="notification-panel">
      {/* Header */}
      <div className="notification-panel-header">
        <h3>Notifications</h3>

        <div className="notification-panel-actions">
          {hasUnread && (
            <button
              className="btn-text"
              onClick={onMarkAllRead}
              title="Mark all as read"
            >
              Mark all read
            </button>
          )}
          {hasRead && (
            <button
              className="btn-text"
              onClick={onDeleteAllRead}
              title="Clear read notifications"
            >
              Clear read
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="notification-panel-content">
        {loading ? (
          // Loading State
          <div className="notification-loading">
            <div className="spinner"></div>
            <p>Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          // Empty State
          <div className="notification-empty">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="empty-icon"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <p>No notifications</p>
            <span>You're all caught up!</span>
          </div>
        ) : (
          // Notification List
          <div className="notification-list">
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onRead={() => onNotificationRead(notification.id)}
                onDelete={() => onNotificationDelete(notification.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="notification-panel-footer">
          <button
            className="btn-view-all"
            onClick={onClose}
          >
            View all notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationPanel;