// Auth state machine for the whole app. The router watches this to decide
// whether to show the sign-in screen or the home screen.
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'auth_repository.dart';

enum AuthStatus { unknown, signedOut, signedIn }

class AuthController extends Notifier<AuthStatus> {
  @override
  AuthStatus build() {
    _restore();
    return AuthStatus.unknown; // splash state while we check secure storage
  }

  Future<void> _restore() async {
    // Don't trust a stored access token (it may be hours old and expired):
    // exchange the refresh token for a fresh pair on every app start.
    final ok = await ref.read(authRepositoryProvider).refreshSession();
    state = ok ? AuthStatus.signedIn : AuthStatus.signedOut;
  }

  Future<void> signIn(String email, String password,
      {required bool isRegister}) async {
    final repo = ref.read(authRepositoryProvider);
    isRegister
        ? await repo.register(email, password)
        : await repo.login(email, password);
    state = AuthStatus.signedIn;
  }

  Future<void> signOut() async {
    await ref.read(authRepositoryProvider).signOut();
    state = AuthStatus.signedOut;
  }
}

final authControllerProvider =
    NotifierProvider<AuthController, AuthStatus>(AuthController.new);
