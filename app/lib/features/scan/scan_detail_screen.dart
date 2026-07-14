// The Phase 2 result screen. Lifecycle:
//   open -> show image + "Analyzing..." shimmer
//   poll GET /scans/{id} every 1.5s until status is complete/failed
//   complete -> AI result card (category, confidence, summary, details,
//               suggested-action chips) + follow-up chat underneath
// Tapping a suggested action drops it into the chat box -- actions and
// chat share one brain.
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';
import 'scan_repository.dart';

class ScanDetailScreen extends ConsumerStatefulWidget {
  const ScanDetailScreen({super.key, required this.scanId});
  final String scanId;

  @override
  ConsumerState<ScanDetailScreen> createState() => _ScanDetailScreenState();
}

class _ScanDetailScreenState extends ConsumerState<ScanDetailScreen> {
  ScanDetail? _scan;
  Timer? _poll;
  final _chatBox = TextEditingController();
  final List<ChatMessage> _messages = [];
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _refresh();
    _poll = Timer.periodic(const Duration(milliseconds: 1500), (_) {
      final s = _scan?.status;
      if (s == 'complete' || s == 'failed') {
        _poll?.cancel();
      } else {
        _refresh();
      }
    });
    _loadMessages();
  }

  Future<void> _refresh() async {
    try {
      final scan = await ref.read(scanRepositoryProvider).scan(widget.scanId);
      if (mounted) setState(() => _scan = scan);
    } catch (_) {/* transient network issues: just try again next tick */}
  }

  Future<void> _loadMessages() async {
    final msgs =
        await ref.read(scanRepositoryProvider).messages(widget.scanId);
    if (mounted) setState(() => _messages
      ..clear()
      ..addAll(msgs));
  }

  Future<void> _send([String? preset]) async {
    final text = (preset ?? _chatBox.text).trim();
    if (text.isEmpty || _sending) return;
    setState(() {
      _sending = true;
      _messages.add(ChatMessage(role: 'user', content: text));
      _chatBox.clear();
    });
    try {
      final reply = await ref
          .read(scanRepositoryProvider)
          .sendMessage(widget.scanId, text);
      if (mounted) setState(() => _messages.add(reply));
    } catch (_) {
      if (mounted) {
        setState(() => _messages.add(ChatMessage(
            role: 'assistant',
            content: 'Sorry — I could not reply. Is the backend running?')));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _poll?.cancel();
    _chatBox.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final repo = ref.read(scanRepositoryProvider);
    final scan = _scan;
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: const Text('Scan result'),
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline),
            tooltip: 'Delete scan',
            onPressed: _deleteScan,
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: FutureBuilder(
              future: repo.image(widget.scanId),
              builder: (context, snap) => snap.hasData
                  ? Image.memory(snap.data!, fit: BoxFit.cover)
                  : const AspectRatio(
                      aspectRatio: 4 / 3,
                      child: Center(
                          child: CircularProgressIndicator(color: scanGlow)),
                    ),
            ),
          ),
          const SizedBox(height: 16),
          if (scan == null || scan.status == 'uploaded' || scan.status == 'analyzing')
            _card(Row(children: [
              const SizedBox(
                  width: 18,
                  height: 18,
                  child:
                      CircularProgressIndicator(color: scanGlow, strokeWidth: 2)),
              const SizedBox(width: 12),
              Text(scan?.status == 'analyzing'
                  ? 'AI is analyzing your scan…'
                  : 'Uploading…'),
            ]))
          else if (scan.status == 'failed')
            _card(Text('Analysis failed. ${scan.summary ?? ''}',
                style: const TextStyle(color: Colors.redAccent)))
          else ...[
            _resultCard(scan),
            const SizedBox(height: 16),
            _chatSection(),
          ],
        ],
      ),
    );
  }


  // Phase 4: real actions per category. Tapping stores data on the server
  // and shows the confirmation (with running totals) in a snackbar.
  static const _primaryActions = {
    'receipt': ('add_expense', 'Add expense', Icons.receipt_long),
    'product': ('save_wishlist', 'Save to wishlist', Icons.favorite_border),
    'electronics': ('save_wishlist', 'Save to wishlist', Icons.favorite_border),
    'food': ('log_meal', 'Log meal', Icons.restaurant),
  };

  Future<void> _runAction(String actionType) async {
    try {
      final message = await ref
          .read(scanRepositoryProvider)
          .runAction(widget.scanId, actionType);
      if (!mounted) return;
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(message)));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Action failed — is the backend running?')));
    }
  }

  Widget? _primaryActionButton(ScanDetail scan) {
    final action = _primaryActions[scan.category];
    if (action == null) return null;
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: FilledButton.icon(
        onPressed: () => _runAction(action.$1),
        icon: Icon(action.$3),
        label: Text(action.$2),
      ),
    );
  }

  Widget _receiptItems(List items) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Column(
        children: [
          for (final item in items.take(20))
            if (item is Map)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  children: [
                    Expanded(
                        child: Text('${item['name'] ?? ''}',
                            style: const TextStyle(fontSize: 13))),
                    Text('${item['price'] ?? ''}',
                        style: const TextStyle(
                            fontSize: 13, fontWeight: FontWeight.w600)),
                  ],
                ),
              ),
        ],
      ),
    );
  }


  Future<void> _deleteScan() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete this scan?'),
        content: const Text(
            'This permanently deletes the photo, the AI analysis, the chat, '
            'and any memories from this scan. This cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Delete',
                  style: TextStyle(color: Colors.redAccent))),
        ],
      ),
    );
    if (confirmed != true) return;
    await ref.read(scanRepositoryProvider).deleteScan(widget.scanId);
    if (mounted) context.go('/history');
  }

  Widget _card(Widget child) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
            color: inkRaised, borderRadius: BorderRadius.circular(16)),
        child: child,
      );

  Widget _resultCard(ScanDetail scan) {
    return _card(Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
                color: scanGlow.withOpacity(0.15),
                borderRadius: BorderRadius.circular(999)),
            child: Text(
              (scan.category ?? 'unknown').toUpperCase(),
              style: const TextStyle(
                  color: scanGlow, fontSize: 12, fontWeight: FontWeight.w700),
            ),
          ),
          const SizedBox(width: 8),
          if (scan.confidence != null)
            Text('${(scan.confidence! * 100).round()}% sure',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: mistText.withOpacity(0.5))),
        ]),
        const SizedBox(height: 12),
        Text(scan.summary ?? '',
            style: Theme.of(context).textTheme.bodyLarge),
        if (scan.details['items'] is List)
          _receiptItems(scan.details['items'] as List),
        if (scan.details.isNotEmpty) ...[
          const SizedBox(height: 12),
          ...scan.details.entries
              .where((e) => e.key != 'items')
              .map((e) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                        width: 110,
                        child: Text(e.key,
                            style: TextStyle(
                                color: mistText.withOpacity(0.55),
                                fontSize: 13))),
                    Expanded(
                        child: Text('${e.value}',
                            style: const TextStyle(fontSize: 13))),
                  ],
                ),
              )),
        ],
        if (scan.suggestedActions.isNotEmpty) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: scan.suggestedActions
                .map((a) => ActionChip(
                      label: Text(a, style: const TextStyle(fontSize: 12)),
                      backgroundColor: inkDeep,
                      side: const BorderSide(color: scanGlow, width: 1),
                      onPressed: () => _send(a),
                    ))
                .toList(),
          ),
        ],
        if (_primaryActionButton(scan) != null) _primaryActionButton(scan)!,
      ],
    ));
  }

  Widget _chatSection() {
    return _card(Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Ask about this scan',
            style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 12),
        ..._messages.map((m) => Align(
              alignment: m.role == 'user'
                  ? Alignment.centerRight
                  : Alignment.centerLeft,
              child: Container(
                margin: const EdgeInsets.only(bottom: 8),
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                constraints: const BoxConstraints(maxWidth: 420),
                decoration: BoxDecoration(
                  color: m.role == 'user'
                      ? scanGlow.withOpacity(0.15)
                      : inkDeep,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(m.content),
              ),
            )),
        if (_sending)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text('Thinking…',
                style: TextStyle(color: mistText.withOpacity(0.5))),
          ),
        Row(children: [
          Expanded(
            child: TextField(
              controller: _chatBox,
              decoration:
                  const InputDecoration(hintText: 'e.g. How much is this worth?'),
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            onPressed: _sending ? null : _send,
            icon: const Icon(Icons.send, color: scanGlow),
          ),
        ]),
      ],
    ));
  }
}
