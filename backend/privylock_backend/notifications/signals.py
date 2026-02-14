"""
Notification Signals for PrivyLock
Auto-create notifications based on system events
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from vault.models import Document
from users.models import Device
from .models import Notification, NotificationPreference
from .utils import NotificationCreator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Document)
def create_expiry_notifications(sender, instance, created, **kwargs):
    """
    Create expiry notifications when document is created or updated

    Triggers:
    - Document created with expiry date
    - Document expiry date changed
    """
    if not instance.has_expiry or not instance.encrypted_expiry_date:
        return

    # Only create notifications if document was just created
    # (Scheduled task will handle ongoing expiry checks)
    if created:
        logger.info(f"📄 New document created with expiry: {instance.id}")

        # Get user preferences
        prefs = NotificationPreference.get_or_create_for_user(instance.user)

        # Create initial expiry notification (if far enough in future)
        try:
            NotificationCreator.create_expiry_alert(
                document=instance,
                user=instance.user,
                preferences=prefs
            )
        except Exception as e:
            logger.error(f"❌ Failed to create expiry notification: {str(e)}")


@receiver(post_save, sender=Device)
def create_new_device_notification(sender, instance, created, **kwargs):
    """
    Create notification when new device is registered

    Triggers:
    - New device login detected
    """
    if created:
        logger.info(f"🔐 New device login: {instance.device_name}")

        # Get user preferences
        prefs = NotificationPreference.get_or_create_for_user(instance.user)

        # Only create notification if security alerts enabled
        if not prefs.push_security_alerts and not prefs.email_security_alerts:
            logger.info("  ⏩ Security alerts disabled, skipping")
            return

        try:
            NotificationCreator.create_security_alert(
                user=instance.user,
                alert_message=f"New device login: {instance.device_name}",
                device_info={'device': instance.device_name}
            )
        except Exception as e:
            logger.error(f"❌ Failed to create device notification: {str(e)}")


@receiver(pre_save, sender=Document)
def check_expiry_date_change(sender, instance, **kwargs):
    """
    Check if expiry date was changed
    """
    if not instance.pk:
        return  # New document, not an update

    try:
        old_instance = Document.objects.get(pk=instance.pk)

        # Check if expiry date changed
        if old_instance.encrypted_expiry_date != instance.encrypted_expiry_date:
            logger.info(f"📄 Document {instance.id} expiry date changed")

            # Delete old expiry notifications
            Notification.objects.filter(
                document=instance,
                notification_type__in=[
                    Notification.DOCUMENT_EXPIRY,
                    Notification.DOCUMENT_EXPIRED
                ],
                is_read=False
            ).delete()

            logger.info("  🗑️ Deleted old expiry notifications")

    except Document.DoesNotExist:
        pass


# ========================================
# STORAGE MONITORING SIGNALS
# ========================================

def check_storage_usage(user):
    """
    Check if user storage usage exceeds thresholds
    """
    from vault.models import Document

    # Get user's storage info
    user_docs = Document.objects.filter(user=user)
    total_size = sum(doc.file_size for doc in user_docs)

    # Get user's storage limit (from subscription)
    storage_limit = user.storage_limit  # Assuming this field exists

    if storage_limit <= 0:
        return

    # Calculate usage percentage
    usage_percent = (total_size / storage_limit) * 100

    # Get user preferences
    prefs = NotificationPreference.get_or_create_for_user(user)

    # Check critical threshold
    if usage_percent >= prefs.storage_critical_threshold:
        # Check if notification already exists (don't spam)
        existing = Notification.objects.filter(
            user=user,
            notification_type=Notification.STORAGE_CRITICAL,
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=1)
        ).exists()

        if not existing:
            NotificationCreator.create_storage_alert(
                user=user,
                usage_percent=usage_percent,
                alert_type='CRITICAL',
                preferences=prefs
            )
            logger.info(f"⚠️ Created CRITICAL storage alert for {user.username}")

    # Check warning threshold
    elif usage_percent >= prefs.storage_warning_threshold:
        # Check if notification already exists
        existing = Notification.objects.filter(
            user=user,
            notification_type=Notification.STORAGE_WARNING,
            is_read=False,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).exists()

        if not existing:
            NotificationCreator.create_storage_alert(
                user=user,
                usage_percent=usage_percent,
                alert_type='WARNING',
                preferences=prefs
            )
            logger.info(f"⚠️ Created WARNING storage alert for {user.username}")


@receiver(post_save, sender=Document)
def monitor_storage_after_upload(sender, instance, created, **kwargs):
    """
    Monitor storage usage after document upload
    """
    if created:
        try:
            check_storage_usage(instance.user)
        except Exception as e:
            logger.error(f"❌ Failed to check storage: {str(e)}")