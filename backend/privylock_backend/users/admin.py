"""
Users App Admin Configuration - UPDATED FOR PRIVYLOCK

Customizes Django admin interface for user management.
Provides admin panel for viewing and managing users and devices.

CHANGES:
✅ Show email instead of encrypted_email
✅ Show mobile_number
✅ Show email_verified status (mobile verification removed)
✅ Show google_id and auth_provider
✅ Updated filters and search fields
✅ Changed LifeVault → PrivyLock branding

Admin Features:
- User management (view, edit, delete)
- Device management
- Search and filters
- Bulk actions
- Verification status indicators
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Device


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.

    Features:
    - List view with key user info
    - Search by username, email, mobile
    - Filter by verification status, provider, subscription
    - Custom display for verification status
    - Readonly sensitive fields
    """

    # List display
    list_display = [
        'id',
        'email',
        'mobile_number',
        'email_verification_badge',
        'auth_provider_badge',
        'subscription_tier',
        'storage_usage',
        'created_at',
        'last_login_at',
        'is_active',
    ]

    # List filters
    list_filter = [
        'auth_provider',
        'email_verified',
        'subscription_tier',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
    ]

    # Search fields
    search_fields = [
        'username',
        'email',
        'mobile_number',
        'id',
    ]

    # Ordering
    ordering = ['-created_at']

    # Readonly fields
    readonly_fields = [
        'id',
        'username',
        'email_verification_token',
        'google_id',
        'recovery_key_hash',
        'created_at',
        'last_login_at',
        'storage_usage',
    ]

    # Fieldsets for detail view
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'username', 'password')
        }),
        ('Contact Information', {
            'fields': (
                'email',
                'mobile_number',
            ),
        }),
        ('Verification Status', {
            'fields': (
                'email_verified',
                'email_verification_token',
            ),
            'description': 'Email verification status (mobile verification disabled)',
        }),
        ('Authentication', {
            'fields': (
                'auth_provider',
                'google_id',
                'recovery_key_hash',
            ),
        }),
        ('Subscription & Storage', {
            'fields': ('subscription_tier', 'storage_usage'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {
            'fields': ('created_at', 'last_login_at', 'last_login'),
        }),
    )

    # Add user fieldsets
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'mobile_number',
                'password1',
                'password2',
                'email_verified',
            ),
        }),
    )

    def email_verification_badge(self, obj):
        """Display email verification status with colored badge."""
        if obj.email_verified:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 10px; '
                'border-radius: 3px; font-size: 11px; font-weight: bold;">'
                '✓ Verified</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '✗ Not Verified</span>'
        )
    email_verification_badge.short_description = 'Email Status'

    def auth_provider_badge(self, obj):
        """Display authentication provider with badge."""
        colors = {
            'local': '#2196F3',  # Blue
            'google': '#DB4437',  # Google Red
        }
        color = colors.get(obj.auth_provider, '#9E9E9E')

        icon = '🔐' if obj.auth_provider == 'local' else '🌐'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.get_auth_provider_display()
        )
    auth_provider_badge.short_description = 'Provider'

    def storage_usage(self, obj):
        """Display storage usage in human-readable format."""
        bytes_used = obj.storage_used

        if bytes_used == 0:
            return '0 Bytes'

        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        while bytes_used >= k and i < len(sizes) - 1:
            bytes_used /= k
            i += 1

        return f"{bytes_used:.2f} {sizes[i]}"

    storage_usage.short_description = 'Storage Used'

    # Bulk actions
    actions = ['verify_email', 'mark_unverified']

    def verify_email(self, request, queryset):
        """Bulk action: Mark emails as verified."""
        updated = queryset.update(email_verified=True)
        self.message_user(
            request,
            f'{updated} user(s) marked as email verified.'
        )
    verify_email.short_description = 'Mark selected users as email verified'

    def mark_unverified(self, request, queryset):
        """Bulk action: Mark as unverified."""
        updated = queryset.update(email_verified=False)
        self.message_user(
            request,
            f'{updated} user(s) marked as unverified.'
        )
    mark_unverified.short_description = 'Mark selected users as unverified'


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin interface for Device model.

    Features:
    - View all user devices
    - Filter by device type, trust status
    - Search by device name, ID
    - Bulk trust/untrust actions
    """

    # List display
    list_display = [
        'id',
        'user_link',
        'device_name',
        'device_type_badge',
        'trust_status',
        'last_active',
        'created_at',
    ]

    # List filters
    list_filter = [
        'device_type',
        'is_trusted',
        'created_at',
        'last_active',
    ]

    # Search fields
    search_fields = [
        'device_id',
        'device_name',
        'user__username',
        'user__email',
    ]

    # Ordering
    ordering = ['-last_active']

    # Readonly fields
    readonly_fields = [
        'id',
        'device_id',
        'created_at',
        'last_active',
    ]

    # Fieldsets
    fieldsets = (
        ('Device Information', {
            'fields': ('id', 'device_id', 'device_name', 'device_type')
        }),
        ('User & Security', {
            'fields': ('user', 'is_trusted'),
        }),
        ('Activity', {
            'fields': ('created_at', 'last_active'),
        }),
    )

    def user_link(self, obj):
        """Display user with link."""
        from django.urls import reverse

        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.email
        )
    user_link.short_description = 'User'

    def device_type_badge(self, obj):
        """Display device type with icon."""
        icons = {
            'web': '🌐',
            'android': '📱',
            'ios': '🍎',
        }
        icon = icons.get(obj.device_type, '📱')

        return format_html(
            '{} {}',
            icon,
            obj.get_device_type_display()
        )
    device_type_badge.short_description = 'Type'

    def trust_status(self, obj):
        """Display trust status with color."""
        if obj.is_trusted:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Trusted</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Not Trusted</span>'
        )

    trust_status.short_description = 'Trust Status'

    # Bulk actions
    actions = ['mark_as_trusted', 'mark_as_untrusted']

    def mark_as_trusted(self, request, queryset):
        """Bulk action: Mark devices as trusted."""
        updated = queryset.update(is_trusted=True)
        self.message_user(
            request,
            f'{updated} device(s) marked as trusted.'
        )

    mark_as_trusted.short_description = 'Mark selected devices as trusted'

    def mark_as_untrusted(self, request, queryset):
        """Bulk action: Mark devices as untrusted."""
        updated = queryset.update(is_trusted=False)
        self.message_user(
            request,
            f'{updated} device(s) marked as untrusted.'
        )

    mark_as_untrusted.short_description = 'Mark selected devices as untrusted'