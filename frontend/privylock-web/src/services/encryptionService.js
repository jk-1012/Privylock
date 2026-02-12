/**
 * encryptionService.js - Encryption Service for PrivyLock
 *
 * FEATURES:
 * ✅ Master Key Derivation (PBKDF2-HMAC-SHA256, 600K iterations)
 * ✅ File Encryption/Decryption (AES-256-GCM)
 * ✅ Text Encryption/Decryption (AES-256-GCM)
 * ✅ Password Hashing (SHA-256)
 * ✅ Deterministic Salt (from email hash)
 * ✅ Base64 Encoding/Decoding
 * ✅ Recovery Key Generation
 * ✅ Device ID Generation
 * ✅ Zero-Knowledge Architecture
 */

class EncryptionService {
  constructor() {
    // Web Crypto API
    this.crypto = window.crypto;
    this.subtle = this.crypto.subtle;

    // PBKDF2 Configuration
    this.PBKDF2_ITERATIONS = 600000;  // 600K iterations (slow brute force)
    this.SALT_LENGTH = 16;             // 128 bits
    this.KEY_LENGTH = 32;              // 256 bits

    // AES-GCM Configuration
    this.IV_LENGTH = 12;               // 96 bits
    this.TAG_LENGTH = 128;             // 128 bits
  }

  // ========================================
  // KEY DERIVATION
  // ========================================

  /**
   * Derive master encryption key from password using PBKDF2
   *
   * CRITICAL: Salt must be derived from email hash (deterministic)
   * Same email + password always produces same master key
   *
   * @param {string} password - User's password
   * @param {Uint8Array} salt - Salt bytes (from email hash)
   * @returns {Promise<ArrayBuffer>} 256-bit master key
   */
  async deriveMasterKey(password, salt) {
    try {
      console.log('🔑 Deriving master key...');
      console.log('  → Password length:', password.length);
      console.log('  → Salt length:', salt.byteLength, 'bytes');

      // Convert password string to bytes
      const encoder = new TextEncoder();
      const passwordBytes = encoder.encode(password);

      // Import password as key material
      const keyMaterial = await this.subtle.importKey(
        'raw',
        passwordBytes,
        'PBKDF2',
        false,
        ['deriveKey']
      );

      // Derive 256-bit key using PBKDF2
      const key = await this.subtle.deriveKey(
        {
          name: 'PBKDF2',
          salt: salt,
          iterations: this.PBKDF2_ITERATIONS,
          hash: 'SHA-256'
        },
        keyMaterial,
        {
          name: 'AES-GCM',
          length: 256
        },
        true,  // Extractable (so we can export it)
        ['encrypt', 'decrypt']
      );

      // Export key as ArrayBuffer
      const exportedKey = await this.subtle.exportKey('raw', key);

      console.log('  ✅ Master key derived:', exportedKey.byteLength, 'bytes');

      return exportedKey;

    } catch (error) {
      console.error('❌ Key derivation failed:', error);
      throw new Error('Failed to derive master key: ' + error.message);
    }
  }

  // ========================================
  // HASHING
  // ========================================

  /**
   * Hash password using SHA-256
   *
   * Used for:
   * - Username generation (from email)
   * - Salt generation (from email)
   * - Password hashing before sending to server
   * - Recovery key hashing
   *
   * @param {string} input - String to hash
   * @returns {Promise<string>} Hex string (64 characters)
   */
  async hashPassword(input) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(input);

      const hashBuffer = await this.subtle.digest('SHA-256', data);

      // Convert to hex string
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');

