"""
Serializers for vault API - WITH FOLDER SUPPORT

============================================================================
STEP 2: SERIALIZERS.PY - Add FolderSerializer and Update DocumentSerializer
============================================================================

✅ NEW: FolderSerializer for folder CRUD operations
✅ UPDATED: DocumentSerializer with folder and folder_name fields
✅ FIXED: Correct field order in create() method

Changes:
1. Added FolderSerializer with validation
2. Updated DocumentSerializer with folder fields
3. Fixed field order to prevent empty encrypted fields
4. Added folder validation in FolderSerializer

============================================================================
"""

from rest_framework import serializers
from .models import Document, DocumentCategory, DocumentVersion, Folder
from django.db import transaction
import hashlib
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# DOCUMENT CATEGORY SERIALIZER
# ============================================================================

class DocumentCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for document categories.
    """
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'icon', 'display_order', 'document_count']

    def get_document_count(self, obj):
        """Count non-deleted documents in this category."""
        return obj.documents.filter(is_deleted=False).count()


# ============================================================================
# ✅ NEW: FOLDER SERIALIZER
# ============================================================================

class FolderSerializer(serializers.ModelSerializer):
    """
    Serializer for Folder model.

    Handles folder creation, updates, and nested folder trees.
    Provides document count and category information.
    """
    document_count = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)

    class Meta:
        model = Folder
        fields = [
            'id',
            'user',
            'category',
            'category_name',
            'category_icon',
            'encrypted_name',
            'parent',
            'color',
            'icon',
            'document_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'created_at',
            'updated_at',
            'document_count',
            'category_name',
            'category_icon',
        ]

    def validate(self, data):
        """
        Validate folder creation.

        Checks:
        1. Parent folder belongs to same user
        2. Parent folder belongs to same category
        3. No circular references
        """
        # Validate parent folder
        if 'parent' in data and data['parent']:
            parent = data['parent']
            request = self.context.get('request')

            # Check parent ownership
            if request and parent.user != request.user:
                raise serializers.ValidationError({
                    'parent': 'Parent folder must belong to you'
                })

            # Check parent category matches
            if 'category' in data and parent.category != data['category']:
                raise serializers.ValidationError({
                    'parent': 'Parent folder must be in same category'
                })

            # Prevent circular references (folder cannot be its own parent)
            if self.instance and parent.id == self.instance.id:
                raise serializers.ValidationError({
                    'parent': 'Folder cannot be its own parent'
                })

        return data

    def validate_encrypted_name(self, value):
        """Validate encrypted name is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError('Folder name cannot be empty')
        return value


# ============================================================================
# DOCUMENT SERIALIZER (✅ UPDATED WITH FOLDER FIELDS)
# ============================================================================

