"""
Vault App Configuration

Configures the document vault application for Django.
This app handles all document storage, encryption, and version control.
"""

from django.apps import AppConfig


class VaultConfig(AppConfig):
    """
    Configuration class for the Vault app.

    This app handles:
    - Document upload and storage (encrypted)
    - Document download and retrieval
    - Document categorization
    - Version control and history
    - Expiry tracking
    - Soft deletion and restoration
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vault'
    verbose_name = 'Document Vault'

    def ready(self):
        """
        Import signal handlers when app is ready.

        Signals that could be implemented:
        - pre_delete: Clean up files before document deletion
        - post_save: Create initial version on document creation
        - post_delete: Clean up orphaned files
        """
        # Import signals
        try:
            from . import signals
        except ImportError:
            pass