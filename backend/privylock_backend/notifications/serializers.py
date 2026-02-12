"""
Notification Serializers for PrivyLock
Handles encryption/decryption of notification content
"""

from rest_framework import serializers
from .models import Notification, NotificationPreference
from vault.models import Document
import logging

logger = logging.getLogger(__name__)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model

    NOTE: Title and body are encrypted in database.
    Frontend must decrypt using master key.
    """

    # Encrypted fields (sent as Base64 strings)
    encrypted_title = serializers.CharField()
    encrypted_body = serializers.CharField()

    # Related object details
    document_id = serializers.UUIDField(source='document.id', read_only=True, allow_null=True)
    document_title = serializers.CharField(source='document.encrypted_title', read_only=True, allow_null=True)

    device_id = serializers.UUIDField(source='device.id', read_only=True, allow_null=True)
    device_name = serializers.CharField(source='device.device_name', read_only=True, allow_null=True)

    # Computed fields
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'priority',
            'encrypted_title',
            'encrypted_body',
            'document_id',
            'document_title',
            'device_id',
            'device_name',
            'is_read',
            'read_at',
            'action_url',
            'email_sent',
            'push_sent',
            'expires_at',
            'created_at',
            'is_expired',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'read_at',
            'email_sent',
            'push_sent',
        ]

    def to_representation(self, instance):
        """
        Convert binary fields to Base64 for JSON serialization
        """
        data = super().to_representation(instance)

        # Convert BinaryField to Base64 string
        if instance.encrypted_title:
            import base64
            data['encrypted_title'] = base64.b64encode(
                instance.encrypted_title
            ).decode('utf-8')

        if instance.encrypted_body:
            import base64
            data['encrypted_body'] = base64.b64encode(
                instance.encrypted_body
            ).decode('utf-8')

        return data


class NotificationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating notifications
    Used internally by system (not exposed to API)
    """

    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    priority = serializers.ChoiceField(
        choices=Notification.PRIORITY_LEVELS,
        default=Notification.MEDIUM
    )
    encrypted_title = serializers.CharField()
    encrypted_body = serializers.CharField()
    document_id = serializers.UUIDField(required=False, allow_null=True)
    device_id = serializers.UUIDField(required=False, allow_null=True)
    action_url = serializers.CharField(required=False, allow_null=True)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_encrypted_title(self, value):
        """Validate encrypted title"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Title cannot be empty")
        return value

    def validate_encrypted_body(self, value):
        """Validate encrypted body"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Body cannot be empty")
        return value

    def create(self, validated_data):
        """
        Create notification

        NOTE: User must be added from view context
        """
        import base64

        # Get user from context
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User required")

        # Convert Base64 strings to bytes
        encrypted_title = validated_data['encrypted_title']
        encrypted_body = validated_data['encrypted_body']

        # Handle if already bytes or needs conversion
        if isinstance(encrypted_title, str):
            encrypted_title = base64.b64decode(encrypted_title)

        if isinstance(encrypted_body, str):
            encrypted_body = base64.b64decode(encrypted_body)

        # Get related objects
        document = None
        if validated_data.get('document_id'):
            try:
                document = Document.objects.get(
                    id=validated_data['document_id'],
                    user=user
                )
            except Document.DoesNotExist:
                logger.warning(f"Document {validated_data['document_id']} not found")

        device = None
        if validated_data.get('device_id'):
            try:
                from users.models import Device
                device = Device.objects.get(
                    id=validated_data['device_id'],
                    user=user
                )
            except:
                logger.warning(f"Device {validated_data['device_id']} not found")

        # Create notification
        notification = Notification.objects.create(
            user=user,
            notification_type=validated_data['notification_type'],
            priority=validated_data.get('priority', Notification.MEDIUM),
            encrypted_title=encrypted_title,
            encrypted_body=encrypted_body,
            document=document,
            device=device,
            action_url=validated_data.get('action_url'),
            expires_at=validated_data.get('expires_at'),
        )

        logger.info(f"✅ Notification created: {notification.id} for user {user.username}")

        return notification


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )

    def validate_notification_ids(self, value):
        """Validate notification IDs belong to user"""
        user = self.context.get('user')
        if not user:
            raise serializers.ValidationError("User required")

        # Check all notifications exist and belong to user
        existing_ids = set(
            Notification.objects.filter(
                id__in=value,
                user=user
            ).values_list('id', flat=True)
        )

        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid notification IDs: {invalid_ids}"
            )

        return value

    def mark_as_read(self):
        """Mark notifications as read"""
        user = self.context.get('user')
        notification_ids = self.validated_data['notification_ids']

        # Update all notifications
        count = Notification.objects.filter(
            id__in=notification_ids,
            user=user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        logger.info(f"✅ Marked {count} notifications as read for user {user.username}")

        return count


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model
    """

    class Meta:
        model = NotificationPreference
        fields = [
            'in_app_enabled',
            'email_enabled',
            'email_expiry_alerts',
            'email_storage_alerts',
            'email_security_alerts',
            'push_enabled',
            'push_expiry_alerts',
            'push_storage_alerts',
            'push_security_alerts',
            'alert_30_days',
            'alert_15_days',
            'alert_7_days',
            'alert_1_day',
            'alert_on_expiry',
            'storage_warning_threshold',
            'storage_critical_threshold',
        ]

    def validate_storage_warning_threshold(self, value):
        """Validate storage warning threshold"""
        if not (50 <= value <= 100):
            raise serializers.ValidationError(
                "Storage warning threshold must be between 50 and 100"
            )
        return value

    def validate_storage_critical_threshold(self, value):
        """Validate storage critical threshold"""
        if not (50 <= value <= 100):
            raise serializers.ValidationError(
                "Storage critical threshold must be between 50 and 100"
            )
        return value

    def validate(self, data):
        """Validate that critical threshold is higher than warning threshold"""
        warning = data.get('storage_warning_threshold', 80)
        critical = data.get('storage_critical_threshold', 95)

        if critical <= warning:
            raise serializers.ValidationError(
                "Critical threshold must be higher than warning threshold"
            )

        return data


from django.utils import timezone