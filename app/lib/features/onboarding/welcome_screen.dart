// First-run onboarding: three slides that teach the core loop in ten
// seconds. Shown once; a flag in secure storage prevents repeats.
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';

const onboardedKey = 'onboarded_v1';

class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});
  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen> {
  final _pages = const [
    (Icons.center_focus_weak, 'Point at anything',
        'Scan objects, food, receipts, plants, gadgets — your camera becomes a question.'),
    (Icons.auto_awesome, 'AI that understands',
        'Specialist AI agents identify what you scanned, explain it, and suggest useful actions.'),
    (Icons.psychology, 'It remembers for you',
        'Every scan becomes a memory. Ask later: "what was that mug?" — and control what it keeps.'),
  ];
  final _controller = PageController();
  int _page = 0;

  Future<void> _finish() async {
    await const FlutterSecureStorage().write(key: onboardedKey, value: 'yes');
    if (mounted) context.go('/sign-in');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (context, i) {
                  final (icon, title, body) = _pages[i];
                  return Padding(
                    padding: const EdgeInsets.all(36),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(icon, size: 84, color: scanGlow),
                        const SizedBox(height: 28),
                        Text(title,
                            style: Theme.of(context).textTheme.headlineSmall,
                            textAlign: TextAlign.center),
                        const SizedBox(height: 14),
                        Text(body,
                            textAlign: TextAlign.center,
                            style: Theme.of(context)
                                .textTheme
                                .bodyLarge
                                ?.copyWith(color: mistText.withOpacity(0.7))),
                      ],
                    ),
                  );
                },
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _pages.length,
                (i) => Container(
                  width: 8, height: 8,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: i == _page ? scanGlow : inkRaised,
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _page == _pages.length - 1
                      ? _finish
                      : () => _controller.nextPage(
                          duration: const Duration(milliseconds: 250),
                          curve: Curves.easeOut),
                  child: Text(_page == _pages.length - 1
                      ? 'Get started'
                      : 'Next'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
