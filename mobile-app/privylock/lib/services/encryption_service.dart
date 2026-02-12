import 'dart:convert';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:encrypt/encrypt.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pointycastle/export.dart';

class EncryptionService {
  final _secureStorage = const FlutterSecureStorage();
  static const _masterKeyStorageKey = 'master_encryption_key';
  static const _saltStorageKey = 'encryption_salt';

  /// Derives a master key from user's password using PBKDF2
  Future<Uint8List> deriveMasterKey(String password, Uint8List salt) async {
    final pbkdf2 = PBKDF2KeyDerivator(HMac(SHA256Digest(), 64))
      ..init(Pbkdf2Parameters(salt, 600000, 32)); // 600k iterations, 256-bit key

    return pbkdf2.process(Uint8List.fromList(password.codeUnits));
  }

  /// Generates a random salt
  Uint8List generateSalt() {
    final secureRandom = FortunaRandom();
    final seedSource = Random.secure();
    final seeds = <int>[];
    for (int i = 0; i < 32; i++) {
      seeds.add(seedSource.nextInt(255));
    }
    secureRandom.seed(KeyParameter(Uint8List.fromList(seeds)));

    return secureRandom.nextBytes(32);
  }

  /// Stores master key securely
  Future<void> storeMasterKey(Uint8List key, Uint8List salt) async {
    await _secureStorage.write(
      key: _masterKeyStorageKey,
      value: base64Encode(key),
    );
    await _secureStorage.write(
      key: _saltStorageKey,
      value: base64Encode(salt),
    );
  }

  /// Retrieves master key from secure storage
  Future<Uint8List?> getMasterKey() async {
    final keyString = await _secureStorage.read(key: _masterKeyStorageKey);
    if (keyString == null) return null;
    return base64Decode(keyString);
  }

  /// Encrypts text using AES-256-GCM
  Future<Map<String, String>> encryptText(String plaintext) async {
    final masterKey = await getMasterKey();
    if (masterKey == null) throw Exception('Master key not found');

    final key = Key(masterKey);
    final iv = IV.fromSecureRandom(16); // 128-bit IV for GCM

    final encrypter = Encrypter(AES(key, mode: AESMode.gcm));
    final encrypted = encrypter.encrypt(plaintext, iv: iv);

    return {
      'ciphertext': encrypted.base64,
      'iv': iv.base64,
      'tag': encrypted.base64, // GCM auth tag included
    };
  }

  /// Decrypts text
  Future<String> decryptText(Map<String, String> encryptedData) async {
    final masterKey = await getMasterKey();
    if (masterKey == null) throw Exception('Master key not found');

    final key = Key(masterKey);
    final iv = IV.fromBase64(encryptedData['iv']!);

    final encrypter = Encrypter(AES(key, mode: AESMode.gcm));
    final encrypted = Encrypted.fromBase64(encryptedData['ciphertext']!);

    return encrypter.decrypt(encrypted, iv: iv);
  }

  /// Encrypts file bytes
  Future<Map<String, dynamic>> encryptFile(Uint8List fileBytes) async {
    final masterKey = await getMasterKey();
    if (masterKey == null) throw Exception('Master key not found');

    final key = Key(masterKey);
    final iv = IV.fromSecureRandom(16);

    final encrypter = Encrypter(AES(key, mode: AESMode.cbc));
    final encrypted = encrypter.encryptBytes(fileBytes, iv: iv);

    return {
      'data': encrypted.bytes,
      'iv': iv.base64,
    };
  }

  /// Decrypts file bytes
  Future<Uint8List> decryptFile(Map<String, dynamic> encryptedData) async {
    final masterKey = await getMasterKey();
    if (masterKey == null) throw Exception('Master key not found');

    final key = Key(masterKey);
    final iv = IV.fromBase64(encryptedData['iv']);

    final encrypter = Encrypter(AES(key, mode: AESMode.cbc));
    final encrypted = Encrypted(Uint8List.fromList(encryptedData['data']));

    return Uint8List.fromList(encrypter.decryptBytes(encrypted, iv: iv));
  }

  /// Hashes password for server authentication
  String hashPassword(String password) {
    final bytes = utf8.encode(password);
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Clears all encryption keys (logout)
  Future<void> clearKeys() async {
    await _secureStorage.delete(key: _masterKeyStorageKey);
    await _secureStorage.delete(key: _saltStorageKey);
  }
}