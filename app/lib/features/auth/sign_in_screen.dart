import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';

import '../onboarding/welcome_screen.dart';

import '../../app/theme.dart';
import 'auth_controller.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});
  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  final _email = TextEditingController();

  @override
  void initState() {
    super.initState();
    _maybeShowOnboarding();
  }

  Future<void> _maybeShowOnboarding() async {
    final seen =
        await const FlutterSecureStorage().read(key: onboardedKey);
    if (seen == null && mounted) context.go('/welcome');
  }

  final _password = TextEditingController();
  bool _isRegister = false;
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    setState(() { _busy = true; _error = null; });
    try {
      await ref.read(authControllerProvider.notifier).signIn(
            _email.text.trim(),
            _password.text,
            isRegister: _isRegister,
          );
      // Router redirect takes over from here.
    } on DioException catch (e) {
      // Backend errors arrive as {code, message} -- show the message.
      final detail = e.response?.data is Map ? e.response?.data['detail'] : null;
      setState(() => _error =
          detail is Map ? detail['message'] : 'Could not reach the server');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.center_focus_weak, size: 56, color: scanGlow),
                const SizedBox(height: 12),
                Text('HippocampusFlow',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall),
                Text('Point. Understand. Remember.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: mistText.withOpacity(0.6))),
                const SizedBox(height: 32),
                TextField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(hintText: 'Email'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  obscureText: true,
                  decoration:
                      const InputDecoration(hintText: 'Password (8+ characters)'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!,
                      style: const TextStyle(color: Colors.redAccent)),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: Text(_busy
                      ? 'One moment…'
                      : (_isRegister ? 'Create account' : 'Sign in')),
                ),
                TextButton(
                  onPressed: () => setState(() => _isRegister = !_isRegister),
                  child: Text(_isRegister
                      ? 'Have an account? Sign in'
                      : 'New here? Create an account'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
