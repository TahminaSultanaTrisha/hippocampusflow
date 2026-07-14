// The repository is the ONLY place that knows the auth API's URLs and JSON
// shapes. Screens never touch Dio directly -- when the API changes, you
// edit one file.
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';
import '../../core/auth/token_storage.dart';

class AuthRepository {
  AuthRepository(this._dio, this._storage);
  final Dio _dio;
  final TokenStorage _storage;

  Future<void> register(String email, String password) async {
    final r = await _dio.post('/auth/register',
        data: {'email': email, 'password': password});
    await _storage.save(
        access: r.data['access_token'], refresh: r.data['refresh_token']);
  }

  Future<void> login(String email, String password) async {
    final r = await _dio.post('/auth/login',
        data: {'email': email, 'password': password});
    await _storage.save(
        access: r.data['access_token'], refresh: r.data['refresh_token']);
  }


  /// Called on app start: exchanges the stored refresh token for a fresh
  /// token pair. Returns false when there is no session or it has expired,
  /// in which case the user must sign in again.
  Future<bool> refreshSession() async {
    final refresh = await _storage.refresh;
    if (refresh == null) return false;
    try {
      final r = await _dio.post('/auth/refresh',
          data: {'refresh_token': refresh});
      await _storage.save(
          access: r.data['access_token'], refresh: r.data['refresh_token']);
      return true;
    } catch (_) {
      await _storage.clear();
      return false;
    }
  }

  Future<bool> hasSession() async => await _storage.access != null;

  Future<void> signOut() => _storage.clear();
}

final authRepositoryProvider = Provider((ref) =>
    AuthRepository(ref.read(dioProvider), ref.read(tokenStorageProvider)));
