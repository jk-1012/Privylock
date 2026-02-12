"""
Vault App URL Configuration - WITH FOLDER SUPPORT

============================================================================
STEP 4: URLS.PY - Register Folder Routes
============================================================================

✅ NEW: Folder ViewSet registration
✅ NEW: Folder management endpoints

Changes:
1. Registered FolderViewSet with router
2. Added folder endpoints documentation

============================================================================
AVAILABLE ENDPOINTS
============================================================================

Categories:
  GET    /api/vault/categories/           - List all categories
  GET    /api/vault/categories/{id}/      - Get category details

Folders: (✅ NEW)
  GET    /api/vault/folders/              - List user's folders
                                            Query params:
                                            - category: Filter by category ID
                                            - parent: Filter by parent folder ID
                                              (use 'null' for root folders)
  POST   /api/vault/folders/              - Create new folder
  GET    /api/vault/folders/{id}/         - Get folder details
  PATCH  /api/vault/folders/{id}/         - Update folder (name, color, icon)
  DELETE /api/vault/folders/{id}/         - Delete folder (documents preserved)
  GET    /api/vault/folders/{id}/tree/    - Get complete folder tree with
                                            subfolders and documents

Documents:
  GET    /api/vault/documents/            - List user's documents
                                            Query params:
                                            - category: Filter by category ID
                                            - folder: Filter by folder ID
                                              (use 'null' for root documents)
  POST   /api/vault/documents/            - Upload new document
  GET    /api/vault/documents/{id}/       - Get document details
  PUT    /api/vault/documents/{id}/       - Update document
  DELETE /api/vault/documents/{id}/       - Delete document (soft delete)
  GET    /api/vault/documents/{id}/download/ - Download encrypted file
  GET    /api/vault/documents/{id}/versions/ - List document versions
  POST   /api/vault/documents/move/       - Move documents to folder (✅ NEW)
                                            Request body:
                                            {
                                              "document_ids": ["uuid1", "uuid2"],
                                              "folder_id": "folder-uuid" or null
                                            }

============================================================================
EXAMPLE API CALLS
============================================================================

1. List all folders in a category:
   GET /api/vault/folders/?category=<category-uuid>

2. Get root folders only:
   GET /api/vault/folders/?category=<category-uuid>&parent=null

3. Create subfolder:
   POST /api/vault/folders/
   {
     "category": "<category-uuid>",
     "parent": "<parent-folder-uuid>",
     "encrypted_name": "base64-encrypted-name",
     "icon": "📁",
     "color": "#3b82f6"
   }

4. Get folder tree with all documents:
   GET /api/vault/folders/<folder-uuid>/tree/

5. Upload document to folder:
   POST /api/vault/documents/
   (multipart/form-data)
   - encrypted_file: File
   - folder: <folder-uuid>
   - category: <category-uuid>
   - encrypted_title: base64...
   - ...

6. Move documents to folder:
   POST /api/vault/documents/move/
   {
     "document_ids": ["doc-uuid-1", "doc-uuid-2"],
     "folder_id": "folder-uuid"
   }

7. Move documents to root (remove from folder):
   POST /api/vault/documents/move/
   {
     "document_ids": ["doc-uuid-1"],
     "folder_id": null
   }

8. Get documents in specific folder:
   GET /api/vault/documents/?folder=<folder-uuid>

9. Get root documents (no folder):
   GET /api/vault/documents/?folder=null

============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'vault'

# ============================================================================
# ROUTER CONFIGURATION
# ============================================================================

# Create router for ViewSets
router = DefaultRouter()

# Document Categories
router.register(
    r'categories',
    views.DocumentCategoryViewSet,
    basename='category'
)

# ✅ NEW: Folders - Hierarchical document organization
router.register(
    r'folders',
    views.FolderViewSet,
    basename='folder'
)

# Documents
router.register(
    r'documents',
    views.DocumentViewSet,
    basename='document'
)

# ============================================================================
# URL PATTERNS
# ============================================================================

urlpatterns = [
    # Include all router URLs
    path('', include(router.urls)),
]

# ============================================================================
# REGISTERED ENDPOINTS
# ============================================================================
"""
The DefaultRouter automatically generates these URL patterns:

Categories:
  ^categories/$
    [name='category-list']
    GET: List categories

  ^categories/(?P<pk>[^/.]+)/$
    [name='category-detail']
    GET: Retrieve category

Folders: (✅ NEW)
  ^folders/$
    [name='folder-list']
    GET: List folders
    POST: Create folder

  ^folders/(?P<pk>[^/.]+)/$
    [name='folder-detail']
    GET: Retrieve folder
    PUT: Update folder (full)
    PATCH: Update folder (partial)
    DELETE: Delete folder

  ^folders/(?P<pk>[^/.]+)/tree/$
    [name='folder-tree']
    GET: Get folder tree

Documents:
  ^documents/$
    [name='document-list']
    GET: List documents
    POST: Create document

  ^documents/(?P<pk>[^/.]+)/$
    [name='document-detail']
    GET: Retrieve document
    PUT: Update document (full)
    PATCH: Update document (partial)
    DELETE: Delete document

  ^documents/(?P<pk>[^/.]+)/download/$
    [name='document-download']
    GET: Download document

  ^documents/(?P<pk>[^/.]+)/versions/$
    [name='document-versions']
    GET: List document versions

  ^documents/move/$
    [name='document-move'] (✅ NEW)
    POST: Move documents to folder
"""

# ============================================================================
# FUTURE ENHANCEMENTS (Commented out for now)
# ============================================================================
#
# Additional custom endpoints to consider:
#
# urlpatterns += [
#     # Global search across all documents
#     path('search/', views.search_documents, name='search'),
#
#     # Storage statistics
#     path('stats/', views.get_statistics, name='statistics'),
#
#     # Bulk operations
#     path('documents/bulk-delete/', views.bulk_delete_documents, name='bulk-delete'),
#     path('folders/bulk-create/', views.bulk_create_folders, name='bulk-create-folders'),
#
#     # Export operations
#     path('folders/<uuid:pk>/export/', views.export_folder, name='export-folder'),
#     path('documents/<uuid:pk>/export/', views.export_document, name='export-document'),
#
#     # Sharing (for future family sharing feature)
#     path('documents/<uuid:pk>/share/', views.share_document, name='share-document'),
#     path('folders/<uuid:pk>/share/', views.share_folder, name='share-folder'),
#
#     # Templates
#     path('templates/', views.list_templates, name='list-templates'),
#     path('templates/<uuid:pk>/apply/', views.apply_template, name='apply-template'),
# ]

# ============================================================================
# IMPLEMENTATION NOTES
# ============================================================================
#
# 1. All ViewSets get standard REST endpoints via DefaultRouter
# 2. Custom actions defined with @action decorator in views.py
# 3. URL patterns auto-registered by DefaultRouter
# 4. All endpoints require authentication (IsAuthenticated permission)
# 5. All responses filtered by request.user (user isolation)
# 6. Folder operations support hierarchical organization
# 7. Documents can be organized in folders or remain at root level
#
# ============================================================================

# ============================================================================
# END OF URLS.PY
# ============================================================================
"""
Next Steps:
1. Replace your vault/urls.py with this file
2. Restart Django server
3. Continue to STEP 5 (Run Migrations)
"""