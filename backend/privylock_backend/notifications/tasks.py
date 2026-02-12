"""
Notification Tasks for PrivyLock
Background tasks for checking expiry dates and sending notifications

NOTE: This requires Celery or similar task queue
For now, these are standalone functions that can be called manually or via cron
"""

from django.utils import timezone
from datetime import timedelta
import logging

from vault.models import Document
from users.models import User
from .models import Notification, NotificationPreference
from .utils import NotificationCreator, cleanup_expired_notifications, cleanup_old_read_notifications

logger = logging.getLogger(__name__)


def check_document_expiry():
    """
    Check all documents for upcoming expiry dates
    Create notifications for documents expiring soon

    Should run daily (e.g., via cron job)

    Usage (Django management command or cron):
        python manage.py check_document_expiry
    """
    logger.info("🔍 Starting document expiry check...")

    notifications_created = 0

    # Get all documents with expiry dates
    documents = Document.objects.filter(
        has_expiry=True,
        encrypted_expiry_date__isnull=False
    )

    logger.info(f"  📄 Found {documents.count()} documents with expiry dates")

    for document in documents:
        try:
            # Get user preferences
            prefs = NotificationPreference.get_or_create_for_user(document.user)

            # Decrypt expiry date
            # NOTE: You'll need to implement this based on your encryption
            # For now, this is a placeholder
            from vault.encryption import decrypt_text

            try:
                expiry_date_str = decrypt_text(document.encrypted_expiry_date, document.user)
                expiry_date = timezone.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"  ⚠️ Failed to decrypt expiry date for {document.id}: {str(e)}")
                continue

            # Calculate days until expiry
            days_until_expiry = (expiry_date - timezone.now().date()).days

            # Check if we should create notification for this timeframe
            should_notify = False

            if days_until_expiry < 0:
                # Expired - check if we already have an expired notification
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRED,
                    is_read=False
                ).exists()

                if not existing:
                    should_notify = True

            elif days_until_expiry == 0 and prefs.alert_on_expiry:
                # Expires today
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRY,
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    should_notify = True

            elif days_until_expiry == 1 and prefs.alert_1_day:
                # Expires tomorrow
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRY,
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    should_notify = True

            elif days_until_expiry == 7 and prefs.alert_7_days:
                # Expires in 7 days
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRY,
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    should_notify = True

            elif days_until_expiry == 15 and prefs.alert_15_days:
                # Expires in 15 days
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRY,
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    should_notify = True

            elif days_until_expiry == 30 and prefs.alert_30_days:
                # Expires in 30 days
                existing = Notification.objects.filter(
                    user=document.user,
                    document=document,
                    notification_type=Notification.DOCUMENT_EXPIRY,
                    created_at__date=timezone.now().date()
                ).exists()

                if not existing:
                    should_notify = True

            # Create notification if needed
            if should_notify:
                notification = NotificationCreator.create_expiry_alert(
                    document=document,
                    user=document.user,
                    preferences=prefs,
                    days_until_expiry=days_until_expiry
                )

                if notification:
                    notifications_created += 1
                    logger.info(f"  ✅ Created notification for document {document.id} ({days_until_expiry} days)")

        except Exception as e:
            logger.error(f"  ❌ Failed to process document {document.id}: {str(e)}")
            continue

    logger.info(f"✅ Expiry check complete. Created {notifications_created} notifications.")

    return notifications_created


def send_email_notifications():
    """
    Send email notifications for unread notifications

    Should run every few hours (e.g., via cron job)

    Usage:
        python manage.py send_email_notifications
    """
    logger.info("📧 Starting email notification job...")

    emails_sent = 0

    # Get notifications that need email but haven't been sent
    notifications = Notification.objects.filter(
        email_sent=False,
        is_read=False
    ).select_related('user', 'document', 'device')

    logger.info(f"  📬 Found {notifications.count()} notifications to email")

    for notification in notifications:
        try:
            # Get user preferences
            prefs = NotificationPreference.get_or_create_for_user(notification.user)

            # Check if user wants emails for this type
            should_email = prefs.email_enabled

            if should_email:
                if notification.notification_type in [Notification.DOCUMENT_EXPIRY, Notification.DOCUMENT_EXPIRED]:
                    should_email = prefs.email_expiry_alerts
                elif notification.notification_type in [Notification.STORAGE_WARNING, Notification.STORAGE_CRITICAL]:
                    should_email = prefs.email_storage_alerts
                elif notification.notification_type in [Notification.SECURITY_ALERT, Notification.NEW_DEVICE_LOGIN]:
                    should_email = prefs.email_security_alerts

            if should_email:
                # Send email (implement based on your email service)
                # For now, this is a placeholder

                # Example using Django send_mail:
                # from django.core.mail import send_mail
                # from vault.encryption import decrypt_text

                # try:
                #     title = decrypt_text(notification.encrypted_title, notification.user)
                #     body = decrypt_text(notification.encrypted_body, notification.user)
                #
                #     send_mail(
                #         subject=f"PrivyLock: {title}",
                #         message=body,
                #         from_email='noreply@privylock.com',
                #         recipient_list=[notification.user.email],
                #     )
                #
                #     notification.mark_email_sent()
                #     emails_sent += 1
                #     logger.info(f"  ✅ Sent email for notification {notification.id}")
                #
                # except Exception as e:
                #     logger.error(f"  ❌ Failed to send email: {str(e)}")

                # For now, just mark as sent (placeholder)
                notification.mark_email_sent()
                emails_sent += 1
                logger.info(f"  ✅ Marked notification {notification.id} as email sent (placeholder)")

        except Exception as e:
            logger.error(f"  ❌ Failed to process notification {notification.id}: {str(e)}")
            continue

    logger.info(f"✅ Email job complete. Sent {emails_sent} emails.")

    return emails_sent


