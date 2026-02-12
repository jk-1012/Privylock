/**
 * File Service - FIXED TO READ FILE AS ARRAYBUFFER
 *
 * ✅ FIXED: Reads File as ArrayBuffer before encrypting
 * ✅ FIXED: Properly includes folder in FormData
 */

import apiService from './apiService';
import encryptionService from './encryptionService';

class FileService {
  /**
   * Validate file size
   */
  validateFileSize(file, maxSize = 10 * 1024 * 1024) {
    return file.size <= maxSize;
  }

  /**
   * Validate file type
   */
  validateFileType(file) {
    const allowedTypes = [
      // Documents
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',

      // Images
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/bmp',

      // Archives
      'application/zip',
      'application/x-zip-compressed',
      'application/x-rar-compressed',
    ];

    return allowedTypes.includes(file.type) || file.type.startsWith('image/');
  }

  /**
   * Format file size
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * ✅ CRITICAL FIX: Read File as ArrayBuffer
   */
  readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      reader.onload = (e) => {
        console.log('  ✅ File read as ArrayBuffer:', e.target.result.byteLength, 'bytes');
        resolve(e.target.result);
      };

      reader.onerror = () => {
        console.error('  ❌ Failed to read file');
        reject(new Error('Failed to read file'));
      };

      reader.readAsArrayBuffer(file);
    });
  }

  /**
   * Upload document with encryption
   *
   * ✅ FIXED: Reads file as ArrayBuffer BEFORE encrypting
   */
  async uploadDocument(file, metadata) {
    try {
      console.log('📤 Starting upload process...');
      console.log('📋 Metadata received:', metadata);
      console.log('📂 Category:', metadata.category);
      console.log('📁 Folder:', metadata.folder);

      // Get master key
      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found. Please login again.');
      }

      console.log('🔑 Master key retrieved');

      // ✅ CRITICAL FIX: Read file as ArrayBuffer FIRST
      console.log('📖 Reading file as ArrayBuffer...');
      const fileData = await this.readFileAsArrayBuffer(file);

      // ✅ NOW encrypt (fileData is ArrayBuffer!)
      console.log('🔐 Encrypting file...');
      const encryptedFile = await encryptionService.encryptFile(fileData, masterKey);
      console.log('✅ File encrypted:', encryptedFile.byteLength, 'bytes');

      // Encrypt metadata
      console.log('🔐 Encrypting metadata...');
      const encryptedTitle = await encryptionService.encryptText(
        metadata.title,
        masterKey
      );

      const encryptedDescription = metadata.description
        ? await encryptionService.encryptText(metadata.description, masterKey)
        : '';

      const encryptedDocType = metadata.docType
        ? await encryptionService.encryptText(metadata.docType, masterKey)
        : '';

      const encryptedIssueDate = metadata.issueDate
        ? await encryptionService.encryptText(metadata.issueDate, masterKey)
        : '';

      const encryptedExpiryDate = metadata.expiryDate
        ? await encryptionService.encryptText(metadata.expiryDate, masterKey)
        : '';

      console.log('✅ Metadata encrypted');

      // Create FormData
      const formData = new FormData();

      // Add encrypted file
      const encryptedBlob = new Blob([encryptedFile], {
        type: 'application/octet-stream'
      });
      formData.append('encrypted_file', encryptedBlob, file.name);

      // Add encrypted metadata
      formData.append('encrypted_title', encryptedTitle);
      formData.append('encrypted_description', encryptedDescription);
      formData.append('encrypted_doc_type', encryptedDocType);
      formData.append('encrypted_issue_date', encryptedIssueDate);
      formData.append('encrypted_expiry_date', encryptedExpiryDate);

      // Add category
      formData.append('category', metadata.category);

      // ✅ CRITICAL: Add folder ID if provided
      if (metadata.folder) {
        formData.append('folder', metadata.folder);
        console.log('✅ Folder ID added to FormData:', metadata.folder);
      } else {
        console.log('ℹ️ No folder - uploading to root');
      }

      // Add other metadata
      formData.append('has_expiry', metadata.hasExpiry ? 'true' : 'false');

      // Log FormData contents for debugging
      console.log('📦 FormData contents:');
      for (let [key, value] of formData.entries()) {
        if (key === 'encrypted_file') {
          console.log(`  ${key}: [Blob ${value.size} bytes]`);
        } else if (key === 'folder') {
          console.log(`  ${key}: ${value} ✅ FOLDER ID`);
        } else {
          console.log(`  ${key}: ${value}`);
        }
      }

      // Upload to server
      console.log('📤 Uploading to server...');
      const response = await apiService.uploadDocument(formData);

      console.log('✅ Upload successful!');
      console.log('📄 Response:', response.data);

      return response.data;

    } catch (error) {
      console.error('❌ Upload failed:', error);
      console.error('Error details:', error.response?.data);
      throw new Error(error.response?.data?.error || error.message || 'Upload failed');
    }
  }

  /**
   * Download and decrypt document
   */
  async downloadDocument(documentId, fileName) {
    try {
      console.log('📥 Downloading document:', documentId);

      // Get master key
      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found. Please login again.');
      }

      // Download encrypted file
      const response = await apiService.downloadDocument(documentId);
      const encryptedBlob = response.data;

      console.log('📥 Encrypted file downloaded');

      // Read as ArrayBuffer
      const encryptedData = await this.readBlobAsArrayBuffer(encryptedBlob);

      // Decrypt
      console.log('🔓 Decrypting file...');
      const decryptedData = await encryptionService.decryptFile(
        encryptedData,
        masterKey
      );

      console.log('✅ File decrypted');

      // Create blob and download
      const blob = new Blob([decryptedData]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      link.click();

      window.URL.revokeObjectURL(url);

      console.log('✅ Download complete!');

    } catch (error) {
      console.error('❌ Download failed:', error);
      throw error;
    }
  }

  /**
   * Download document as blob (for viewing)
   */
  async downloadDocumentBlob(documentId, mimeType = 'application/octet-stream') {
    try {
      // Get master key
      const masterKey = encryptionService.getMasterKey();
      if (!masterKey) {
        throw new Error('No master key found');
      }

      // Download encrypted file
      const response = await apiService.downloadDocument(documentId);
      const encryptedBlob = response.data;

      // Read as ArrayBuffer
      const encryptedData = await this.readBlobAsArrayBuffer(encryptedBlob);

      // Decrypt
      const decryptedData = await encryptionService.decryptFile(
        encryptedData,
        masterKey
      );

      // Return as blob with proper MIME type
      return new Blob([decryptedData], { type: mimeType });

    } catch (error) {
      console.error('Failed to get document blob:', error);
      throw error;
    }
  }

  /**
   * Get MIME type from file extension
   */
  getMimeTypeFromExtension(extension) {
    const mimeTypes = {
      'pdf': 'application/pdf',
      'jpg': 'image/jpeg',
      'jpeg': 'image/jpeg',
      'png': 'image/png',
      'gif': 'image/gif',
      'webp': 'image/webp',
      'bmp': 'image/bmp',
      'txt': 'text/plain',
      'doc': 'application/msword',
      'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'xls': 'application/vnd.ms-excel',
      'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'ppt': 'application/vnd.ms-powerpoint',
      'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'mp4': 'video/mp4',
      'mp3': 'audio/mpeg',
    };

    return mimeTypes[extension?.toLowerCase()] || 'application/octet-stream';
  }

  /**
   * Read blob as ArrayBuffer
   */
  readBlobAsArrayBuffer(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsArrayBuffer(blob);
    });
  }
}

export default new FileService();