      return hashHex;

    } catch (error) {
      console.error('❌ Hashing failed:', error);
      throw new Error('Failed to hash password: ' + error.message);
    }
  }

  // ========================================
  // TEXT ENCRYPTION/DECRYPTION
  // ========================================

  /**
   * Encrypt text using AES-256-GCM
   *
   * Used for encrypting:
   * - Document titles
   * - Document descriptions
   * - Folder names
   *
   * @param {string} text - Plaintext to encrypt
   * @param {ArrayBuffer} masterKey - 256-bit master key
   * @returns {Promise<string>} Base64-encoded encrypted data
   */
  async encryptText(text, masterKey) {
    try {
      if (!text) return '';

      console.log('🔐 Encrypting text:', text.substring(0, 20) + '...');

      // Convert text to bytes
      const encoder = new TextEncoder();
      const data = encoder.encode(text);

      // Generate random IV (96 bits)
      const iv = this.crypto.getRandomValues(new Uint8Array(this.IV_LENGTH));

      // Import master key
      const key = await this.subtle.importKey(
        'raw',
        masterKey,
        { name: 'AES-GCM' },
        false,
        ['encrypt']
      );

      // Encrypt
      const encryptedData = await this.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: this.TAG_LENGTH
        },
        key,
        data
      );

      // Combine IV + encrypted data
      const combined = new Uint8Array([
        ...iv,
        ...new Uint8Array(encryptedData)
      ]);

      // Convert to Base64
      const base64 = btoa(String.fromCharCode(...combined));

      console.log('  ✅ Text encrypted, length:', base64.length);

      return base64;

    } catch (error) {
      console.error('❌ Text encryption failed:', error);
      throw new Error('Failed to encrypt text: ' + error.message);
    }
  }

  /**
   * Decrypt text using AES-256-GCM
   *
   * @param {string} encryptedBase64 - Base64-encoded encrypted data
   * @param {ArrayBuffer} masterKey - 256-bit master key
   * @returns {Promise<string>} Decrypted plaintext
   */
  async decryptText(encryptedBase64, masterKey) {
    try {
      if (!encryptedBase64) return '';

      // Convert Base64 to bytes
      const combined = Uint8Array.from(atob(encryptedBase64), c => c.charCodeAt(0));

      // Extract IV (first 12 bytes)
      const iv = combined.slice(0, this.IV_LENGTH);

      // Extract encrypted data (rest)
      const encryptedData = combined.slice(this.IV_LENGTH);

      // Import master key
      const key = await this.subtle.importKey(
        'raw',
        masterKey,
        { name: 'AES-GCM' },
        false,
        ['decrypt']
      );

      // Decrypt
      const decryptedData = await this.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: this.TAG_LENGTH
        },
        key,
        encryptedData
      );

      // Convert to string
      const decoder = new TextDecoder();
      return decoder.decode(decryptedData);

    } catch (error) {
      console.error('❌ Text decryption failed:', error);
      throw new Error('Failed to decrypt text');
    }
  }

  /**
   * Decode Base64-encoded text from backend (for notifications)
   *
   * IMPORTANT: Notifications are NOT encrypted - they're stored as plain text bytes.
   * Backend converts to Base64 for transport, frontend decodes back to plain text.
   *
   * @param {string} base64Text - Base64-encoded plain text from backend
   * @param {ArrayBuffer} masterKey - NOT USED (kept for compatibility)
   * @returns {Promise<string>} Plain text string
   */
  async decryptBase64Text(base64Text, masterKey = null) {
    try {
      if (!base64Text) return '';

      console.log('🔓 Decoding Base64 notification text...');

      // Simply decode Base64 to get plain text
      // No actual decryption needed (notifications are not encrypted)
      const plaintext = atob(base64Text);

      console.log('  ✅ Base64 decoded successfully');

      return plaintext;

    } catch (error) {
      console.error('❌ Base64 decoding failed:', error);
      console.error('  → Input length:', base64Text?.length);
      console.error('  → Error details:', error.message);

      // Return fallback message instead of throwing
      return '[Unable to decode notification]';
    }
  }

  // ========================================
  // FILE ENCRYPTION/DECRYPTION
  // ========================================

  /**
   * Encrypt file using AES-256-GCM
   *
   * @param {ArrayBuffer} fileData - File contents as ArrayBuffer
   * @param {ArrayBuffer} masterKey - 256-bit master key
   * @returns {Promise<Uint8Array>} Encrypted file with IV prepended
   */
  async encryptFile(fileData, masterKey) {
    try {
      console.log('🔐 Encrypting file:', fileData.byteLength, 'bytes');

      // Generate random IV (96 bits)
      const iv = this.crypto.getRandomValues(new Uint8Array(this.IV_LENGTH));

      // Import master key
      const key = await this.subtle.importKey(
        'raw',
        masterKey,
        { name: 'AES-GCM' },
        false,
        ['encrypt']
      );

      // Encrypt file data
      const encryptedData = await this.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: this.TAG_LENGTH
        },
        key,
        fileData
      );

      // Combine IV + encrypted data
      const combined = new Uint8Array([
        ...iv,
        ...new Uint8Array(encryptedData)
      ]);

      console.log('  ✅ File encrypted:', combined.byteLength, 'bytes');

      return combined;

    } catch (error) {
      console.error('❌ File encryption failed:', error);
      throw new Error('Failed to encrypt file: ' + error.message);
    }
  }

  /**
   * Decrypt file using AES-256-GCM
   *
   * @param {ArrayBuffer} encryptedData - Encrypted file with IV prepended
   * @param {ArrayBuffer} masterKey - 256-bit master key
   * @returns {Promise<ArrayBuffer>} Decrypted file data
   */
  async decryptFile(encryptedData, masterKey) {
    try {
      const encryptedArray = new Uint8Array(encryptedData);

      console.log('🔓 Decrypting file:', encryptedArray.byteLength, 'bytes');

      // Extract IV (first 12 bytes)
      const iv = encryptedArray.slice(0, this.IV_LENGTH);

      // Extract encrypted data (rest)
      const ciphertext = encryptedArray.slice(this.IV_LENGTH);

      // Import master key
      const key = await this.subtle.importKey(
        'raw',
        masterKey,
        { name: 'AES-GCM' },
        false,
        ['decrypt']
      );

      // Decrypt
      const decryptedData = await this.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: this.TAG_LENGTH
        },
        key,
        ciphertext
      );

      console.log('  ✅ File decrypted:', decryptedData.byteLength, 'bytes');

      return decryptedData;

    } catch (error) {
      console.error('❌ File decryption failed:', error);
      throw new Error('Failed to decrypt file');
    }
  }

  // ========================================
  // KEY STORAGE
  // ========================================

  /**
   * Store master key in sessionStorage (Base64 encoded)
   *
   * CRITICAL FIX: Convert ArrayBuffer to Base64 before storing
   * SessionStorage can only store strings
   *
   * @param {ArrayBuffer} masterKey - Master encryption key
   */
  storeMasterKey(masterKey) {
    try {
      // Convert ArrayBuffer to Base64
      const base64 = this.arrayBufferToBase64(masterKey);

      // Store in sessionStorage
      sessionStorage.setItem('masterKey', base64);

      console.log('✅ Master key stored in session');

    } catch (error) {
      console.error('❌ Failed to store master key:', error);
      throw new Error('Failed to store master key: ' + error.message);
    }
  }

  /**
   * Get master key from sessionStorage
   *
   * CRITICAL FIX: Convert Base64 back to ArrayBuffer
   *
   * @returns {ArrayBuffer|null} Master key or null if not found
   */
  getMasterKey() {
    try {
      const base64 = sessionStorage.getItem('masterKey');

      if (!base64) {
        console.warn('⚠️ No master key found in session');
        return null;
      }

      // Convert Base64 to ArrayBuffer
      const masterKey = this.base64ToArrayBuffer(base64);

      console.log('✅ Master key retrieved:', masterKey.byteLength, 'bytes');

      return masterKey;

    } catch (error) {
      console.error('❌ Failed to retrieve master key:', error);
      return null;
    }
  }

  /**
   * Get salt from sessionStorage
   *
   * @returns {Uint8Array|null} Salt or null if not found
   */
  getSalt() {
    try {
      const saltBase64 = sessionStorage.getItem('salt');

      if (!saltBase64) {
        return null;
      }

      const saltBuffer = this.base64ToArrayBuffer(saltBase64);
      return new Uint8Array(saltBuffer);

    } catch (error) {
      console.error('❌ Failed to retrieve salt:', error);
      return null;
    }
  }

  /**
   * Clear all encryption keys from storage
   */
  clearKeys() {
    sessionStorage.removeItem('masterKey');
    sessionStorage.removeItem('salt');
    console.log('✅ Encryption keys cleared from session');
  }

  // ========================================
  // ENCODING/DECODING UTILITIES
  // ========================================

  /**
   * Convert ArrayBuffer to Base64 string
   *
   * @param {ArrayBuffer} buffer - ArrayBuffer to convert
   * @returns {string} Base64 string
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Convert Base64 string to ArrayBuffer
   *
   * @param {string} base64 - Base64 string
   * @returns {ArrayBuffer} ArrayBuffer
   */
  base64ToArrayBuffer(base64) {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  /**
   * Convert hex string to Uint8Array
   *
   * Used to convert salt hex string to bytes for PBKDF2
   *
   * @param {string} hexString - Hex string (e.g., "a1b2c3d4")
   * @returns {Uint8Array} Byte array
   */
  hexToUint8Array(hexString) {
    // Remove any non-hex characters
    hexString = hexString.replace(/[^0-9a-f]/gi, '');

    // Ensure even length (hex pairs)
    if (hexString.length % 2 !== 0) {
      hexString = '0' + hexString;
    }

    // Convert hex pairs to bytes
    const bytes = new Uint8Array(hexString.length / 2);
    for (let i = 0; i < hexString.length; i += 2) {
      bytes[i / 2] = parseInt(hexString.substring(i, i + 2), 16);
    }

    return bytes;
  }

  /**
   * Convert Uint8Array to hex string
   *
   * @param {Uint8Array} bytes - Byte array
   * @returns {string} Hex string
   */
  uint8ArrayToHex(bytes) {
    return Array.from(bytes)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  // ========================================
  // UTILITY FUNCTIONS
  // ========================================

  /**
   * Generate 12-word recovery key
   *
   * Format: word1-word2-word3-...-word12
   * Each word: 6 random alphanumeric characters
   *
   * @returns {string} Recovery key (e.g., "abc123-def456-...")
   */
  generateRecoveryKey() {
    const words = [];
    const charset = 'abcdefghijklmnopqrstuvwxyz0123456789';

    for (let i = 0; i < 12; i++) {
      let word = '';
      for (let j = 0; j < 6; j++) {
        const randomIndex = Math.floor(Math.random() * charset.length);
        word += charset[randomIndex];
      }
      words.push(word);
    }

    return words.join('-');
  }

  /**
   * Generate unique device ID
   *
   * Format: device-{timestamp}-{random}
   *
   * @returns {string} Device ID
   */
  generateDeviceId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    return `device-${timestamp}-${random}`;
  }

  /**
   * Get user-friendly device name from browser
   *
   * Format: "{Browser} on {OS}"
   * Example: "Chrome on Windows"
   *
   * @returns {string} Device name
   */
  getDeviceName() {
    const ua = navigator.userAgent;
    let browserName = 'Browser';
    let osName = 'Unknown OS';

    // Detect browser
    if (ua.includes('Chrome') && !ua.includes('Edge')) {
      browserName = 'Chrome';
    } else if (ua.includes('Firefox')) {
      browserName = 'Firefox';
    } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
      browserName = 'Safari';
    } else if (ua.includes('Edge')) {
      browserName = 'Edge';
    } else if (ua.includes('Opera') || ua.includes('OPR')) {
      browserName = 'Opera';
    }

    // Detect OS
    if (ua.includes('Windows')) {
      osName = 'Windows';
    } else if (ua.includes('Mac')) {
      osName = 'macOS';
    } else if (ua.includes('Linux')) {
      osName = 'Linux';
    } else if (ua.includes('Android')) {
      osName = 'Android';
    } else if (ua.includes('iOS') || ua.includes('iPhone') || ua.includes('iPad')) {
      osName = 'iOS';
    }

    return `${browserName} on ${osName}`;
  }

  /**
   * Generate random salt (for testing/debugging)
   *
   * NOTE: In production, salt is derived from email hash (deterministic)
   *
   * @returns {Uint8Array} Random salt (16 bytes)
   */
  generateSalt() {
    return this.crypto.getRandomValues(new Uint8Array(this.SALT_LENGTH));
  }

  /**
   * Validate password strength
   *
   * @param {string} password - Password to validate
   * @returns {Object} Validation result
   */
  validatePassword(password) {
    const result = {
      valid: true,
      errors: [],
      strength: 0,
    };

    // Minimum length
    if (password.length < 12) {
      result.valid = false;
      result.errors.push('Password must be at least 12 characters long');
    } else {
      result.strength += 25;
    }

    // Uppercase
    if (!/[A-Z]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one uppercase letter');
    } else {
      result.strength += 25;
    }

    // Lowercase
    if (!/[a-z]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one lowercase letter');
    } else {
      result.strength += 25;
    }

    // Number
    if (!/[0-9]/.test(password)) {
      result.valid = false;
      result.errors.push('Password must contain at least one number');
    } else {
      result.strength += 25;
    }

    // Special character (optional but recommended)
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      result.strength += 10;
    }

    // Length bonus
    if (password.length >= 16) {
      result.strength += 10;
    }

    // Cap at 100
    result.strength = Math.min(result.strength, 100);

    return result;
  }
}

// Export singleton instance
export default new EncryptionService();