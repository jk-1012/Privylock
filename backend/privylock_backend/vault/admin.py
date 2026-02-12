"""
Vault App Admin Configuration

Customizes Django admin interface for document management.
Provides admin panel for viewing documents, categories, and versions.

Security Note:
- Document content is encrypted and cannot be viewed in admin
- Admin can only see metadata (encrypted titles, file sizes, etc.)
- This maintains zero-knowledge architecture
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import DocumentCategory, Document, DocumentVersion


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for DocumentCategory model.

    Features:
    - List all categories with document counts
    - Reorder categories (drag and drop)
    - Edit category names and icons
    """

    # List display
    list_display = [
        'display_order',
        'category_name',
        'icon',
        'document_count',
        'created_documents',
    ]

    # List editable
    list_editable = ['display_order']

    # REQUIRED:
    # The first field in list_display cannot be editable unless
    # list_display_links is explicitly set to another field
    list_display_links = ['category_name']

    # Ordering
    ordering = ['display_order', 'name']

    # Search
    search_fields = ['name']

    def category_name(self, obj):
        """Display category with icon."""
        return f"{obj.icon} {obj.name}"

    category_name.short_description = 'Category'
    category_name.admin_order_field = 'name'

    def document_count(self, obj):
        """Count documents in this category."""
        count = obj.documents.filter(is_deleted=False).count()
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )

    document_count.short_description = 'Active Documents'

    def created_documents(self, obj):
        """Show creation stats."""
        total = obj.documents.count()
        active = obj.documents.filter(is_deleted=False).count()
        deleted = total - active

        return format_html(
            'Total: {} | Active: {} | Deleted: {}',
            total, active, deleted
        )

    created_documents.short_description = 'Statistics'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Admin interface for Document model.

    Features:
    - View all documents (encrypted)
    - Filter by category, user, status
    - Search by ID
    - Bulk soft delete/restore
    - View file size and metadata

    Note: Encrypted fields display as binary data
    """

    # List display
    list_display = [
        'id',
        'user',
        'category',
        'file_info',
        'size_display',
        'status_display',
        'has_expiry',
        'created_at',
    ]

    # List filters
    list_filter = [
        'category',
        'is_deleted',
        'has_expiry',
        'created_at',
    ]

    # Search fields
    search_fields = [
        'id',
        'user__username',
    ]

    # Ordering
    ordering = ['-created_at']

    # Readonly fields
    readonly_fields = [
        'id',
        'encrypted_title',
        'encrypted_description',
        'encrypted_doc_type',
        'file_hash',
        'created_at',
        'updated_at',
        'deleted_at',
    ]

    # Fieldsets
    fieldsets = (
        ('Document Information', {
            'fields': ('id', 'user', 'category')
        }),
        ('Encrypted Metadata', {
            'fields': (
                'encrypted_title',
                'encrypted_description',
                'encrypted_doc_type'
            ),
            'description': 'These fields contain encrypted data (zero-knowledge).',
        }),
        ('File Information', {
            'fields': (
                'encrypted_file',
                'file_size',
                'file_extension',
                'mime_type',
                'file_hash',
            ),
        }),
        ('Expiry Tracking', {
            'fields': (
                'has_expiry',
                'encrypted_issue_date',
                'encrypted_expiry_date',
                'notification_trigger_timestamp',
            ),
        }),
        ('Status', {
            'fields': (
                'is_deleted',
                'deleted_at',
            ),
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )

    def file_info(self, obj):
        """Display file extension and MIME type."""
        return f"{obj.file_extension.upper()} ({obj.mime_type})"

    file_info.short_description = 'File Type'

    def size_display(self, obj):
        """Display file size in human-readable format."""
        bytes_val = obj.file_size

        if bytes_val == 0:
            return '0 Bytes'

        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        while bytes_val >= k and i < len(sizes) - 1:
            bytes_val /= k
            i += 1

        return f"{bytes_val:.2f} {sizes[i]}"

    size_display.short_description = 'File Size'
    size_display.admin_order_field = 'file_size'

    def status_display(self, obj):
        """Display document status with color."""
        if obj.is_deleted:
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ Deleted</span>'
            )
        return format_html(
            '<span style="color: green; font-weight: bold;">✓ Active</span>'
        )

    status_display.short_description = 'Status'

    # Bulk actions
    actions = ['soft_delete_documents', 'restore_documents']

    def soft_delete_documents(self, request, queryset):
        """Bulk action: Soft delete documents."""
        from django.utils import timezone

        updated = queryset.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )

        self.message_user(
            request,
            f'{updated} document(s) marked as deleted.'
        )

    soft_delete_documents.short_description = 'Soft delete selected documents'

    def restore_documents(self, request, queryset):
        """Bulk action: Restore soft-deleted documents."""
        updated = queryset.update(
            is_deleted=False,
            deleted_at=None
        )

        self.message_user(
            request,
            f'{updated} document(s) restored.'
        )

    restore_documents.short_description = 'Restore selected documents'


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    """
    Admin interface for DocumentVersion model.

    Features:
    - View all document versions
    - Filter by document
    - See version history
    """

    # List display
    list_display = [
        'id',
        'document',
        'version_number',
        'size_display',
        'created_at',
    ]

    # List filters
    list_filter = [
        'created_at',
    ]

    # Search fields
    search_fields = [
        'document__id',
        'id',
    ]

    # Ordering
    ordering = ['-created_at']

    # Readonly fields
    readonly_fields = [
        'id',
        'document',
        'version_number',
        'file_hash',
        'created_at',
    ]

    def size_display(self, obj):
        """Display file size in human-readable format."""
        bytes_val = obj.file_size

        if bytes_val == 0:
            return '0 Bytes'

        k = 1024
        sizes = ['Bytes', 'KB', 'MB', 'GB']
        i = 0
        while bytes_val >= k and i < len(sizes) - 1:
            bytes_val /= k
            i += 1

        return f"{bytes_val:.2f} {sizes[i]}"

    size_display.short_description = 'File Size'
    size_display.admin_order_field = 'file_size'