"""
Notification utility functions for PrivyLock
FINAL CORRECT VERSION - Stores unencrypted text as bytes (will be encrypted by frontend)

IMPORTANT ARCHITECTURE NOTE:
- Backend creates notifications with PLAIN TEXT stored as bytes
- Frontend receives Base64-encoded bytes
- Frontend decodes Base64 to get plain text (no master key decryption needed)
- This is simpler than encrypting on backend (which would require master key on server)

Why this approach?
1. Zero-knowledge: Server never has master key
2. Notifications are generic ("Document expiring") - not sensitive
3. User authentication ensures only user sees their notifications
4. Sensitive document details remain encrypted in vault
"""
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


class NotificationCreator:
    """
    Helper class for creating notifications in PrivyLock.

    Creates notifications with plain text stored as bytes.
    Frontend will decode from Base64 (no encryption/decryption needed).
    """

    @staticmethod
    def create_expiry_alert(user, document, days_until_expiry):
        """
        Create a document expiry notification.

        Args:
            user: User instance
            document: Document instance
            days_until_expiry: Integer (positive for future, negative for past)

        Returns:
            Notification instance
        """
        # Generate notification text based on expiry status
        if days_until_expiry > 0:
            title = "Document Expiring Soon"
            body = f"Your document will expire in {days_until_expiry} days."
            notification_type = 'EXPIRY_ALERT'
        elif days_until_expiry == 0:
            title = "Document Expires Today"
            body = "Your document expires today. Please renew if needed."
            notification_type = 'EXPIRY_ALERT'
        else:
            title = "Document Expired"
            body = f"Your document expired {abs(days_until_expiry)} days ago."
            notification_type = 'EXPIRY_ALERT'

        # Store as plain text bytes
        # Frontend will decode Base64 → plain text (no encryption involved)
        encrypted_title = title.encode('utf-8')
        encrypted_body = body.encode('utf-8')

        # Set priority based on urgency
        if days_until_expiry <= 1:
            priority = 'high'
        elif days_until_expiry <= 7:
            priority = 'medium'
        else:
            priority = 'low'

        # Create notification
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            document=document,
            priority=priority
        )

        logger.info(
            f"📢 Expiry notification created: {notification.id} "
            f"for user {user.id}, document {document.id}, "
            f"days_until_expiry={days_until_expiry}"
        )

        return notification

    @staticmethod
    def create_storage_alert(user, storage_percentage):
        """
        Create a storage warning notification.

        Args:
            user: User instance
            storage_percentage: Integer (0-100)

        Returns:
            Notification instance
        """
        title = "Storage Warning"
        body = (
            f"Your storage is {storage_percentage}% full. "
            f"Consider deleting old documents or upgrading your plan."
        )

        # Store as plain text bytes
        encrypted_title = title.encode('utf-8')
        encrypted_body = body.encode('utf-8')

        # High priority if almost full
        priority = 'high' if storage_percentage >= 95 else 'medium'

        notification = Notification.objects.create(
            user=user,
            notification_type='SYSTEM',
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            priority=priority
        )

        logger.info(
            f"📢 Storage alert created: {notification.id} "
            f"for user {user.id}, storage={storage_percentage}%"
        )

        return notification

    @staticmethod
    def create_security_alert(user, alert_message, device_info=None):
        """
        Create a security alert notification.

        Args:
            user: User instance
            alert_message: String describing the security event
            device_info: Optional dict with device details

        Returns:
            Notification instance
        """
        title = "Security Alert"

        # Include device info if provided
        if device_info:
            body = f"{alert_message}\n\nDevice: {device_info.get('device', 'Unknown')}"
        else:
            body = alert_message

        # Store as plain text bytes
        encrypted_title = title.encode('utf-8')
        encrypted_body = body.encode('utf-8')

        notification = Notification.objects.create(
            user=user,
            notification_type='SECURITY_ALERT',
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            priority='high'
        )

        logger.info(
            f"📢 Security alert created: {notification.id} "
            f"for user {user.id}"
        )

        return notification

    @staticmethod
    def create_renewal_reminder(user, document, days_until_expiry):
        """
        Create a renewal reminder notification.

        Args:
            user: User instance
            document: Document instance
            days_until_expiry: Integer (days until expiry)

        Returns:
            Notification instance
        """
        title = "Renewal Reminder"
        body = (
            f"Don't forget to renew your document. "
            f"It expires in {days_until_expiry} days."
        )

        # Store as plain text bytes
        encrypted_title = title.encode('utf-8')
        encrypted_body = body.encode('utf-8')

        notification = Notification.objects.create(
            user=user,
            notification_type='RENEWAL_REMINDER',
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            document=document,
            priority='medium'
        )

        logger.info(
            f"📢 Renewal reminder created: {notification.id} "
            f"for user {user.id}, document {document.id}"
        )

        return notification

    @staticmethod
    def create_system_notification(user, title, body, priority='low'):
        """
        Create a generic system notification.

        Args:
            user: User instance
            title: Notification title
            body: Notification body
            priority: 'low', 'medium', or 'high'

        Returns:
            Notification instance
        """
        # Store as plain text bytes
        encrypted_title = title.encode('utf-8')
        encrypted_body = body.encode('utf-8')

        notification = Notification.objects.create(
            user=user,
            notification_type='SYSTEM',
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            priority=priority
        )

        logger.info(
            f"📢 System notification created: {notification.id} "
            f"for user {user.id}, priority={priority}"
        )

        return notification

    @staticmethod
    def cleanup_old_notifications(days_to_keep=30):
        """
        Delete read notifications older than specified days.

        Args:
            days_to_keep: Integer (default 30 days)

        Returns:
            Integer count of deleted notifications
        """
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            read_at__lt=cutoff_date
        ).delete()

        logger.info(
            f"🗑️ Cleaned up {deleted_count} old notifications "
            f"(older than {days_to_keep} days)"
        )

        return deleted_count

    @staticmethod
    def mark_all_read_for_user(user):
        """
        Mark all notifications as read for a specific user.

        Args:
            user: User instance

        Returns:
            Integer count of notifications marked as read
        """
        updated_count = Notification.objects.filter(
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        logger.info(
            f"✅ Marked {updated_count} notifications as read "
            f"for user {user.id}"
        )

        return updated_count

    @staticmethod
    def delete_all_read_for_user(user):
        """
        Delete all read notifications for a specific user.

        Args:
            user: User instance

        Returns:
            Integer count of deleted notifications
        """
        deleted_count, _ = Notification.objects.filter(
            user=user,
            is_read=True
        ).delete()

        logger.info(
            f"🗑️ Deleted {deleted_count} read notifications "
            f"for user {user.id}"
        )

        return deleted_count


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_storage_percentage(user):
    """
    Calculate user's storage usage percentage.

    Args:
        user: User instance

    Returns:
        Float (0-100) representing storage usage percentage
    """
    storage_limits = {
        'FREE': 1073741824,           # 1 GB
        'PREMIUM': 26843545600,       # 25 GB
        'FAMILY': 107374182400,       # 100 GB
        'LIFETIME': 10737418240,      # 10 GB
    }

    user_limit = storage_limits.get(user.subscription_tier, storage_limits['FREE'])

    if user_limit == 0:
        return 0

    percentage = (user.storage_used / user_limit) * 100
    return min(percentage, 100)  # Cap at 100%


def check_storage_alerts(user):
    """
    Check if user needs storage alerts and create them.

    Args:
        user: User instance

    Returns:
        List of created notifications
    """
    notifications = []

    # Get user's notification preferences
    try:
        from notifications.models import NotificationPreference
        prefs = NotificationPreference.objects.get(user=user)

        if not prefs.in_app_enabled:
            return notifications

    except NotificationPreference.DoesNotExist:
        # Use default settings
        prefs = None

    # Calculate storage percentage
    storage_pct = calculate_storage_percentage(user)

    # Check thresholds
    warning_threshold = prefs.storage_warning_threshold if prefs else 80
    critical_threshold = prefs.storage_critical_threshold if prefs else 95

    # Create alerts if needed
    if storage_pct >= critical_threshold:
        # Check if we already sent this alert recently
        from django.utils import timezone
        from datetime import timedelta

        recent_alert = Notification.objects.filter(
            user=user,
            notification_type='SYSTEM',
            encrypted_title__contains=b'Storage',
            created_at__gte=timezone.now() - timedelta(days=1)
        ).exists()

        if not recent_alert:
            notif = NotificationCreator.create_storage_alert(user, int(storage_pct))
            notifications.append(notif)

    elif storage_pct >= warning_threshold:
        # Check if we already sent this alert recently
        from django.utils import timezone
        from datetime import timedelta

        recent_alert = Notification.objects.filter(
            user=user,
            notification_type='SYSTEM',
            encrypted_title__contains=b'Storage',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).exists()

        if not recent_alert:
            notif = NotificationCreator.create_storage_alert(user, int(storage_pct))
            notifications.append(notif)

    return notifications


# ============================================================================
# END OF UTILS.PY
# ============================================================================