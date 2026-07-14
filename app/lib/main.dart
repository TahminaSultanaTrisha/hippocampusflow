// App entry point. ProviderScope is Riverpod's root container -- every
// provider (auth state, API client, ...) lives inside it.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';

void main() {
  runApp(const ProviderScope(child: HippocampusFlowApp()));
}
