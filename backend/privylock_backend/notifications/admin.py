"""
Notification Admin for PrivyLock
Provides admin interface for notifications
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Notification, NotificationPreference
import base64


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""

    list_display = [
        'id',
        'user_link',
        'notification_type_badge',
        'priority_badge',
        'encrypted_title_preview',
        'is_read_badge',
        'email_sent_badge',
        'created_at',
    ]

    list_filter = [
        'notification_type',
        'priority',
        'is_read',
        'email_sent',
        'push_sent',
        'created_at',
    ]

    search_fields = [
        'user__username',
        'id',
    ]

    readonly_fields = [
        'id',
        'user',
        'notification_type',
        'priority',
        'encrypted_title_display',
        'encrypted_body_display',
        'document',
        'device',
        'is_read',
        'read_at',
        'email_sent',
        'email_sent_at',
        'push_sent',
        'push_sent_at',
        'created_at',
        'updated_at',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'notification_type',
                'priority',
            )
        }),
        ('Content (Encrypted)', {
            'fields': (
                'encrypted_title_display',
                'encrypted_body_display',
            ),
            'description': 'Content is encrypted and cannot be read in admin panel.'
        }),
        ('Related Objects', {
            'fields': (
                'document',
                'device',
                'action_url',
            )
        }),
        ('Status', {
            'fields': (
                'is_read',
                'read_at',
                'email_sent',
                'email_sent_at',
                'push_sent',
                'push_sent_at',
            )
        }),
        ('Timestamps', {
            'fields': (
                'expires_at',
                'created_at',
                'updated_at',
            )
        }),
    )

    actions = [
        'mark_as_read',
        'mark_as_unread',
        'delete_selected',
    ]

    def user_link(self, obj):
        """Display user with link"""
        from django.urls import reverse
        from django.utils.html import format_html

        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def notification_type_badge(self, obj):
        """Display notification type with color badge"""
        colors = {
            'DOCUMENT_EXPIRY': '#FF9800',
            'DOCUMENT_EXPIRED': '#F44336',
            'STORAGE_WARNING': '#FF9800',
            'STORAGE_CRITICAL': '#F44336',
            'SECURITY_ALERT': '#F44336',
            'NEW_DEVICE_LOGIN': '#2196F3',
            'SYSTEM': '#9E9E9E',
        }
        color = colors.get(obj.notification_type, '#9E9E9E')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_notification_type_display()
        )
    notification_type_badge.short_description = 'Type'

    def priority_badge(self, obj):
        """Display priority with color badge"""
        colors = {
            'LOW': '#4CAF50',
            'MEDIUM': '#FF9800',
            'HIGH': '#FF5722',
            'CRITICAL': '#F44336',
        }
        color = colors.get(obj.priority, '#9E9E9E')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.priority
        )
    priority_badge.short_description = 'Priority'

    def encrypted_title_preview(self, obj):
        """Display encrypted title preview"""
        if obj.encrypted_title:
            preview = base64.b64encode(obj.encrypted_title[:20]).decode('utf-8')
            return f"{preview}..."
        return "—"
    encrypted_title_preview.short_description = 'Title (Encrypted)'

    def encrypted_title_display(self, obj):
        """Display full encrypted title"""
        if obj.encrypted_title:
            return base64.b64encode(obj.encrypted_title).decode('utf-8')
        return "—"
    encrypted_title_display.short_description = 'Encrypted Title (Base64)'

    def encrypted_body_display(self, obj):
        """Display full encrypted body"""
        if obj.encrypted_body:
            return base64.b64encode(obj.encrypted_body).decode('utf-8')
        return "—"
    encrypted_body_display.short_description = 'Encrypted Body (Base64)'

    def is_read_badge(self, obj):
        """Display read status with badge"""
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Read</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">○ Unread</span>'
        )
    is_read_badge.short_description = 'Status'

    def email_sent_badge(self, obj):
        """Display email sent status"""
        if obj.email_sent:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: gray;">○</span>')
    email_sent_badge.short_description = 'Email'

    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        count = queryset.filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'Marked {count} notifications as read.')
    mark_as_read.short_description = 'Mark selected as read'

    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        count = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        self.message_user(request, f'Marked {count} notifications as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'

    def has_add_permission(self, request):
        """Disable manual notification creation in admin"""
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model"""

    list_display = [
        'user_link',
        'in_app_enabled',
        'email_enabled',
        'push_enabled',
        'alerts_summary',
    ]

    list_filter = [
        'in_app_enabled',
        'email_enabled',
        'push_enabled',
        'email_expiry_alerts',
        'email_storage_alerts',
        'email_security_alerts',
    ]

    search_fields = [
        'user__username',
    ]

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('In-App Notifications', {
            'fields': (
                'in_app_enabled',
            )
        }),
        ('Email Notifications', {
            'fields': (
                'email_enabled',
                'email_expiry_alerts',
                'email_storage_alerts',
                'email_security_alerts',
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_enabled',
                'push_expiry_alerts',
                'push_storage_alerts',
                'push_security_alerts',
            )
        }),
        ('Expiry Alert Timing', {
            'fields': (
                'alert_30_days',
                'alert_15_days',
                'alert_7_days',
                'alert_1_day',
                'alert_on_expiry',
            )
        }),
        ('Storage Thresholds', {
            'fields': (
                'storage_warning_threshold',
                'storage_critical_threshold',
            )
        }),
    )

    def user_link(self, obj):
        """Display user with link"""
        from django.urls import reverse

        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def alerts_summary(self, obj):
        """Display summary of enabled alerts"""
        alerts = []
        if obj.alert_30_days:
            alerts.append('30d')
        if obj.alert_15_days:
            alerts.append('15d')
        if obj.alert_7_days:
            alerts.append('7d')
        if obj.alert_1_day:
            alerts.append('1d')
        if obj.alert_on_expiry:
            alerts.append('0d')

        return ', '.join(alerts) if alerts else 'None'
    alerts_summary.short_description = 'Expiry Alerts'