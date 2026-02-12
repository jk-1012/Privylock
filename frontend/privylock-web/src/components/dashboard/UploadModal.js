/**
 * UploadModal Component - FIXED FOR FOLDER SUPPORT
 *
 * ✅ FIXED: Auto-selects category based on current view
 * ✅ FIXED: Uploads to selected folder
 * ✅ FIXED: Shows current folder context
 */

import React, { useState } from 'react';
import fileService from '../../services/fileService';
import './UploadModal.css';

const UploadModal = ({ categories, selectedCategory, selectedFolder, onClose, onSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  // ✅ FIXED: Auto-select category if provided
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    docType: '',
    category: selectedCategory && selectedCategory !== 'all' ? selectedCategory : '',  // ✅ Auto-select
    folder: selectedFolder?.id || '',  // ✅ Auto-select folder
    hasExpiry: false,
    issueDate: '',
    expiryDate: '',
  });

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    setError('');

    if (!fileService.validateFileSize(file, 10 * 1024 * 1024)) {
      setError('File size must be less than 10MB');
      return;
    }

    if (!fileService.validateFileType(file)) {
      setError('File type not supported. Please upload PDF, images, or Office documents.');
      return;
    }

    setSelectedFile(file);

    if (!formData.title) {
      const name = file.name.split('.').slice(0, -1).join('.');
      setFormData({
        ...formData,
        title: name
      });
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;

    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    if (!formData.title) {
      setError('Please enter a document title');
      return;
    }

    if (!formData.category) {
      setError('Please select a category');
      return;
    }

    if (formData.hasExpiry && !formData.expiryDate) {
      setError('Please enter an expiry date');
      return;
    }

    setUploading(true);
    setError('');
    setProgress(0);

    console.log('📋 Upload Form Data:', formData);
    console.log('📂 Category:', formData.category);
    console.log('📁 Folder:', formData.folder);

    let progressInterval = null;

    try {
      progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      // ✅ FIXED: Include folder in metadata
      const metadata = {
        title: formData.title,
        description: formData.description,
        docType: formData.docType || formData.title,
        category: formData.category,
        folder: formData.folder || null,  // ✅ Send folder ID
        hasExpiry: formData.hasExpiry,
        issueDate: formData.issueDate,
        expiryDate: formData.expiryDate,
      };

      console.log('📤 Uploading with metadata:', metadata);

      await fileService.uploadDocument(selectedFile, metadata);

      if (progressInterval) {
        clearInterval(progressInterval);
      }

      setProgress(100);
      console.log('✅ Upload successful!');

      setTimeout(() => {
        onSuccess();
      }, 500);

    } catch (error) {
      console.error('❌ Upload failed:', error);

      if (progressInterval) {
        clearInterval(progressInterval);
      }

      setError(error.message || 'Upload failed. Please try again.');
      setUploading(false);
      setProgress(0);
    }
  };

  if (!categories || categories.length === 0) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h2>📤 Upload Document</h2>
            <button onClick={onClose} className="btn-close">×</button>
          </div>
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <p>Loading categories...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📤 Upload Document</h2>
          <button onClick={onClose} className="btn-close">×</button>
        </div>

        {/* ✅ NEW: Show upload context */}
        {(selectedCategory !== 'all' || selectedFolder) && (
          <div className="upload-context">
            <small>Uploading to:</small>
            <div className="context-path">
              {categories.find(c => c.id === formData.category)?.icon}{' '}
              {categories.find(c => c.id === formData.category)?.name}
              {selectedFolder && (
                <>
                  {' › '}
                  {selectedFolder.icon} {selectedFolder.name}
                </>
              )}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div
            className={`file-drop-zone ${dragActive ? 'active' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="file-selected">
                <div className="file-icon">📎</div>
                <div className="file-info">
                  <p className="file-name">{selectedFile.name}</p>
                  <p className="file-size">
                    {fileService.formatFileSize(selectedFile.size)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="btn-remove"
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="file-prompt">
                <div className="upload-icon">📁</div>
                <p>Drag and drop file here</p>
                <p className="or-text">or</p>
                <label htmlFor="file-input" className="btn-select-file">
                  Choose File
                </label>
                <input
                  id="file-input"
                  type="file"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                  disabled={uploading}
                />
                <p className="file-hint">
                  Max 10MB • PDF, Images, Office documents
                </p>
              </div>
            )}
          </div>

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="title">Document Title *</label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="e.g., Passport Copy"
              required
              disabled={uploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (Optional)</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Add notes about this document..."
              rows={3}
              disabled={uploading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="docType">Document Type</label>
            <input
              type="text"
              id="docType"
              name="docType"
              value={formData.docType}
              onChange={handleChange}
              placeholder="e.g., Passport, Aadhar Card, License"
              disabled={uploading}
            />
          </div>

          {/* ✅ UPDATED: Category selector (can change if needed) */}
          <div className="form-group">
            <label htmlFor="category">Category *</label>
            <select
              id="category"
              name="category"
              value={formData.category}
              onChange={handleChange}
              required
              disabled={uploading}
            >
              <option value="">Select a category</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>
                  {cat.icon} {cat.name}
                </option>
              ))}
            </select>
            {selectedCategory !== 'all' && (
              <small style={{ color: '#666', fontSize: '12px' }}>
                Auto-selected based on current view
              </small>
            )}
          </div>

          <div className="form-group-inline">
            <input
              type="checkbox"
              id="hasExpiry"
              name="hasExpiry"
              checked={formData.hasExpiry}
              onChange={handleChange}
              disabled={uploading}
            />
            <label htmlFor="hasExpiry">
              This document has an expiry date
            </label>
          </div>

          {formData.hasExpiry && (
            <>
              <div className="form-group">
                <label htmlFor="issueDate">Issue Date (Optional)</label>
                <input
                  type="date"
                  id="issueDate"
                  name="issueDate"
                  value={formData.issueDate}
                  onChange={handleChange}
                  max={new Date().toISOString().split('T')[0]}
                  disabled={uploading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="expiryDate">Expiry Date *</label>
                <input
                  type="date"
                  id="expiryDate"
                  name="expiryDate"
                  value={formData.expiryDate}
                  onChange={handleChange}
                  min={new Date().toISOString().split('T')[0]}
                  required
                  disabled={uploading}
                />
              </div>
            </>
          )}

          {uploading && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="progress-text">
                {progress < 100 ? `Uploading... ${progress}%` : 'Upload complete!'}
              </p>
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
              disabled={uploading}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="btn-primary"
              disabled={uploading || !selectedFile}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UploadModal;