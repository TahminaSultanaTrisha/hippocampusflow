// Scan history with memory search AND multi-select delete:
// tap the checklist icon (or long-press any scan) to enter select mode,
// tick scans, delete them all in one confirmed action.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/theme.dart';
import '../scan/scan_repository.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});
  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  final _searchBox = TextEditingController();
  List<ScanSummary>? _scans;
  MemoryAnswer? _memoryResult;
  bool _asking = false;
  bool _selectMode = false;
  final Set<String> _selected = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final scans = await ref.read(scanRepositoryProvider).history();
    if (mounted) setState(() => _scans = scans);
  }

  Future<void> _ask() async {
    final q = _searchBox.text.trim();
    if (q.isEmpty) return;
    setState(() { _asking = true; _memoryResult = null; _exitSelect(); });
    try {
      final result = await ref.read(scanRepositoryProvider).askMemory(q);
      if (mounted) setState(() => _memoryResult = result);
    } catch (_) {
      if (mounted) {
        setState(() => _memoryResult = MemoryAnswer(
            answer: 'Could not search memory — is the backend running?',
            scans: []));
      }
    } finally {
      if (mounted) setState(() => _asking = false);
    }
  }

  void _clearSearch() {
    _searchBox.clear();
    setState(() => _memoryResult = null);
  }

  void _exitSelect() {
    _selectMode = false;
    _selected.clear();
  }

  Future<void> _deleteSelected() async {
    final count = _selected.length;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete $count scan${count == 1 ? '' : 's'}?'),
        content: const Text(
            'This permanently deletes the photos, AI analyses, chats, and '
            'memories from these scans. This cannot be undone.'),
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
    final deleted = await ref
        .read(scanRepositoryProvider)
        .batchDelete(_selected.toList());
    if (!mounted) return;
    setState(_exitSelect);
    await _load();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$deleted scan${deleted == 1 ? '' : 's'} deleted.')));
    }
  }

  @override
  void dispose() {
    _searchBox.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final showing = _memoryResult?.scans ?? _scans;
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        title: Text(_selectMode ? '${_selected.length} selected' : 'History'),
        actions: [
          if (_selectMode) ...[
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
              tooltip: 'Delete selected',
              onPressed: _selected.isEmpty ? null : _deleteSelected,
            ),
            IconButton(
              icon: const Icon(Icons.close),
              tooltip: 'Cancel',
              onPressed: () => setState(_exitSelect),
            ),
          ] else if (_memoryResult == null)
            IconButton(
              icon: const Icon(Icons.checklist),
              tooltip: 'Select scans',
              onPressed: (_scans?.isEmpty ?? true)
                  ? null
                  : () => setState(() => _selectMode = true),
            ),
        ],
      ),
      body: Column(
        children: [
          if (!_selectMode)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: TextField(
                controller: _searchBox,
                decoration: InputDecoration(
                  hintText: 'Ask your memory… e.g. "what was that mug?"',
                  prefixIcon: const Icon(Icons.psychology, color: scanGlow),
                  suffixIcon: _memoryResult != null ||
                          _searchBox.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: _clearSearch)
                      : null,
                ),
                onSubmitted: (_) => _ask(),
              ),
            ),
          if (_asking)
            const Padding(
              padding: EdgeInsets.all(12),
              child: LinearProgressIndicator(color: scanGlow),
            ),
          if (_memoryResult != null && _memoryResult!.answer.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: scanGlow.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: scanGlow.withOpacity(0.4)),
                ),
                child: Text(_memoryResult!.answer),
              ),
            ),
          Expanded(
            child: showing == null
                ? const Center(
                    child: CircularProgressIndicator(color: scanGlow))
                : showing.isEmpty
                    ? Center(
                        child: Text(_memoryResult != null
                            ? 'No matching scans.'
                            : 'No scans yet — go scan something!'))
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: showing.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 12),
                        itemBuilder: (context, i) =>
                            _scanTile(context, showing[i]),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _scanTile(BuildContext context, ScanSummary scan) {
    final repo = ref.read(scanRepositoryProvider);
    final selected = _selected.contains(scan.id);
    final when = scan.createdAt.toLocal();
    final stamp =
        '${when.day}/${when.month}/${when.year}  ${when.hour.toString().padLeft(2, '0')}:${when.minute.toString().padLeft(2, '0')}';
    return InkWell(
      onTap: _selectMode
          ? () => setState(() =>
              selected ? _selected.remove(scan.id) : _selected.add(scan.id))
          : () => context.go('/scans/${scan.id}'),
      onLongPress: () => setState(() {
        _selectMode = true;
        _selected.add(scan.id);
      }),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: inkRaised,
          borderRadius: BorderRadius.circular(16),
          border: selected
              ? Border.all(color: scanGlow, width: 2)
              : null,
        ),
        child: Row(
          children: [
            if (_selectMode)
              Padding(
                padding: const EdgeInsets.only(left: 8),
                child: Icon(
                  selected
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked,
                  color: selected ? scanGlow : mistText.withOpacity(0.3),
                ),
              ),
            ClipRRect(
              borderRadius: _selectMode
                  ? BorderRadius.circular(12)
                  : const BorderRadius.horizontal(left: Radius.circular(16)),
              child: SizedBox(
                width: 84,
                height: 84,
                child: FutureBuilder(
                  future: repo.image(scan.id),
                  builder: (context, s) => s.hasData
                      ? Image.memory(s.data!, fit: BoxFit.cover)
                      : Container(color: inkDeep),
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(scan.category ?? 'Unanalyzed scan',
                      style: Theme.of(context).textTheme.titleSmall),
                  const SizedBox(height: 4),
                  Text(stamp,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: mistText.withOpacity(0.5))),
                ],
              ),
            ),
            if (!_selectMode)
              const Icon(Icons.chevron_right, color: scanGlow),
            const SizedBox(width: 8),
          ],
        ),
      ),
    );
  }
}
