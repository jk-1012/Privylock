"""
API views for document vault - WITH FOLDER SUPPORT

============================================================================
STEP 3: VIEWS.PY - Add FolderViewSet and Update DocumentViewSet
============================================================================

✅ NEW: FolderViewSet for folder management
✅ UPDATED: DocumentViewSet with folder filtering
✅ NEW: move() action to move documents between folders

Changes:
1. Added FolderViewSet with CRUD operations
2. Added tree() action for folder hierarchy
3. Updated DocumentViewSet with folder filtering
4. Added move() action for bulk document moves

============================================================================
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.utils import timezone
from .models import Document, DocumentCategory, DocumentVersion, Folder
from .serializers import (
    DocumentSerializer,
    DocumentCategorySerializer,
    DocumentVersionSerializer,
    FolderSerializer
)
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# DOCUMENT CATEGORY VIEWSET
# ============================================================================

class DocumentCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for document categories.

    Endpoints:
    - GET /api/vault/categories/ - List all categories
    - GET /api/vault/categories/{id}/ - Get category details

    No pagination (small dataset).
    """
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def list(self, request):
        """List all document categories."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================================
# ✅ NEW: FOLDER VIEWSET
# ============================================================================

class FolderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for folder management.

    Endpoints:
    - GET    /api/vault/folders/           - List user's folders
    - POST   /api/vault/folders/           - Create new folder
    - GET    /api/vault/folders/{id}/      - Get folder details
    - PATCH  /api/vault/folders/{id}/      - Update folder
    - DELETE /api/vault/folders/{id}/      - Delete folder
    - GET    /api/vault/folders/{id}/tree/ - Get folder tree with documents

    Query Parameters:
    - category: Filter by category ID
    - parent: Filter by parent folder ID (use 'null' for root folders)
    """
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """
        Return only current user's folders.

        Supports filtering by:
        - category: Get folders in specific category
        - parent: Get root folders or subfolders of a parent
        """
        queryset = Folder.objects.filter(user=self.request.user)

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            logger.info(f"📁 Filtering folders by category: {category_id}")

        # Filter by parent (get root folders or subfolders)
        parent_id = self.request.query_params.get('parent')
        if parent_id == 'null' or parent_id == '':
            # Get root folders (no parent)
            queryset = queryset.filter(parent__isnull=True)
            logger.info(f"📁 Getting root folders")
        elif parent_id:
            # Get subfolders of specific parent
            queryset = queryset.filter(parent_id=parent_id)
            logger.info(f"📁 Getting subfolders of: {parent_id}")

        return queryset.select_related('category', 'parent')

    def perform_create(self, serializer):
        """Create folder for current user."""
        folder = serializer.save(user=self.request.user)
        logger.info(f"📁 Folder created: {folder.id} by user {self.request.user.id}")

    def perform_update(self, serializer):
        """Update folder."""
        folder = serializer.save()
        logger.info(f"📁 Folder updated: {folder.id}")

    def perform_destroy(self, instance):
        """
        Delete folder.

        Documents in the folder are preserved (folder field set to NULL).
        Subfolders are also deleted (CASCADE).
        """
        folder_id = instance.id
        doc_count = instance.documents.count()
        subfolder_count = instance.subfolders.count()

        # Delete folder (documents will have folder set to NULL)
        instance.delete()

        logger.info(
            f"📁 Folder deleted: {folder_id} "
            f"({doc_count} docs preserved, {subfolder_count} subfolders deleted)"
        )

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """
        Get complete folder tree with subfolders and documents.

        GET /api/vault/folders/{id}/tree/

        Returns:
        {
            "id": "uuid",
            "encrypted_name": "base64...",
            "icon": "📁",
            "color": "#3b82f6",
            "document_count": 5,
            "subfolders": [
                {
                    "id": "uuid",
                    "encrypted_name": "base64...",
                    ...
                }
            ],
            "documents": [
                {
                    "id": "uuid",
                    "encrypted_title": "base64...",
                    ...
                }
            ]
        }
        """
        folder = self.get_object()
        tree = self._build_tree(folder)

        logger.info(f"📁 Folder tree requested: {folder.id}")

        return Response(tree)

    def _build_tree(self, folder):
        """
        Recursively build folder tree.

        Includes subfolders and documents at each level.
        """
        return {
            'id': str(folder.id),
            'encrypted_name': folder.encrypted_name,
            'icon': folder.icon,
            'color': folder.color,
            'document_count': folder.document_count,
            'created_at': folder.created_at,
            'subfolders': [
                self._build_tree(subfolder)
                for subfolder in folder.subfolders.all()
            ],
            'documents': DocumentSerializer(
                folder.documents.filter(is_deleted=False),
                many=True,
                context={'request': self.request}
            ).data
        }


# ============================================================================
# DOCUMENT VIEWSET (✅ UPDATED WITH FOLDER FILTERING)
# ============================================================================

