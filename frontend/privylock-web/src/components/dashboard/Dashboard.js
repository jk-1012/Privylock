/**
 * Dashboard Component - COMPLETE FOR PRIVYLOCK
 *
 * CHANGES FROM LIFEVAULT:
 * ✅ Changed LifeVault → PrivyLock branding
 * ✅ Added NotificationBell component
 * ✅ Preserved DocumentViewer functionality
 * ✅ Preserved FolderTree and all existing features
 * ✅ All existing functionality intact
 * ✅ Proper folder filtering
 * ✅ Document encryption/decryption
 * ✅ Upload, download, delete, rename, move operations
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import apiService from '../../services/apiService';
import encryptionService from '../../services/encryptionService';
import fileService from '../../services/fileService';
import DocumentCard from './DocumentCard';
import DocumentViewer from './DocumentViewer';
import UploadModal from './UploadModal';
import FolderTree from '../vault/FolderTree';
import CreateFolderModal from '../vault/CreateFolderModal';
import NotificationBell from '../notifications/NotificationBell';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Document viewer state
  const [viewingDocument, setViewingDocument] = useState(null);
  const [showViewer, setShowViewer] = useState(false);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory, selectedFolder]);

  /**
   * Load all dashboard data with proper folder filtering
   */
  const loadData = async () => {
    try {
      setError('');
      setLoading(true);
      console.log('📥 Loading dashboard data...');
      console.log('  Category:', selectedCategory);
      console.log('  Folder:', selectedFolder);

      // Load categories
      const catsResponse = await apiService.getCategories();
      const categoriesData = Array.isArray(catsResponse.data)
        ? catsResponse.data
        : (catsResponse.data.results || []);

      console.log('✅ Categories loaded:', categoriesData.length);
      setCategories(categoriesData);

      // Load folders for current category
      if (selectedCategory && selectedCategory !== 'all') {
        try {
          const foldersResponse = await apiService.getFolders(selectedCategory);
          const foldersData = Array.isArray(foldersResponse.data)
            ? foldersResponse.data
            : (foldersResponse.data.results || []);

          const masterKey = encryptionService.getMasterKey();
          if (masterKey) {
            const decryptedFolders = await Promise.all(
              foldersData.map(async (folder) => {
                try {
                  const decryptedName = await encryptionService.decryptText(
                    folder.encrypted_name,
                    masterKey
                  );
                  return { ...folder, name: decryptedName };
                } catch (err) {
                  console.error('Failed to decrypt folder name:', err);
                  return { ...folder, name: 'Encrypted Folder' };
                }
              })
            );
            setFolders(decryptedFolders);
            console.log('✅ Folders loaded:', decryptedFolders.length);
          }
        } catch (err) {
          console.error('Failed to load folders:', err);
          setFolders([]);
        }
      } else {
        setFolders([]);
      }

      // Build query params for proper filtering
      const params = {};

      // Filter by category
      if (selectedCategory && selectedCategory !== 'all') {
        params.category = selectedCategory;
        console.log('  → Filtering by category:', selectedCategory);
      }

      // Filter by folder (or root)
      if (selectedFolder) {
        // Show ONLY documents IN this folder
        params.folder = selectedFolder.id;
        console.log('  → Filtering by folder:', selectedFolder.id, selectedFolder.name);
      } else if (selectedCategory !== 'all') {
        // When in category but NO folder selected, show ONLY root documents
        params.folder = 'null';
        console.log('  → Showing ROOT documents only (folder=null)');
      }

      // Load documents
      console.log('📥 Fetching documents with params:', params);
      const docsResponse = await apiService.getDocuments(params);
      const documentsData = Array.isArray(docsResponse.data)
        ? docsResponse.data
        : (docsResponse.data.results || []);

      console.log('✅ Documents loaded:', documentsData.length);

      // Get master key
      const masterKey = encryptionService.getMasterKey();

      if (!masterKey) {
        console.error('❌ No master key found!');
        setError('Session expired. Please login again.');
        logout();
        return;
      }

      // Decrypt documents
      const docsWithDecrypted = await Promise.all(
        documentsData.map(async (doc) => {
          try {
            let decryptedTitle = 'Untitled';
            if (doc.encrypted_title) {
              try {
                decryptedTitle = await encryptionService.decryptText(
                  doc.encrypted_title,
                  masterKey
                );
              } catch (err) {
                console.error(`Failed to decrypt title for ${doc.id}:`, err);
              }
            }

            let decryptedDescription = '';
            if (doc.encrypted_description) {
              try {
                decryptedDescription = await encryptionService.decryptText(
                  doc.encrypted_description,
                  masterKey
                );
              } catch (err) {
                console.error(`Failed to decrypt description:`, err);
              }
            }

            let decryptedDocType = 'Other';
            if (doc.encrypted_doc_type) {
              try {
                decryptedDocType = await encryptionService.decryptText(
                  doc.encrypted_doc_type,
                  masterKey
                );
              } catch (err) {
                console.error(`Failed to decrypt doc type:`, err);
              }
            }

            return {
              ...doc,
              title: decryptedTitle,
              description: decryptedDescription,
              docType: decryptedDocType,
            };
          } catch (err) {
            console.error(`Failed to decrypt document ${doc.id}:`, err);
            return {
              ...doc,
              title: 'Encrypted (unable to decrypt)',
              description: '',
              docType: 'Unknown',
            };
          }
        })
      );

      setDocuments(docsWithDecrypted);
      console.log('✅ Dashboard loaded successfully!');
      console.log('  → Showing', docsWithDecrypted.length, 'documents');

    } catch (error) {
      console.error('❌ Failed to load data:', error);
      setError('Failed to load dashboard. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle view document
   */
  const handleView = (document) => {
    console.log('👁️ Opening document viewer:', document.title);
    setViewingDocument(document);
    setShowViewer(true);
  };

  /**
   * Handle moving documents to folder
   */
  const handleMoveDocuments = async (documentIds, folderId) => {
    try {
      console.log('📁 Moving documents:', documentIds, 'to folder:', folderId);

      await apiService.moveDocuments(documentIds, folderId);

      console.log('✅ Documents moved successfully!');

      // Reload to show updated organization
      loadData();

    } catch (error) {
      console.error('❌ Failed to move documents:', error);
      alert('Failed to move documents. Please try again.');
    }
  };

  /**
   * Handle renaming document
   */
  const handleRenameDocument = async (documentId, newTitle) => {
    try {
      console.log('✏️ Renaming document:', documentId, 'to:', newTitle);

      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found');
      }

      const encryptedTitle = await encryptionService.encryptText(newTitle, masterKey);

      await apiService.updateDocument(documentId, {
        encrypted_title: encryptedTitle
      });

      console.log('✅ Document renamed successfully!');
      loadData();

    } catch (error) {
      console.error('❌ Failed to rename document:', error);
      alert('Failed to rename document. Please try again.');
    }
  };

  const handleUploadSuccess = () => {
    setShowUpload(false);
    loadData();
  };

  const handleFolderCreated = () => {
    setShowCreateFolder(false);
    loadData();
  };

  const handleFolderSelect = (folder) => {
    console.log('📁 Folder selected:', folder);
    setSelectedFolder(folder);
  };

  const handleDownload = async (document) => {
    try {
      console.log('📥 Downloading:', document.title);
      await fileService.downloadDocument(
        document.id,
        `${document.title}.${document.file_extension}`
      );
      console.log('✅ Download successful!');
    } catch (error) {
      console.error('❌ Download failed:', error);
      alert('Failed to download document. Please try again.');
    }
  };

  const handleDelete = async (id) => {
    const doc = documents.find(d => d.id === id);

    if (window.confirm(`Are you sure you want to delete "${doc?.title}"?`)) {
      try {
        await apiService.deleteDocument(id);
        console.log('✅ Document deleted');
        loadData();
      } catch (error) {
        console.error('❌ Delete failed:', error);
        alert('Failed to delete document');
      }
    }
  };

  const filteredDocs = documents.filter(doc => {
    const searchMatch = !searchQuery ||
                       doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                       doc.docType.toLowerCase().includes(searchQuery.toLowerCase());
    return searchMatch;
  });

  const getStoragePercentage = () => {
    if (!user) return 0;
    const limits = {
      'FREE': 1073741824,        // 1 GB
      'PREMIUM': 26843545600,    // 25 GB
      'FAMILY': 107374182400,    // 100 GB
      'LIFETIME': 10737418240,   // 10 GB
    };
    const limit = limits[user.subscription_tier] || limits.FREE;
    return (user.storage_used / limit) * 100;
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading your vault...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-brand">
          {/* ✅ CHANGED: LifeVault → PrivyLock */}
          <h1>🔐 PrivyLock</h1>
        </div>

        <div className="navbar-actions">
          <div className="storage-indicator">
            <small>Storage: {formatBytes(user?.storage_used || 0)}</small>
            <div className="storage-bar">
              <div
                className="storage-fill"
                style={{ width: `${getStoragePercentage()}%` }}
              ></div>
            </div>
          </div>

          {/* ✅ ADDED: Notification Bell */}
          <NotificationBell />

          <span className="user-badge">{user?.subscription_tier || 'FREE'}</span>

          <button onClick={logout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-main">
        {selectedCategory !== 'all' && (
          <aside className="dashboard-sidebar">
            <FolderTree
              categoryId={selectedCategory}
              onFolderSelect={handleFolderSelect}
              selectedFolder={selectedFolder}
              onCreateFolder={() => setShowCreateFolder(true)}
            />
          </aside>
        )}

        <div className="dashboard-content">
          {error && (
            <div className="error-banner">
              ⚠️ {error}
            </div>
          )}

          <div className="dashboard-header">
            <div className="header-left">
              <div className="breadcrumb">
                <span
                  className="breadcrumb-item clickable"
                  onClick={() => {
                    setSelectedCategory('all');
                    setSelectedFolder(null);
                  }}
                >
                  All Documents
                </span>
                {selectedCategory !== 'all' && (
                  <>
                    <span className="breadcrumb-separator">›</span>
                    <span
                      className="breadcrumb-item clickable"
                      onClick={() => setSelectedFolder(null)}
                    >
                      {categories.find(c => c.id === selectedCategory)?.name}
                    </span>
                  </>
                )}
                {selectedFolder && (
                  <>
                    <span className="breadcrumb-separator">›</span>
                    <span className="breadcrumb-item active">
                      {selectedFolder.icon} {selectedFolder.name}
                    </span>
                  </>
                )}
              </div>

              <h2>My Documents ({filteredDocs.length})</h2>

              <div className="search-box">
                <input
                  type="text"
                  placeholder="🔍 Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <button
              onClick={() => setShowUpload(true)}
              className="btn-upload"
            >
              + Upload Document
            </button>
          </div>

          <div className="categories-filter">
            <button
              className={selectedCategory === 'all' ? 'active' : ''}
              onClick={() => {
                setSelectedCategory('all');
                setSelectedFolder(null);
              }}
            >
              📁 All Documents
            </button>

            {categories.map(cat => (
              <button
                key={cat.id}
                className={selectedCategory === cat.id ? 'active' : ''}
                onClick={() => {
                  setSelectedCategory(cat.id);
                  setSelectedFolder(null);
                }}
              >
                {cat.icon} {cat.name}
              </button>
            ))}
          </div>

          <div className="documents-grid">
            {filteredDocs.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📄</div>
                <h3>No documents yet</h3>
                <p>
                  {searchQuery
                    ? `No documents match "${searchQuery}"`
                    : selectedFolder
                    ? `This folder is empty`
                    : 'Upload your first document to get started!'
                  }
                </p>
                {!searchQuery && (
                  <button
                    onClick={() => setShowUpload(true)}
                    className="btn-upload"
                  >
                    + Upload Document
                  </button>
                )}
              </div>
            ) : (
              filteredDocs.map(doc => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onView={handleView}
                  onDownload={handleDownload}
                  onDelete={handleDelete}
                  onMove={handleMoveDocuments}
                  onRename={handleRenameDocument}
                  folders={folders}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {showUpload && (
        <UploadModal
          categories={categories}
          selectedCategory={selectedCategory}
          selectedFolder={selectedFolder}
          onClose={() => setShowUpload(false)}
          onSuccess={handleUploadSuccess}
        />
      )}

      {showCreateFolder && (
        <CreateFolderModal
          categoryId={selectedCategory}
          parentFolder={selectedFolder}
          onClose={() => setShowCreateFolder(false)}
          onSuccess={handleFolderCreated}
        />
      )}

      {/* ✅ Document Viewer Modal */}
      {showViewer && viewingDocument && (
        <DocumentViewer
          document={viewingDocument}
          onClose={() => {
            setShowViewer(false);
            setViewingDocument(null);
          }}
        />
      )}
    </div>
  );
};

export default Dashboard;