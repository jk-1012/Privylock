import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/app_config.dart';

class ApiService {
  late final Dio _dio;
  final _secureStorage = const FlutterSecureStorage();

  ApiService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConfig.baseUrl,
        connectTimeout: const Duration(milliseconds: AppConfig.connectTimeout),
        receiveTimeout: const Duration(milliseconds: AppConfig.receiveTimeout),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Add JWT token to requests
          final token = await _secureStorage.read(key: 'access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) async {
          // Handle 401 (unauthorized) - refresh token
          if (error.response?.statusCode == 401) {
            // Try to refresh token
            if (await _refreshToken()) {
              // Retry the request
              return handler.resolve(await _retry(error.requestOptions));
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Future<bool> _refreshToken() async {
    try {
      final refreshToken = await _secureStorage.read(key: 'refresh_token');
      if (refreshToken == null) return false;

      final response = await _dio.post(
        '/auth/token/refresh/',
        data: {'refresh': refreshToken},
      );

      await _secureStorage.write(
        key: 'access_token',
        value: response.data['access'],
      );

      return true;
    } catch (e) {
      return false;
    }
  }

  Future<Response<dynamic>> _retry(RequestOptions requestOptions) async {
    final options = Options(
      method: requestOptions.method,
      headers: requestOptions.headers,
    );
    return _dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: options,
    );
  }

  // Auth endpoints
  Future<Response> register(Map<String, dynamic> data) async {
    return await _dio.post('/auth/register/', data: data);
  }

  Future<Response> login(Map<String, dynamic> data) async {
    return await _dio.post('/auth/login/', data: data);
  }

  // Document endpoints
  Future<Response> uploadDocument(FormData data) async {
    return await _dio.post('/vault/documents/upload/', data: data);
  }

  Future<Response> getDocuments({int page = 1}) async {
    return await _dio.get('/vault/documents/', queryParameters: {'page': page});
  }

  Future<Response> getDocumentDetail(String id) async {
    return await _dio.get('/vault/documents/$id/');
  }

  Future<Response> deleteDocument(String id) async {
    return await _dio.delete('/vault/documents/$id/');
  }

  // Category endpoints
  Future<Response> getCategories() async {
    return await _dio.get('/vault/categories/');
  }
}