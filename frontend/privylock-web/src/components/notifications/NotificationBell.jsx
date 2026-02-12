/**
 * NotificationBell Component
 *
 * Bell icon with unread count badge
 * Toggles notification panel on click
 */

import React, { useState, useEffect, useRef } from 'react';
import apiService from '../../services/apiService';
import encryptionService from '../../services/encryptionService';
import NotificationPanel from './NotificationPanel';
import './NotificationBell.css';

const NotificationBell = () => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [showPanel, setShowPanel] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const bellRef = useRef(null);
  const panelRef = useRef(null);

  // Fetch unread count on mount and every 30 seconds
  useEffect(() => {
    fetchUnreadCount();

    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, []);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        bellRef.current &&
        !bellRef.current.contains(event.target) &&
        panelRef.current &&
        !panelRef.current.contains(event.target)
      ) {
        setShowPanel(false);
      }
    };

    if (showPanel) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPanel]);

  /**
   * Fetch unread notification count
   */
  const fetchUnreadCount = async () => {
    try {
      const response = await apiService.getUnreadCount();
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  /**
   * Fetch all notifications
   */
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await apiService.getNotifications({
        unread_only: false
      });

      // Decrypt notifications
      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        console.error('No master key found');
        setLoading(false);
        return;
      }

      const decryptedNotifications = await Promise.all(
        response.data.map(async (notif) => {
          try {
            // Decrypt title and body
            const title = await encryptionService.decryptBase64Text(
              notif.encrypted_title,
              masterKey
            );
            const body = await encryptionService.decryptBase64Text(
              notif.encrypted_body,
              masterKey
            );

            return {
              ...notif,
              title,
              body
            };
          } catch (error) {
            console.error('Failed to decrypt notification:', error);
            return {
              ...notif,
              title: 'Encrypted',
              body: 'Unable to decrypt notification'
            };
          }
        })
      );

      setNotifications(decryptedNotifications);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      setLoading(false);
    }
  };

  /**
   * Toggle notification panel
   */
  const handleBellClick = () => {
    if (!showPanel) {
      // Opening panel - fetch notifications
      fetchNotifications();
    }
    setShowPanel(!showPanel);
  };

  /**
   * Handle notification read
   */
  const handleNotificationRead = async (notificationId) => {
    try {
      await apiService.markNotificationRead(notificationId);

      // Update local state
      setNotifications(notifications.map(notif =>
        notif.id === notificationId
          ? { ...notif, is_read: true }
          : notif
      ));

      // Update unread count
      fetchUnreadCount();
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  /**
   * Handle mark all as read
   */
  const handleMarkAllRead = async () => {
    try {
      await apiService.markAllNotificationsRead();

      // Update local state
      setNotifications(notifications.map(notif => ({
        ...notif,
        is_read: true
      })));

      // Update unread count
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  /**
   * Handle notification delete
   */
  const handleNotificationDelete = async (notificationId) => {
    try {
      await apiService.deleteNotification(notificationId);

      // Update local state
      setNotifications(notifications.filter(notif => notif.id !== notificationId));

      // Update unread count
      fetchUnreadCount();
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  /**
   * Handle delete all read
   */
  const handleDeleteAllRead = async () => {
    try {
      await apiService.deleteAllReadNotifications();

      // Update local state - keep only unread
      setNotifications(notifications.filter(notif => !notif.is_read));
    } catch (error) {
      console.error('Failed to delete all read:', error);
    }
  };

  return (
    <>
      <div
        className="notification-bell-container"
        ref={bellRef}
        onClick={handleBellClick}
      >
        <div className={`notification-bell ${showPanel ? 'active' : ''}`}>
          {/* Bell Icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="bell-icon"
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>

          {/* Unread Badge */}
          {unreadCount > 0 && (
            <span className="notification-badge">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </div>
      </div>

      {/* Notification Panel */}
      {showPanel && (
        <div ref={panelRef}>
          <NotificationPanel
            notifications={notifications}
            loading={loading}
            onNotificationRead={handleNotificationRead}
            onNotificationDelete={handleNotificationDelete}
            onMarkAllRead={handleMarkAllRead}
            onDeleteAllRead={handleDeleteAllRead}
            onClose={() => setShowPanel(false)}
          />
        </div>
      )}
    </>
  );
};

export default NotificationBell;