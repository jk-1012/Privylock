/**
 * CreateFolderModal Component - Modal for creating new folders
 *
 * Location: src/components/vault/CreateFolderModal.jsx
 *
 * Features:
 * - Enter folder name
 * - Choose folder icon
 * - Choose folder color
 * - Select parent folder (optional)
 * - Encrypt folder name before sending to server
 */

import React, { useState } from 'react';
import apiService from '../../services/apiService';
import encryptionService from '../../services/encryptionService';
import './CreateFolderModal.css';

const CreateFolderModal = ({ categoryId, parentFolder, onClose, onSuccess }) => {
  const [folderName, setFolderName] = useState('');
  const [icon, setIcon] = useState('📁');
  const [color, setColor] = useState('#3b82f6');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  // Available icons
  const icons = [
    '📁', '👨', '👩', '👶', '👴', '👵',
    '🚗', '🏍️', '🚙', '🏠', '🏢', '🏗️',
    '💰', '💳', '📊', '🎓', '📚', '🏥',
    '⚖️', '📄', '🔐', '🎯', '⭐', '🌟'
  ];

  // Available colors
  const colors = [
    '#3b82f6', // Blue
    '#ef4444', // Red
    '#10b981', // Green
    '#f59e0b', // Orange
    '#8b5cf6', // Purple
    '#ec4899', // Pink
    '#06b6d4', // Cyan
    '#84cc16', // Lime
  ];

  /**
   * Handle form submission
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!folderName.trim()) {
      setError('Please enter a folder name');
      return;
    }

    try {
      setCreating(true);
      setError('');

      console.log('📁 Creating folder:', folderName);

      // Get master key
      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found. Please login again.');
      }

      // Encrypt folder name
      const encryptedName = await encryptionService.encryptText(
        folderName,
        masterKey
      );

      console.log('✅ Folder name encrypted');

      // Create folder
      const folderData = {
        category: categoryId,
        parent: parentFolder?.id || null,
        encrypted_name: encryptedName,
        icon: icon,
        color: color
      };

      console.log('📤 Sending folder data:', {
        ...folderData,
        encrypted_name: encryptedName.substring(0, 20) + '...'
      });

      await apiService.post('/vault/folders/', folderData);

      console.log('✅ Folder created successfully!');

      // Success - close modal and refresh
      onSuccess();

    } catch (error) {
      console.error('❌ Failed to create folder:', error);
      setError(error.response?.data?.error || error.message || 'Failed to create folder');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content create-folder-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📁 Create New Folder</h2>
          <button onClick={onClose} className="btn-close">×</button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {/* Parent folder info */}
          {parentFolder && (
            <div className="parent-folder-info">
              <small>Creating subfolder in:</small>
              <div className="parent-folder-name">
                {parentFolder.icon} {parentFolder.name}
              </div>
            </div>
          )}

          {/* Folder name input */}
          <div className="form-group">
            <label htmlFor="folderName">Folder Name *</label>
            <input
              type="text"
              id="folderName"
              value={folderName}
              onChange={(e) => setFolderName(e.target.value)}
              placeholder="e.g., Person 1, MH-01-AB-1234, Mumbai House"
              required
              disabled={creating}
              autoFocus
            />
            <small className="form-hint">
              Examples: "Father - Rajesh", "Car MH-01-AB-1234", "Flat 301 Mumbai"
            </small>
          </div>

          {/* Icon picker */}
          <div className="form-group">
            <label>Folder Icon</label>
            <div className="icon-picker">
              {icons.map(emoji => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setIcon(emoji)}
                  className={`icon-option ${icon === emoji ? 'selected' : ''}`}
                  disabled={creating}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          {/* Color picker */}
          <div className="form-group">
            <label>Folder Color</label>
            <div className="color-picker">
              {colors.map(c => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  className={`color-option ${color === c ? 'selected' : ''}`}
                  style={{ backgroundColor: c }}
                  disabled={creating}
                  title={c}
                />
              ))}
            </div>
          </div>

          {/* Preview */}
          <div className="form-group">
            <label>Preview</label>
            <div className="folder-preview">
              <span className="preview-icon" style={{ color: color }}>
                {icon}
              </span>
              <span className="preview-name">
                {folderName || 'Folder Name'}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={creating}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="btn-primary"
              disabled={creating || !folderName.trim()}
            >
              {creating ? 'Creating...' : 'Create Folder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateFolderModal;