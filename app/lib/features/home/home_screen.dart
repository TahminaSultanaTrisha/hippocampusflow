// Home: the pulsing scan circle (the app's heartbeat), history, profile.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
      vsync: this, duration: const Duration(seconds: 2))
    ..repeat(reverse: true);

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('HippocampusFlow'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'Scan history',
            onPressed: () => context.go('/history'),
          ),
          IconButton(
            icon: const Icon(Icons.person_outline),
            tooltip: 'Profile',
            onPressed: () => context.go('/profile'),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            GestureDetector(
              onTap: () => context.go('/scan'),
              child: AnimatedBuilder(
                animation: _pulse,
                builder: (context, child) {
                  final t = _pulse.value;
                  return Container(
                    width: 180,
                    height: 180,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: inkRaised,
                      border: Border.all(color: scanGlow, width: 2),
                      boxShadow: [
                        BoxShadow(
                          color: scanGlow.withOpacity(0.15 + 0.25 * t),
                          blurRadius: 24 + 26 * t,
                          spreadRadius: 2 + 6 * t,
                        ),
                      ],
                    ),
                    child: child,
                  );
                },
                child: const Icon(Icons.center_focus_weak,
                    size: 72, color: scanGlow),
              ),
            ),
            const SizedBox(height: 28),
            Text('Scan anything',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Text('Food · receipts · plants · gadgets · anything',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: mistText.withOpacity(0.45))),
          ],
        ),
      ),
    );
  }
}
