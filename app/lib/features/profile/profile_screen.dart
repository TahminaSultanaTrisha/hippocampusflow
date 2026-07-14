import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';
import '../auth/auth_controller.dart';
import '../scan/scan_repository.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repo = ref.read(scanRepositoryProvider);
    return Scaffold(
      appBar: AppBar(backgroundColor: Colors.transparent, title: const Text('Profile')),
      body: FutureBuilder(
        future: repo.me(),
        builder: (context, snap) {
          final email = snap.data?['email'] ?? '…';
          final tier = snap.data?['subscription_tier'] ?? 'free';
          final used = snap.data?['scans_used_this_month'] ?? 0;
          final limit = snap.data?['scan_limit'];
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                    color: inkRaised, borderRadius: BorderRadius.circular(16)),
                child: Row(children: [
                  const CircleAvatar(
                      backgroundColor: scanGlow,
                      child: Icon(Icons.person, color: inkDeep)),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('$email',
                            style: Theme.of(context).textTheme.titleSmall),
                        Text(
                            limit == null
                                ? '${tier.toString().toUpperCase()} plan · unlimited scans'
                                : '${tier.toString().toUpperCase()} plan · $used of $limit scans used this month',
                            style: Theme.of(context)
                                .textTheme
                                .bodySmall
                                ?.copyWith(color: mistText.withOpacity(0.5))),
                        if (limit != null) ...[
                          const SizedBox(height: 8),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(6),
                            child: LinearProgressIndicator(
                              value: (used as num) / limit,
                              minHeight: 6,
                              color: used >= limit ? Colors.redAccent : scanGlow,
                              backgroundColor: inkDeep,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ]),
              ),
              const SizedBox(height: 12),
              ListTile(
                tileColor: inkRaised,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
                leading: const Icon(Icons.psychology, color: scanGlow),
                title: const Text('Manage memories'),
                subtitle: const Text('See and delete what the AI remembers'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => context.go('/memories'),
              ),
              const SizedBox(height: 12),
              ListTile(
                tileColor: inkRaised,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
                leading: const Icon(Icons.workspace_premium, color: scanGlow),
                title: const Text('Upgrade to Premium'),
                subtitle: const Text('Unlimited scans — coming soon'),
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Premium is coming soon — you\'re early!'))),
              ),
              const SizedBox(height: 12),
              ListTile(
                tileColor: inkRaised,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
                leading: const Icon(Icons.logout, color: Colors.redAccent),
                title: const Text('Sign out'),
                onTap: () =>
                    ref.read(authControllerProvider.notifier).signOut(),
              ),
            ],
          );
        },
      ),
    );
  }
}
