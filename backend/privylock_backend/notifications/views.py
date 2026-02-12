"""
Notification Views for PrivyLock
Provides API endpoints for notification management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
import logging

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationSerializer,
    NotificationMarkReadSerializer,
    NotificationPreferenceSerializer
)

logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Notification operations

    Endpoints:
    - GET /api/notifications/ - List notifications
    - GET /api/notifications/{id}/ - Get notification details
    - PATCH /api/notifications/{id}/ - Update notification (mark as read)
    - DELETE /api/notifications/{id}/ - Delete notification
    - POST /api/notifications/mark_read/ - Mark multiple as read
    - POST /api/notifications/mark_all_read/ - Mark all as read
    - DELETE /api/notifications/delete_all_read/ - Delete all read notifications
    - GET /api/notifications/unread_count/ - Get unread count
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get notifications for current user

        Query params:
        - unread_only: true/false (default: false)
        - notification_type: filter by type
        - priority: filter by priority
        """
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        # Filter by unread
        unread_only = self.request.query_params.get('unread_only', 'false')
        if unread_only.lower() == 'true':
            queryset = queryset.filter(is_read=False)

        # Filter by type
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Exclude expired notifications
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )

        return queryset.select_related('document', 'device')

    def list(self, request, *args, **kwargs):
        """
        List notifications

        Returns notifications in descending order (newest first)
        """
        try:
            queryset = self.get_queryset()

            # Pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)

            logger.info(f"📬 Listed {len(serializer.data)} notifications for {request.user.username}")

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Failed to list notifications: {str(e)}")
            return Response(
                {'error': 'Failed to load notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, *args, **kwargs):
        """Get notification details"""
        try:
            notification = self.get_object()
            serializer = self.get_serializer(notification)

            logger.info(f"📬 Retrieved notification {notification.id}")

            return Response(serializer.data)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Failed to retrieve notification: {str(e)}")
            return Response(
                {'error': 'Failed to load notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, *args, **kwargs):
        """
        Update notification (typically to mark as read)

        Request body:
        {
          "is_read": true
        }
        """
        try:
            notification = self.get_object()

            # Only allow updating is_read field
            if 'is_read' in request.data:
                is_read = request.data['is_read']

                if is_read and not notification.is_read:
                    notification.mark_as_read()
                    logger.info(f"✅ Marked notification {notification.id} as read")
                elif not is_read and notification.is_read:
                    notification.is_read = False
                    notification.read_at = None
                    notification.save(update_fields=['is_read', 'read_at'])
                    logger.info(f"✅ Marked notification {notification.id} as unread")

            serializer = self.get_serializer(notification)
            return Response(serializer.data)

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Failed to update notification: {str(e)}")
            return Response(
                {'error': 'Failed to update notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Delete notification"""
        try:
            notification = self.get_object()
            notification_id = notification.id
            notification.delete()

            logger.info(f"🗑️ Deleted notification {notification_id}")

            return Response(
                {'message': 'Notification deleted'},
                status=status.HTTP_204_NO_CONTENT
            )

        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"❌ Failed to delete notification: {str(e)}")
            return Response(
                {'error': 'Failed to delete notification'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """
        Mark multiple notifications as read

        Request body:
        {
          "notification_ids": ["uuid1", "uuid2", ...]
        }
        """
        try:
            serializer = NotificationMarkReadSerializer(
                data=request.data,
                context={'user': request.user}
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            count = serializer.mark_as_read()

            return Response({
                'message': f'Marked {count} notifications as read',
                'count': count
            })

        except Exception as e:
            logger.error(f"❌ Failed to mark notifications as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark notifications as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        try:
            count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )

            logger.info(f"✅ Marked all {count} notifications as read for {request.user.username}")

            return Response({
                'message': f'Marked {count} notifications as read',
                'count': count
            })

        except Exception as e:
            logger.error(f"❌ Failed to mark all as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark all as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def delete_all_read(self, request):
        """Delete all read notifications"""
        try:
            notifications = Notification.objects.filter(
                user=request.user,
                is_read=True
            )
            count = notifications.count()
            notifications.delete()

            logger.info(f"🗑️ Deleted {count} read notifications for {request.user.username}")

            return Response({
                'message': f'Deleted {count} read notifications',
                'count': count
            })

        except Exception as e:
            logger.error(f"❌ Failed to delete read notifications: {str(e)}")
            return Response(
                {'error': 'Failed to delete read notifications'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        try:
            count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).filter(
                Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
            ).count()

            return Response({
                'count': count
            })

        except Exception as e:
            logger.error(f"❌ Failed to get unread count: {str(e)}")
            return Response(
                {'error': 'Failed to get unread count'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for NotificationPreference operations

    Endpoints:
    - GET /api/notifications/preferences/ - Get preferences
    - PUT /api/notifications/preferences/ - Update preferences
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get notification preferences"""
        try:
            preferences = NotificationPreference.get_or_create_for_user(request.user)
            serializer = NotificationPreferenceSerializer(preferences)

            logger.info(f"📬 Retrieved preferences for {request.user.username}")

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Failed to get preferences: {str(e)}")
            return Response(
                {'error': 'Failed to load preferences'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update(self, request, pk=None):
        """Update notification preferences"""
        try:
            preferences = NotificationPreference.get_or_create_for_user(request.user)
            serializer = NotificationPreferenceSerializer(
                preferences,
                data=request.data,
                partial=True
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer.save()

            logger.info(f"✅ Updated preferences for {request.user.username}")

            return Response(serializer.data)

        except Exception as e:
            logger.error(f"❌ Failed to update preferences: {str(e)}")
            return Response(
                {'error': 'Failed to update preferences'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )