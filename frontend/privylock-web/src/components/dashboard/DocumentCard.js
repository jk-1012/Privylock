/**
 * DocumentCard Component - GOOGLE DRIVE STYLE
 *
 * ✅ Visible buttons: View, Download only
 * ✅ Three-dot menu: Download, Move, Rename, Delete
 */

import React, { useState, useRef, useEffect } from 'react';
import './DocumentCard.css';

const DocumentCard = ({ document, onDownload, onDelete, onView, onMove, onRename, folders }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showMoveModal, setShowMoveModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [newTitle, setNewTitle] = useState(document.title);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    if (typeof window !== 'undefined') {
      window.document.addEventListener('mousedown', handleClickOutside);
      return () => window.document.removeEventListener('mousedown', handleClickOutside);
    }
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (extension) => {
    const icons = {
      'pdf': '📄',
      'doc': '📝',
      'docx': '📝',
      'jpg': '🖼️',
      'jpeg': '🖼️',
      'png': '🖼️',
      'gif': '🖼️',
      'txt': '📃',
      'xls': '📊',
      'xlsx': '📊',
    };
    return icons[extension?.toLowerCase()] || '📎';
  };

  const handleRename = () => {
    if (newTitle && newTitle !== document.title && onRename) {
      onRename(document.id, newTitle);
      setShowRenameModal(false);
    }
  };

  const handleMove = (folderId) => {
    if (onMove) {
      onMove([document.id], folderId);
      setShowMoveModal(false);
    }
  };

  return (
    <>
      <div className="document-card">
        {/* Document Icon */}
        <div className="document-icon">
          {getFileIcon(document.file_extension)}
        </div>

        {/* Document Info */}
        <div className="document-info">
          <h3 className="document-title">{document.title}</h3>

          <div className="document-meta">
            <span className="doc-type">{document.docType}</span>
            <span className="separator">•</span>
            <span className="file-size">{formatSize(document.file_size)}</span>
          </div>

          {document.description && (
            <p className="document-description">
              {document.description}
            </p>
          )}

          <div className="document-footer">
            <span className="upload-date">
              📅 {formatDate(document.created_at)}
            </span>

            {document.category_details && (
              <span className="category-badge">
                {document.category_details.icon} {document.category_details.name}
              </span>
            )}
          </div>
        </div>

        {/* Three-dot menu button */}
        <div className="document-menu-container" ref={menuRef}>
          <button
            className="btn-menu"
            onClick={() => setShowMenu(!showMenu)}
            title="More actions"
          >
            ⋮
          </button>

          {/* Dropdown menu */}
          {showMenu && (
            <div className="document-dropdown-menu">
              {onView && (
                <button
                  onClick={() => {
                    onView(document);
                    setShowMenu(false);
                  }}
                  className="menu-item"
                >
                  <span className="menu-icon">👁️</span>
                  <span>View</span>
                </button>
              )}

              <button
                onClick={() => {
                  onDownload(document);
                  setShowMenu(false);
                }}
                className="menu-item"
              >
                <span className="menu-icon">⬇️</span>
                <span>Download</span>
              </button>

              {onMove && (
                <button
                  onClick={() => {
                    setShowMoveModal(true);
                    setShowMenu(false);
                  }}
                  className="menu-item"
                >
                  <span className="menu-icon">📁</span>
                  <span>Move to folder</span>
                </button>
              )}

              {onRename && (
                <button
                  onClick={() => {
                    setShowRenameModal(true);
                    setShowMenu(false);
                  }}
                  className="menu-item"
                >
                  <span className="menu-icon">✏️</span>
                  <span>Rename</span>
                </button>
              )}

              <div className="menu-divider"></div>

              <button
                onClick={() => {
                  onDelete(document.id);
                  setShowMenu(false);
                }}
                className="menu-item danger"
              >
                <span className="menu-icon">🗑️</span>
                <span>Delete</span>
              </button>
            </div>
          )}
        </div>

        {/* ✅ FIXED: Only View and Download buttons visible */}
        <div className="document-actions">
          {onView && (
            <button
              onClick={() => onView(document)}
              className="btn-action btn-view"
              title="View"
            >
              👁️ View
            </button>
          )}

          <button
            onClick={() => onDownload(document)}
            className="btn-action btn-download"
            title="Download"
          >
            ⬇️ Download
          </button>
        </div>
      </div>

      {/* Move Modal */}
      {showMoveModal && onMove && (
        <div className="modal-overlay" onClick={() => setShowMoveModal(false)}>
          <div className="modal-content small-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Move to Folder</h3>
              <button onClick={() => setShowMoveModal(false)} className="btn-close">×</button>
            </div>

            <div className="modal-body">
              <p>Select destination folder for "{document.title}":</p>

              <div className="folder-list">
                <button
                  onClick={() => handleMove(null)}
                  className="folder-option"
                >
                  <span className="folder-icon">📁</span>
                  <span>Root (No folder)</span>
                </button>

                {folders && folders.length > 0 ? (
                  folders.map(folder => (
                    <button
                      key={folder.id}
                      onClick={() => handleMove(folder.id)}
                      className="folder-option"
                      disabled={folder.id === document.folder}
                    >
                      <span className="folder-icon" style={{ color: folder.color }}>
                        {folder.icon}
                      </span>
                      <span>{folder.name}</span>
                      {folder.id === document.folder && (
                        <span className="current-badge">Current</span>
                      )}
                    </button>
                  ))
                ) : (
                  <p style={{ color: '#999', fontSize: '14px', textAlign: 'center', padding: '20px' }}>
                    No folders available
                  </p>
                )}
              </div>
            </div>

            <div className="modal-actions">
              <button onClick={() => setShowMoveModal(false)} className="btn-secondary">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rename Modal */}
      {showRenameModal && onRename && (
        <div className="modal-overlay" onClick={() => setShowRenameModal(false)}>
          <div className="modal-content small-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Rename Document</h3>
              <button onClick={() => setShowRenameModal(false)} className="btn-close">×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="newTitle">New Name</label>
                <input
                  type="text"
                  id="newTitle"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Enter new name"
                  autoFocus
                />
              </div>
            </div>

            <div className="modal-actions">
              <button onClick={() => setShowRenameModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleRename}
                className="btn-primary"
                disabled={!newTitle || newTitle === document.title}
              >
                Rename
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentCard;