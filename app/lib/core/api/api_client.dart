// One Dio instance for the whole app, with two interceptors:
// 1. Attach the access token to every request.
// 2. On a 401, silently call /auth/refresh once and retry the request.
//    The user never sees their 15-minute token expire.
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/token_storage.dart';

// Android emulator reaches your machine's localhost via 10.0.2.2.
// iOS simulator uses localhost directly. Real devices need your LAN IP.
const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

final tokenStorageProvider = Provider((ref) => TokenStorage());

final dioProvider = Provider<Dio>((ref) {
  final storage = ref.read(tokenStorageProvider);
  final dio = Dio(BaseOptions(baseUrl: apiBaseUrl));

  dio.interceptors.add(InterceptorsWrapper(
    onRequest: (options, handler) async {
      final token = await storage.access;
      if (token != null) options.headers['Authorization'] = 'Bearer $token';
      handler.next(options);
    },
    onError: (error, handler) async {
      final isAuthCall = error.requestOptions.path.startsWith('/auth');
      if (error.response?.statusCode == 401 && !isAuthCall) {
        final refresh = await storage.refresh;
        if (refresh != null) {
          try {
            // Plain Dio here so this call skips our interceptors.
            final r = await Dio(BaseOptions(baseUrl: apiBaseUrl))
                .post('/auth/refresh', data: {'refresh_token': refresh});
            await storage.save(
              access: r.data['access_token'],
              refresh: r.data['refresh_token'],
            );
            // Multipart uploads can't be replayed (their FormData is
            // already consumed) -- tokens are refreshed, so the user's next
            // attempt succeeds. Everything else retries automatically.
            if (error.requestOptions.data is FormData) {
              return handler.next(error);
            }
            final retry = await dio.fetch(error.requestOptions
              ..headers['Authorization'] = 'Bearer ${r.data['access_token']}');
            return handler.resolve(retry);
          } catch (_) {
            await storage.clear(); // refresh failed -> proper sign-out
          }
        }
      }
      handler.next(error);
    },
  ));
  return dio;
});
