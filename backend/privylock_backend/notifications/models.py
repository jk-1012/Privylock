"""
Notification Models for PrivyLock
Complete notification system with encrypted content
"""

from django.db import models
from django.utils import timezone
import uuid


class Notification(models.Model):
    """
    User notifications with encrypted content

    Supports:
    - Document expiry alerts (30, 15, 7, 1 days before)
    - Storage warnings
    - Security alerts
    - System notifications
    """

    # Notification Types
    DOCUMENT_EXPIRY = 'DOCUMENT_EXPIRY'
    DOCUMENT_EXPIRED = 'DOCUMENT_EXPIRED'
    STORAGE_WARNING = 'STORAGE_WARNING'
    STORAGE_CRITICAL = 'STORAGE_CRITICAL'
    SECURITY_ALERT = 'SECURITY_ALERT'
    NEW_DEVICE_LOGIN = 'NEW_DEVICE_LOGIN'
    SYSTEM = 'SYSTEM'

    NOTIFICATION_TYPES = [
        (DOCUMENT_EXPIRY, 'Document Expiry Alert'),
        (DOCUMENT_EXPIRED, 'Document Expired'),
        (STORAGE_WARNING, 'Storage Warning'),
        (STORAGE_CRITICAL, 'Storage Critical'),
        (SECURITY_ALERT, 'Security Alert'),
        (NEW_DEVICE_LOGIN, 'New Device Login'),
        (SYSTEM, 'System Notification'),
    ]

    # Priority Levels
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'

    PRIORITY_LEVELS = [
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
        (CRITICAL, 'Critical'),
    ]

    # Fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # Type and priority
    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default=MEDIUM,
        db_index=True
    )

    # Encrypted content
    encrypted_title = models.BinaryField()
    encrypted_body = models.BinaryField()

    # Related document (if any)
    document = models.ForeignKey(
        'vault.Document',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Related device (for security alerts)
    device = models.ForeignKey(
        'users.Device',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    # Status tracking
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Email notification status
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    # Push notification status
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)

    # Action URL (for clickable notifications)
    action_url = models.CharField(max_length=500, null=True, blank=True)

    # Expiry tracking (auto-delete old notifications)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"{self.notification_type} - User {self.user.username}"

    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def mark_email_sent(self):
        """Mark email as sent"""
        if not self.email_sent:
            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save(update_fields=['email_sent', 'email_sent_at'])

    def mark_push_sent(self):
        """Mark push notification as sent"""
        if not self.push_sent:
            self.push_sent = True
            self.push_sent_at = timezone.now()
            self.save(update_fields=['push_sent', 'push_sent_at'])

    @property
    def is_expired(self):
        """Check if notification has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for user"""
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def delete_expired(cls):
        """Delete expired notifications (for cleanup task)"""
        expired = cls.objects.filter(
            expires_at__lt=timezone.now()
        )
        count = expired.count()
        expired.delete()
        return count


class NotificationPreference(models.Model):
    """
    User preferences for notifications
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )

    # In-app notifications (always enabled)
    in_app_enabled = models.BooleanField(default=True)

    # Email notifications
    email_enabled = models.BooleanField(default=True)
    email_expiry_alerts = models.BooleanField(default=True)
    email_storage_alerts = models.BooleanField(default=True)
    email_security_alerts = models.BooleanField(default=True)

    # Push notifications (browser)
    push_enabled = models.BooleanField(default=True)
    push_expiry_alerts = models.BooleanField(default=True)
    push_storage_alerts = models.BooleanField(default=True)
    push_security_alerts = models.BooleanField(default=True)

    # Expiry alert timing (days before expiry)
    alert_30_days = models.BooleanField(default=True)
    alert_15_days = models.BooleanField(default=True)
    alert_7_days = models.BooleanField(default=True)
    alert_1_day = models.BooleanField(default=True)
    alert_on_expiry = models.BooleanField(default=True)

    # Storage alert thresholds
    storage_warning_threshold = models.IntegerField(default=80)  # 80%
    storage_critical_threshold = models.IntegerField(default=95)  # 95%

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notification_preferences'

    def __str__(self):
        return f"Preferences for {self.user.username}"

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get or create preferences for user"""
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs