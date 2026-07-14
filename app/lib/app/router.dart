import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/auth_controller.dart';
import '../features/auth/sign_in_screen.dart';
import '../features/onboarding/welcome_screen.dart';
import '../features/profile/memories_screen.dart';
import '../features/profile/profile_screen.dart';
import '../features/history/history_screen.dart';
import '../features/home/home_screen.dart';
import '../features/scan/scan_detail_screen.dart';
import '../features/scan/scan_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      if (auth == AuthStatus.unknown) return null;
      final signedIn = auth == AuthStatus.signedIn;
      final onSignIn = state.matchedLocation == '/sign-in';
      final onWelcome = state.matchedLocation == '/welcome';
      if (!signedIn && !onSignIn && !onWelcome) return '/sign-in';
      if (signedIn && onSignIn) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
      GoRoute(path: '/sign-in', builder: (_, __) => const SignInScreen()),
      GoRoute(path: '/welcome', builder: (_, __) => const WelcomeScreen()),
      GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
      GoRoute(path: '/memories', builder: (_, __) => const MemoriesScreen()),
      GoRoute(path: '/scan', builder: (_, __) => const ScanScreen()),
      GoRoute(path: '/history', builder: (_, __) => const HistoryScreen()),
      GoRoute(
        path: '/scans/:id',
        builder: (_, state) =>
            ScanDetailScreen(scanId: state.pathParameters['id']!),
      ),
    ],
  );
});