class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for document management.

    Endpoints:
    - GET    /api/vault/documents/              - List user's documents
    - POST   /api/vault/documents/              - Upload new document
    - GET    /api/vault/documents/{id}/         - Get document details
    - PUT    /api/vault/documents/{id}/         - Update document
    - DELETE /api/vault/documents/{id}/         - Delete document (soft)
    - GET    /api/vault/documents/{id}/download/ - Download file
    - GET    /api/vault/documents/{id}/versions/ - List versions
    - POST   /api/vault/documents/move/         - Move documents to folder (✅ NEW)

    Query Parameters:
    - category: Filter by category ID (use 'all' for all categories)
    - folder: Filter by folder ID (use 'null' for root documents)
    """
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['encrypted_title', 'encrypted_doc_type']
    ordering_fields = ['created_at', 'file_size']
    ordering = ['-created_at']
    pagination_class = None

    def get_queryset(self):
        """
        Return only current user's non-deleted documents.

        Supports filtering by:
        - category: Get documents in specific category
        - folder: Get documents in specific folder or root documents
        """
        queryset = Document.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id and category_id != 'all':
            queryset = queryset.filter(category_id=category_id)
            logger.info(f"📄 Filtering documents by category: {category_id}")

        # ✅ NEW: Filter by folder
        folder_id = self.request.query_params.get('folder')
        if folder_id == 'null' or folder_id == '':
            # Get documents not in any folder (root documents)
            queryset = queryset.filter(folder__isnull=True)
            logger.info(f"📄 Getting root documents (no folder)")
        elif folder_id:
            # Get documents in specific folder
            queryset = queryset.filter(folder_id=folder_id)
            logger.info(f"📄 Filtering documents by folder: {folder_id}")

        return queryset.select_related('category', 'folder')

    def perform_create(self, serializer):
        """Create document for current user."""
        document = serializer.save(user=self.request.user)
        logger.info(f"📄 Document created: {document.id} by user {self.request.user.id}")

    def perform_destroy(self, instance):
        """
        Soft delete document and update user storage.
        """
        user = instance.user
        file_size = instance.file_size

        # Soft delete
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

        # Update user storage
        user.storage_used -= file_size
        user.save(update_fields=['storage_used'])

        logger.info(
            f"🗑️ Document soft deleted: {instance.id} "
            f"({file_size} bytes freed)"
        )

    def list(self, request):
        """List all documents for current user."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Upload new document.

        POST /api/vault/documents/
        Content-Type: multipart/form-data
        """
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        logger.warning(f"Document upload failed: {serializer.errors}")
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def destroy(self, request, pk=None):
        """
        Soft delete document.

        DELETE /api/vault/documents/{id}/
        """
        try:
            document = self.get_object()
            self.perform_destroy(document)

            return Response(
                {'success': True, 'message': 'Document deleted'},
                status=status.HTTP_200_OK
            )

        except Http404:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download encrypted document file.

        GET /api/vault/documents/{id}/download/
        """
        try:
            document = self.get_object()

            if not document.encrypted_file:
                return Response(
                    {'error': 'File not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Open and return file
            file_handle = document.encrypted_file.open('rb')
            response = FileResponse(
                file_handle,
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{pk}.enc"'

            logger.info(f"📥 Document downloaded: {pk} by user {request.user.id}")

            return response

        except Http404:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Download error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to download file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        List all versions of a document.

        GET /api/vault/documents/{id}/versions/
        """
        document = self.get_object()
        versions = DocumentVersion.objects.filter(
            document=document
        ).order_by('-version_number')

        serializer = DocumentVersionSerializer(
            versions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    # ✅ NEW: Move documents to folder
    @action(detail=False, methods=['post'])
    def move(self, request):
        """
        Move document(s) to a folder or root.

        POST /api/vault/documents/move/

        Request Body:
        {
            "document_ids": ["uuid1", "uuid2", ...],
            "folder_id": "folder-uuid" or null
        }

        Response:
        {
            "status": "success",
            "moved_count": 2,
            "folder_id": "folder-uuid" or null
        }
        """
        document_ids = request.data.get('document_ids', [])
        folder_id = request.data.get('folder_id')

        # Validate input
        if not document_ids:
            return Response(
                {'error': 'document_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(document_ids, list):
            return Response(
                {'error': 'document_ids must be an array'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get documents (verify ownership)
        documents = Document.objects.filter(
            id__in=document_ids,
            user=request.user,
            is_deleted=False
        )

        if not documents.exists():
            return Response(
                {'error': 'No documents found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get folder (verify ownership and existence)
        folder = None
        if folder_id:
            try:
                folder = Folder.objects.get(
                    id=folder_id,
                    user=request.user
                )
            except Folder.DoesNotExist:
                return Response(
                    {'error': 'Folder not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Move documents
        documents.update(folder=folder)

        logger.info(
            f"📁 Moved {documents.count()} documents to "
            f"{'folder ' + str(folder.id) if folder else 'root'} "
            f"by user {request.user.id}"
        )

        return Response({
            'status': 'success',
            'moved_count': documents.count(),
            'folder_id': str(folder.id) if folder else None
        })


# ============================================================================
# END OF VIEWS.PY
# ============================================================================
"""
Next Steps:
1. Replace your vault/views.py with this file
2. Restart Django server to load new views
3. Continue to STEP 4 (urls.py)
"""