"""
Notification URLs for PrivyLock
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'notifications'

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # Notification endpoints
    # GET    /api/notifications/              - List notifications
    # GET    /api/notifications/{id}/         - Get notification
    # PATCH  /api/notifications/{id}/         - Update notification
    # DELETE /api/notifications/{id}/         - Delete notification
    # POST   /api/notifications/mark_read/    - Mark multiple as read
    # POST   /api/notifications/mark_all_read/ - Mark all as read
    # DELETE /api/notifications/delete_all_read/ - Delete all read
    # GET    /api/notifications/unread_count/ - Get unread count

    path('', include(router.urls)),

    # Preference endpoints
    # GET /api/notifications/preferences/    - Get preferences
    # PUT /api/notifications/preferences/    - Update preferences
    path(
        'preferences/',
        views.NotificationPreferenceViewSet.as_view({
            'get': 'list',
            'put': 'update'
        }),
        name='preferences'
    ),
]