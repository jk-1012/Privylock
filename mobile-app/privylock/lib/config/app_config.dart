class AppConfig {
  // API Configuration
  static const String baseUrl = 'http://10.0.2.2:8000/api';  // Android emulator
  // For iOS simulator: http://localhost:8000/api
  // For real device: http://YOUR_COMPUTER_IP:8000/api

  static const int connectTimeout = 30000; // 30 seconds
  static const int receiveTimeout = 30000;

  // Encryption
  static const int pbkdf2Iterations = 600000;
  static const int aesKeyLength = 256;

  // Storage limits (bytes)
  static const Map<String, int> storageLimits = {
    'FREE': 1 * 1024 * 1024 * 1024,      // 1 GB
    'PREMIUM': 25 * 1024 * 1024 * 1024,  // 25 GB
    'FAMILY': 100 * 1024 * 1024 * 1024,  // 100 GB
    'LIFETIME': 10 * 1024 * 1024 * 1024, // 10 GB
  };

  // Document limits
  static const Map<String, int> documentLimits = {
    'FREE': 20,
    'PREMIUM': 999999,
    'FAMILY': 999999,
    'LIFETIME': 999999,
  };

  // Auto-lock timeout (milliseconds)
  static const int autoLockTimeout = 120000; // 2 minutes

  // Notification settings
  static const List<int> expiryNotificationDays = [60, 30, 7, 0];
}