class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for Document model with folder support.

    ✅ NEW: folder and folder_name fields
    ✅ FIXED: Correct field order in create() method
    """
    encrypted_file = serializers.FileField(
        write_only=True,
        required=True,
        help_text="Encrypted file blob from client"
    )

    category_details = DocumentCategorySerializer(
        source='category',
        read_only=True,
        help_text="Full category object (read-only)"
    )

    # ✅ NEW: Folder information
    folder_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'category',
            'category_details',
            'folder',  # ✅ NEW
            'folder_name',  # ✅ NEW
            'encrypted_title',
            'encrypted_description',
            'encrypted_doc_type',
            'encrypted_file',
            'file_size',
            'file_extension',
            'mime_type',
            'file_hash',
            'has_expiry',
            'encrypted_issue_date',
            'encrypted_expiry_date',
            'notification_trigger_timestamp',
            'is_deleted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'file_size',
            'file_extension',
            'mime_type',
            'file_hash',
            'is_deleted',
            'created_at',
            'updated_at',
            'category_details',
            'folder_name',
        ]

    def get_folder_name(self, obj):
        """Get encrypted folder name if document is in a folder."""
        if obj.folder:
            return obj.folder.encrypted_name
        return None

    def validate(self, data):
        """
        Validate document data.

        Checks:
        1. Folder belongs to same user (if provided)
        2. Folder belongs to same category (if provided)
        """
        if 'folder' in data and data['folder']:
            folder = data['folder']
            request = self.context.get('request')

            # Check folder ownership
            if request and folder.user != request.user:
                raise serializers.ValidationError({
                    'folder': 'Folder must belong to you'
                })

            # Check folder category matches document category
            if 'category' in data and folder.category != data['category']:
                raise serializers.ValidationError({
                    'folder': 'Folder must be in same category as document'
                })

        return data

    def create(self, validated_data):
        """
        Create new document with encryption.

        ✅ CRITICAL FIX: Correct field order
        - Extract encrypted fields first
        - Create document with base fields
        - Encrypted fields override any empty defaults
        """
        # Extract user
        user = validated_data.pop('user', None)
        if not user:
            user = self.context.get('request').user

        if not user:
            raise serializers.ValidationError({'error': 'User not authenticated'})

        logger.info(f"📝 Creating document for user: {user.id}")

        # Extract encrypted file
        if 'encrypted_file' not in validated_data:
            raise serializers.ValidationError({
                'encrypted_file': 'This field is required.'
            })

        encrypted_file = validated_data.pop('encrypted_file')
        logger.info(f"📁 File received: {encrypted_file.name}, size: {encrypted_file.size}")

        # Validate storage
        file_size = encrypted_file.size

        storage_limits = {
            'FREE': 1073741824,           # 1 GB
            'PREMIUM': 26843545600,       # 25 GB
            'FAMILY': 107374182400,       # 100 GB
            'LIFETIME': 10737418240,      # 10 GB
        }

        user_limit = storage_limits.get(user.subscription_tier, storage_limits['FREE'])

        if user.storage_used + file_size > user_limit:
            available = user_limit - user.storage_used
            raise serializers.ValidationError({
                'file': f'Storage limit exceeded. Available: {available} bytes'
            })

        logger.info(f"✅ Storage check passed")

        # Calculate file hash
        try:
            file_content = encrypted_file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            encrypted_file.seek(0)
            logger.info(f"🔢 File hash: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"❌ Hash calculation failed: {str(e)}")
            raise serializers.ValidationError({'file': 'Failed to process file'})

        # Extract file metadata
        file_name = encrypted_file.name
        file_extension = file_name.split('.')[-1] if '.' in file_name else ''
        mime_type = encrypted_file.content_type or 'application/octet-stream'

        logger.info(f"📄 File metadata: ext={file_extension}, mime={mime_type}")

        # ========================================================================
        # 🔧 CRITICAL: Extract encrypted fields BEFORE creating document
        # ========================================================================
        encrypted_title = validated_data.pop('encrypted_title', '')
        encrypted_description = validated_data.pop('encrypted_description', '')
        encrypted_doc_type = validated_data.pop('encrypted_doc_type', '')
        encrypted_issue_date = validated_data.pop('encrypted_issue_date', '')
        encrypted_expiry_date = validated_data.pop('encrypted_expiry_date', '')

        logger.info(f"🔐 Encrypted title length: {len(encrypted_title)}")

        # Log folder info if present
        if 'folder' in validated_data and validated_data['folder']:
            logger.info(f"📁 Document will be in folder: {validated_data['folder'].id}")

        # Create document
        try:
            with transaction.atomic():
                encrypted_file.seek(0)

                # ✅ CORRECT: Create with all fields in proper order
                document = Document.objects.create(
                    user=user,
                    encrypted_file=encrypted_file,
                    file_size=file_size,
                    file_extension=file_extension,
                    mime_type=mime_type,
                    file_hash=file_hash,
                    encrypted_title=encrypted_title,
                    encrypted_description=encrypted_description,
                    encrypted_doc_type=encrypted_doc_type,
                    encrypted_issue_date=encrypted_issue_date,
                    encrypted_expiry_date=encrypted_expiry_date,
                    **validated_data,  # Contains: category, folder, has_expiry, etc.
                )

                logger.info(f"✅ Document created: {document.id}")
                logger.info(f"✅ Title saved: {document.encrypted_title[:20]}...")
                if document.folder:
                    logger.info(f"✅ In folder: {document.folder.id}")

                # Create version 1
                encrypted_file.seek(0)

                version = DocumentVersion.objects.create(
                    document=document,
                    version_number=1,
                    encrypted_file=encrypted_file,
                    file_size=file_size,
                    file_hash=file_hash
                )

                logger.info(f"✅ Version 1 created: {version.id}")

                # Update user storage
                user.storage_used += file_size
                user.save(update_fields=['storage_used'])

                logger.info(f"📊 Storage updated: {user.storage_used} bytes")

                return document

        except Exception as e:
            logger.error(f"❌ Document creation failed: {str(e)}", exc_info=True)
            raise serializers.ValidationError({
                'error': f'Failed to create document: {str(e)}'
            })


# ============================================================================
# DOCUMENT VERSION SERIALIZER
# ============================================================================

class DocumentVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for document versions.
    """
    class Meta:
        model = DocumentVersion
        fields = [
            'id',
            'version_number',
            'file_size',
            'file_hash',
            'encrypted_change_notes',
            'created_at'
        ]
        read_only_fields = fields


# ============================================================================
# END OF SERIALIZERS.PY
# ============================================================================
"""
Next Steps:
1. Replace your vault/serializers.py with this file
2. Restart Django server to load new serializers
3. Continue to STEP 3 (views.py)
"""