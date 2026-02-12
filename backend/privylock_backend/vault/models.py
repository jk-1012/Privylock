"""
Document vault models for LifeVault - WITH FOLDER SUPPORT

============================================================================
STEP 1: MODELS.PY - Add Folder Model and Update Document Model
============================================================================

✅ NEW: Folder model for organizing documents
✅ UPDATED: Document model with folder field
✅ FIXED: TextField for encrypted metadata (not BinaryField)

Changes:
1. Added Folder model with hierarchical structure (parent-child)
2. Added folder field to Document model
3. All encrypted fields use TextField for base64 strings
4. Added document_count property to Folder

============================================================================
"""

from django.db import models
from django.conf import settings
import uuid
import os


# ============================================================================
# HELPER FUNCTION
# ============================================================================

def document_upload_path(instance, filename):
    """
    Generate upload path for document files.

    Handles both Document and DocumentVersion instances.
    Path format: documents/{user_id}/{uuid}_{filename}
    """
    ext = filename.split('.')[-1] if '.' in filename else ''
    new_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    # Get user ID - handle both Document and DocumentVersion
    if hasattr(instance, 'user'):
        user_id = str(instance.user.id)
    elif hasattr(instance, 'document'):
        user_id = str(instance.document.user.id)
    else:
        user_id = 'unknown'

    return os.path.join('documents', user_id, new_filename)


# ============================================================================
# DOCUMENT CATEGORY MODEL
# ============================================================================

class DocumentCategory(models.Model):
    """
    Predefined categories for document organization.

    Examples: Identity Documents, Vehicles, Property, Financial, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., 'Identity Documents')"
    )

    icon = models.CharField(
        max_length=50,
        help_text="Emoji or icon identifier"
    )

    display_order = models.IntegerField(
        default=0,
        help_text="Order for display in UI"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_categories'
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Document Categories'

    def __str__(self):
        return f"{self.icon} {self.name}"


# ============================================================================
# ✅ NEW: FOLDER MODEL
# ============================================================================

class Folder(models.Model):
    """
    Folders for organizing documents within categories.

    Features:
    - Hierarchical structure (parent-child relationships)
    - Encrypted folder names
    - Category-specific
    - User-specific
    - Customizable appearance (color, icon)

    Examples:
    - Identity Documents > Person 1 > Aadhaar Card
    - Vehicles > MH-01-AB-1234 > Insurance
    - Property > Mumbai House > Sale Deed
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='folders',
        help_text="Owner of this folder"
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.CASCADE,
        related_name='folders',
        help_text="Category this folder belongs to"
    )

    # Encrypted folder name (stored as base64 string)
    encrypted_name = models.TextField(
        help_text="Client-encrypted folder name (base64 string)"
    )

    # Parent folder for creating sub-folders
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        help_text="Parent folder (null for root folders)"
    )

    # Folder appearance
    color = models.CharField(
        max_length=7,
        default='#3b82f6',
        help_text="Hex color code (e.g., #3b82f6)"
    )

    icon = models.CharField(
        max_length=10,
        default='📁',
        help_text="Folder icon (emoji)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'folders'
        ordering = ['encrypted_name']
        verbose_name = 'Folder'
        verbose_name_plural = 'Folders'
        indexes = [
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'parent']),
        ]

    def __str__(self):
        return f"Folder: {self.encrypted_name[:20]}..."

    @property
    def document_count(self):
        """
        Get total documents in this folder (including subfolders).
        """
        count = self.documents.filter(is_deleted=False).count()
        for subfolder in self.subfolders.all():
            count += subfolder.document_count
        return count


# ============================================================================
# DOCUMENT MODEL (✅ UPDATED WITH FOLDER FIELD)
# ============================================================================

class Document(models.Model):
    """
    Main document model - stores metadata and encrypted file.

    Security:
    - All text fields encrypted client-side before storage
    - Server never sees plaintext content
    - File encrypted with AES-256-GCM
    - Only encrypted blob stored on server

    ✅ NEW: folder field for organizing documents
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents'
    )

    # ✅ NEW: Folder field
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,  # Keep document if folder deleted
        null=True,
        blank=True,
        related_name='documents',
        help_text="Optional folder for organization"
    )

    # Encrypted metadata (stored as base64 strings)
    encrypted_title = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted document title (base64 string)"
    )

    encrypted_description = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted description (base64 string)"
    )

    encrypted_doc_type = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted document type (base64 string)"
    )

    # File storage
    encrypted_file = models.FileField(
        upload_to=document_upload_path,
        help_text="Encrypted document file"
    )

    # File metadata (NOT encrypted - for server operations)
    file_size = models.BigIntegerField(
        help_text="File size in bytes"
    )

    file_extension = models.CharField(
        max_length=10,
        help_text="Original file extension"
    )

    mime_type = models.CharField(
        max_length=100,
        default='application/octet-stream',
        help_text="MIME type of original file"
    )

    file_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of encrypted file"
    )

    # Expiry tracking
    has_expiry = models.BooleanField(
        default=False,
        help_text="Whether document has expiry date"
    )

    encrypted_issue_date = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted issue date (base64 string)"
    )

    encrypted_expiry_date = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted expiry date (base64 string)"
    )

    notification_trigger_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp for notification scheduling"
    )

    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag"
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'folder']),  # ✅ NEW
            models.Index(fields=['notification_trigger_timestamp']),
        ]

    def __str__(self):
        return f"Document {self.id}"

    def delete_file(self):
        """Delete the physical file from storage."""
        if self.encrypted_file:
            if os.path.isfile(self.encrypted_file.path):
                os.remove(self.encrypted_file.path)


# ============================================================================
# DOCUMENT VERSION MODEL
# ============================================================================

class DocumentVersion(models.Model):
    """
    Version control for documents.
    Each update creates a new version.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )

    version_number = models.IntegerField(
        help_text="Sequential version number (1, 2, 3...)"
    )

    encrypted_file = models.FileField(
        upload_to=document_upload_path,
        help_text="Encrypted file for this version"
    )

    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=64)

    encrypted_change_notes = models.TextField(
        default='',
        blank=True,
        help_text="Client-encrypted notes about changes (base64 string)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_versions'
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']

    def __str__(self):
        return f"v{self.version_number} of {self.document.id}"


# ============================================================================
# END OF MODELS.PY
# ============================================================================
"""
Next Steps:
1. Replace your vault/models.py with this file
2. Run: python manage.py makemigrations vault
3. Run: python manage.py migrate vault
4. Continue to STEP 2 (serializers.py)
"""