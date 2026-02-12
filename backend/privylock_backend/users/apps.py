"""
Users App Configuration

Configures the users application for Django.
This file is automatically referenced in INSTALLED_APPS.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Configuration class for the Users app.

    This app handles:
    - User authentication (register, login, logout)
    - JWT token management
    - Device tracking and management
    - Account recovery
    - User profile management
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'User Management'

    def ready(self):
        """
        Import signal handlers when app is ready.
        This method is called when Django starts.
        """
        # Import signals if you have any
        # Example: from . import signals
        pass