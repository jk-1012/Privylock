/**
 * FolderTree Component - WITH FOLDER ACTIONS
 *
 * ✅ PRODUCTION READY - ESLint compliant
 * ✅ NEW: Right-click menu on folders
 * ✅ NEW: Rename folder option
 * ✅ NEW: Delete folder option
 * ✅ NEW: Three-dot menu for each folder
 */

import React, { useState, useEffect, useRef } from 'react';
import apiService from '../../services/apiService';
import encryptionService from '../../services/encryptionService';
import './FolderTree.css';

const FolderTree = ({ categoryId, onFolderSelect, selectedFolder, onCreateFolder }) => {
  const [folders, setFolders] = useState([]);
  const [expandedFolders, setExpandedFolders] = useState(new Set());
  const [loading, setLoading] = useState(false);

  // ✅ NEW: Folder menu state
  const [folderMenu, setFolderMenu] = useState(null); // { folderId, x, y }
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [renamingFolder, setRenamingFolder] = useState(null);
  const [newFolderName, setNewFolderName] = useState('');

  const menuRef = useRef(null);

  useEffect(() => {
    if (categoryId) {
      loadFolders();
    }
    // ✅ FIXED: ESLint warning suppressed (loadFolders changes on every render)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryId]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setFolderMenu(null);
      }
    };

    if (typeof window !== 'undefined') {
      window.document.addEventListener('mousedown', handleClickOutside);
      return () => window.document.removeEventListener('mousedown', handleClickOutside);
    }
  }, []);

  /**
   * Load and decrypt folders
   */
  const loadFolders = async () => {
    try {
      setLoading(true);
      console.log('📁 Loading folders for category:', categoryId);

      const response = await apiService.getFolders(categoryId);
      console.log('✅ Folders loaded:', response.data);

      const folderData = Array.isArray(response.data)
        ? response.data
        : (response.data.results || []);

      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        console.error('❌ No master key found');
        return;
      }

      const decryptedFolders = await Promise.all(
        folderData.map(async (folder) => {
          try {
            const decryptedName = await encryptionService.decryptText(
              folder.encrypted_name,
              masterKey
            );
            return {
              ...folder,
              name: decryptedName
            };
          } catch (err) {
            console.error('Failed to decrypt folder name:', err);
            return {
              ...folder,
              name: 'Encrypted Folder'
            };
          }
        })
      );

      const tree = buildTree(decryptedFolders);
      setFolders(tree);

    } catch (error) {
      console.error('❌ Failed to load folders:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Build hierarchical tree
   */
  const buildTree = (folders) => {
    const map = {};
    const tree = [];

    folders.forEach(folder => {
      map[folder.id] = { ...folder, children: [] };
    });

    folders.forEach(folder => {
      if (folder.parent) {
        if (map[folder.parent]) {
          map[folder.parent].children.push(map[folder.id]);
        }
      } else {
        tree.push(map[folder.id]);
      }
    });

    return tree;
  };

  /**
   * Toggle folder expand/collapse
   */
  const toggleFolder = (folderId) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  /**
   * ✅ NEW: Handle folder right-click
   */
  const handleFolderContextMenu = (e, folder) => {
    e.preventDefault();
    e.stopPropagation();

    setFolderMenu({
      folderId: folder.id,
      folderName: folder.name,
      x: e.clientX,
      y: e.clientY
    });
  };

  /**
   * ✅ NEW: Rename folder
   */
  const handleRenameFolder = async () => {
    if (!newFolderName || !renamingFolder) return;

    try {
      console.log('✏️ Renaming folder:', renamingFolder.id, 'to:', newFolderName);

      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found');
      }

      const encryptedName = await encryptionService.encryptText(newFolderName, masterKey);

      await apiService.updateFolder(renamingFolder.id, {
        encrypted_name: encryptedName
      });

      console.log('✅ Folder renamed successfully!');
      setShowRenameModal(false);
      setRenamingFolder(null);
      setNewFolderName('');
      loadFolders(); // Reload

    } catch (error) {
      console.error('❌ Failed to rename folder:', error);
      alert('Failed to rename folder. Please try again.');
    }
  };

  /**
   * ✅ NEW: Delete folder
   */
  const handleDeleteFolder = async (folder) => {
    if (!window.confirm(`Delete folder "${folder.name}"?\n\nDocuments inside will be moved to root.`)) {
      return;
    }

    try {
      console.log('🗑️ Deleting folder:', folder.id);

      await apiService.deleteFolder(folder.id);

      console.log('✅ Folder deleted successfully!');
      setFolderMenu(null);

      // If we were viewing this folder, go back to root
      if (selectedFolder?.id === folder.id) {
        onFolderSelect(null);
      }

      loadFolders(); // Reload

    } catch (error) {
      console.error('❌ Failed to delete folder:', error);
      alert('Failed to delete folder. Please try again.');
    }
  };

  /**
   * Render single folder with actions
   */
  const renderFolder = (folder, level = 0) => {
    const isExpanded = expandedFolders.has(folder.id);
    const hasChildren = folder.children && folder.children.length > 0;
    const isSelected = selectedFolder?.id === folder.id;

    return (
      <div key={folder.id} className="folder-item">
        <div
          className={`folder-header ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${level * 20 + 10}px` }}
          onClick={() => onFolderSelect(folder)}
          onContextMenu={(e) => handleFolderContextMenu(e, folder)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFolder(folder.id);
              }}
              className="folder-toggle"
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}

          <span className="folder-icon" style={{ color: folder.color }}>
            {folder.icon}
          </span>

          <span className="folder-name">{folder.name}</span>

          <span className="folder-count">({folder.document_count || 0})</span>

          {/* ✅ NEW: Three-dot menu for folder */}
          <button
            className="folder-menu-btn"
            onClick={(e) => {
              e.stopPropagation();
              setFolderMenu({
                folderId: folder.id,
                folderName: folder.name,
                x: e.clientX,
                y: e.clientY
              });
            }}
            title="Folder options"
          >
            ⋮
          </button>
        </div>

        {isExpanded && hasChildren && (
          <div className="folder-children">
            {folder.children.map(child => renderFolder(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="folder-tree">
        <div className="folder-loading">Loading folders...</div>
      </div>
    );
  }

  return (
    <div className="folder-tree">
      <div
        className={`folder-header root ${!selectedFolder ? 'selected' : ''}`}
        onClick={() => onFolderSelect(null)}
      >
        <span className="folder-icon">📁</span>
        <span className="folder-name">All Documents</span>
      </div>

      {folders.length > 0 ? (
        folders.map(folder => renderFolder(folder))
      ) : (
        <div style={{ padding: '10px', textAlign: 'center', color: '#999', fontSize: '12px' }}>
          No folders yet
        </div>
      )}

      <button
        className="btn-create-folder"
        onClick={onCreateFolder}
      >
        + New Folder
      </button>

      {/* ✅ NEW: Context Menu */}
      {folderMenu && (
        <div
          ref={menuRef}
          className="folder-context-menu"
          style={{
            position: 'fixed',
            top: folderMenu.y,
            left: folderMenu.x,
            zIndex: 10000
          }}
        >
          <button
            className="context-menu-item"
            onClick={() => {
              const folder = folders.find(f => f.id === folderMenu.folderId);
              setRenamingFolder(folder);
              setNewFolderName(folderMenu.folderName);
              setShowRenameModal(true);
              setFolderMenu(null);
            }}
          >
            <span className="menu-icon">✏️</span>
            <span>Rename</span>
          </button>

          <div className="context-menu-divider"></div>

          <button
            className="context-menu-item danger"
            onClick={() => {
              const folder = folders.find(f => f.id === folderMenu.folderId);
              handleDeleteFolder(folder);
            }}
          >
            <span className="menu-icon">🗑️</span>
            <span>Delete</span>
          </button>
        </div>
      )}

      {/* ✅ NEW: Rename Modal */}
      {showRenameModal && renamingFolder && (
        <div className="modal-overlay" onClick={() => setShowRenameModal(false)}>
          <div className="modal-content small-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Rename Folder</h3>
              <button onClick={() => setShowRenameModal(false)} className="btn-close">×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="newFolderName">New Name</label>
                <input
                  type="text"
                  id="newFolderName"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="Enter new folder name"
                  autoFocus
                />
              </div>
            </div>

            <div className="modal-actions">
              <button onClick={() => setShowRenameModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleRenameFolder}
                className="btn-primary"
                disabled={!newFolderName || newFolderName === renamingFolder.name}
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FolderTree;