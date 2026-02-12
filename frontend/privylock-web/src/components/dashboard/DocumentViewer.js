/**
 * DocumentViewer Component - FIXED FOR PDF PREVIEW
 *
 * Provides in-browser preview/viewing of documents.
 *
 * ✅ FIX: Pass MIME type to downloadDocumentBlob() for proper PDF rendering
 *
 * Features:
 * - PDF preview (iframe with correct MIME type)
 * - Image preview (img tag)
 * - Video preview (video tag)
 * - Text file preview (iframe)
 * - Download button for unsupported types
 */

import React, { useState, useEffect } from 'react';
import fileService from '../../services/fileService';
import './DocumentViewer.css';

const DocumentViewer = ({ document, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  useEffect(() => {
    loadPreview();
    return () => {
      // Cleanup: revoke object URL when component unmounts
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [document.id]);

  /**
   * Load and decrypt document for preview.
   *
   * ✅ FIXED: Determine MIME type and pass to downloadDocumentBlob()
   *
   * Flow:
   * 1. Get file extension
   * 2. Determine MIME type (application/pdf, image/jpeg, etc.)
   * 3. Download encrypted file from server
   * 4. Decrypt using master key with correct MIME type
   * 5. Create blob URL for preview
   * 6. Set preview URL state
   */
  const loadPreview = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('📥 Loading preview for:', document.title);

      // ✅ FIXED: Get MIME type from document
      const mimeType = getMimeType();
      console.log('📄 Detected MIME type:', mimeType);

      // Download and decrypt document with correct MIME type
      const blob = await fileService.downloadDocumentBlob(document.id, mimeType);

      console.log('✅ Blob created:', {
        type: blob.type,
        size: blob.size
      });

      // Create object URL for preview
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);

      console.log('✅ Preview loaded');
    } catch (err) {
      console.error('❌ Preview error:', err);
      setError('Failed to load preview. You can still download the file.');
    } finally {
      setLoading(false);
    }
  };

  /**
   * ✅ NEW: Get MIME type from document metadata.
   *
   * Priority:
   * 1. Use document.mime_type if available
   * 2. Otherwise, derive from file_extension
   */
  const getMimeType = () => {
    // If backend provides MIME type, use it
    if (document.mime_type && document.mime_type !== 'application/octet-stream') {
      return document.mime_type;
    }

    // Otherwise, derive from extension
    const ext = document.file_extension?.toLowerCase();
    return fileService.getMimeTypeFromExtension(ext);
  };

  /**
   * Download document to user's device.
   */
  const handleDownload = async () => {
    try {
      await fileService.downloadDocument(
        document.id,
        `${document.title}.${document.file_extension}`
      );
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed. Please try again.');
    }
  };

  /**
   * Render preview based on file type.
   */
  const renderPreview = () => {
    if (loading) {
      return (
        <div className="preview-loading">
          <div className="spinner"></div>
          <p>Loading preview...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="preview-error">
          <p>⚠️ {error}</p>
          <button onClick={handleDownload} className="btn-download">
            📥 Download File
          </button>
        </div>
      );
    }

    const ext = document.file_extension?.toLowerCase();

    // Images
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
      return (
        <div className="preview-image">
          <img
            src={previewUrl}
            alt={document.title}
            style={{ maxWidth: '100%', maxHeight: '80vh' }}
          />
        </div>
      );
    }

    // PDFs - ✅ FIXED: Now works because blob has correct MIME type
    if (ext === 'pdf') {
      return (
        <div className="preview-pdf">
          <iframe
            src={previewUrl}
            title={document.title}
            style={{ width: '100%', height: '80vh', border: 'none' }}
          />
        </div>
      );
    }

    // Videos
    if (['mp4', 'webm', 'ogg'].includes(ext)) {
      return (
        <div className="preview-video">
          <video
            src={previewUrl}
            controls
            style={{ maxWidth: '100%', maxHeight: '80vh' }}
          >
            Your browser does not support video playback.
          </video>
        </div>
      );
    }

    // Text files
    if (['txt', 'md', 'csv'].includes(ext)) {
      return (
        <div className="preview-text">
          <iframe
            src={previewUrl}
            title={document.title}
            style={{ width: '100%', height: '80vh', border: '1px solid #ddd' }}
          />
        </div>
      );
    }

    // Unsupported file type - show download button
    return (
      <div className="preview-unsupported">
        <div className="unsupported-icon">📄</div>
        <h3>Preview not available</h3>
        <p>This file type cannot be previewed in the browser.</p>
        <p className="file-info">
          <strong>File:</strong> {document.title}.{document.file_extension}
          <br />
          <strong>Size:</strong> {formatFileSize(document.file_size)}
        </p>
        <button onClick={handleDownload} className="btn-download">
          📥 Download to View
        </button>
      </div>
    );
  };

  /**
   * Format bytes to human-readable size.
   */
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="document-viewer-overlay" onClick={onClose}>
      <div className="document-viewer" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="viewer-header">
          <div className="viewer-title">
            <h2>{document.title}</h2>
            <p className="viewer-meta">
              {document.file_extension?.toUpperCase()} • {formatFileSize(document.file_size)}
            </p>
          </div>

          <div className="viewer-actions">
            <button
              onClick={handleDownload}
              className="btn-icon"
              title="Download"
            >
              📥
            </button>
            <button
              onClick={onClose}
              className="btn-close"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Preview Area */}
        <div className="viewer-content">
          {renderPreview()}
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;