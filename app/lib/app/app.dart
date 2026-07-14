import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'router.dart';
import 'theme.dart';

class HippocampusFlowApp extends ConsumerWidget {
  const HippocampusFlowApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'HippocampusFlow',
      theme: buildTheme(),
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