def send_push_notifications():
    """
    Send push notifications (browser notifications)

    Should run every few minutes (e.g., via cron job)

    Usage:
        python manage.py send_push_notifications
    """
    logger.info("🔔 Starting push notification job...")

    pushes_sent = 0

    # Get notifications that need push but haven't been sent
    notifications = Notification.objects.filter(
        push_sent=False,
        is_read=False,
        created_at__gte=timezone.now() - timedelta(hours=24)  # Only recent ones
    ).select_related('user', 'document', 'device')

    logger.info(f"  📬 Found {notifications.count()} notifications to push")

    for notification in notifications:
        try:
            # Get user preferences
            prefs = NotificationPreference.get_or_create_for_user(notification.user)

            # Check if user wants push for this type
            should_push = prefs.push_enabled

            if should_push:
                if notification.notification_type in [Notification.DOCUMENT_EXPIRY, Notification.DOCUMENT_EXPIRED]:
                    should_push = prefs.push_expiry_alerts
                elif notification.notification_type in [Notification.STORAGE_WARNING, Notification.STORAGE_CRITICAL]:
                    should_push = prefs.push_storage_alerts
                elif notification.notification_type in [Notification.SECURITY_ALERT, Notification.NEW_DEVICE_LOGIN]:
                    should_push = prefs.push_security_alerts

            if should_push:
                # Send push notification (implement based on your push service)
                # For now, this is a placeholder

                # Example using web push (would need additional setup):
                # from webpush import send_user_notification
                #
                # payload = {
                #     'head': decrypt_text(notification.encrypted_title, notification.user),
                #     'body': decrypt_text(notification.encrypted_body, notification.user),
                #     'url': notification.action_url or '/dashboard'
                # }
                #
                # send_user_notification(
                #     user=notification.user,
                #     payload=payload
                # )

                # For now, just mark as sent (placeholder)
                notification.mark_push_sent()
                pushes_sent += 1
                logger.info(f"  ✅ Marked notification {notification.id} as push sent (placeholder)")

        except Exception as e:
            logger.error(f"  ❌ Failed to process notification {notification.id}: {str(e)}")
            continue

    logger.info(f"✅ Push job complete. Sent {pushes_sent} push notifications.")

    return pushes_sent


def cleanup_notifications():
    """
    Cleanup old and expired notifications

    Should run daily (e.g., via cron job)

    Usage:
        python manage.py cleanup_notifications
    """
    logger.info("🗑️ Starting notification cleanup...")

    # Delete expired notifications
    expired_count = cleanup_expired_notifications()

    # Delete old read notifications (older than 30 days)
    old_count = cleanup_old_read_notifications(days=30)

    total = expired_count + old_count

    logger.info(f"✅ Cleanup complete. Deleted {total} notifications.")

    return total


# ========================================
# CELERY TASKS (if using Celery)
# ========================================

# Uncomment if using Celery:

# from celery import shared_task
#
# @shared_task
# def check_document_expiry_task():
#     """Celery task for checking document expiry"""
#     return check_document_expiry()
#
# @shared_task
# def send_email_notifications_task():
#     """Celery task for sending emails"""
#     return send_email_notifications()
#
# @shared_task
# def send_push_notifications_task():
#     """Celery task for sending push notifications"""
#     return send_push_notifications()
#
# @shared_task
# def cleanup_notifications_task():
#     """Celery task for cleanup"""
#     return cleanup_notifications()