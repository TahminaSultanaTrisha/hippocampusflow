// The privacy control that matters: every memory the AI holds, visible
// and individually deletable. Delete is immediate and permanent.
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/theme.dart';
import '../scan/scan_repository.dart';

class MemoriesScreen extends ConsumerStatefulWidget {
  const MemoriesScreen({super.key});
  @override
  ConsumerState<MemoriesScreen> createState() => _MemoriesScreenState();
}

class _MemoriesScreenState extends ConsumerState<MemoriesScreen> {
  List<Map<String, dynamic>>? _memories;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final memories =
        await ref.read(scanRepositoryProvider).listMemories();
    if (mounted) setState(() => _memories = memories);
  }

  Future<void> _delete(String id) async {
    await ref.read(scanRepositoryProvider).deleteMemory(id);
    if (mounted) {
      setState(() => _memories?.removeWhere((m) => m['id'] == id));
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Memory forgotten.')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
          backgroundColor: Colors.transparent, title: const Text('Memories')),
      body: _memories == null
          ? const Center(child: CircularProgressIndicator(color: scanGlow))
          : _memories!.isEmpty
              ? const Center(child: Text('Nothing remembered yet.'))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _memories!.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, i) {
                    final m = _memories![i];
                    return Container(
                      padding: const EdgeInsets.fromLTRB(14, 6, 4, 6),
                      decoration: BoxDecoration(
                          color: inkRaised,
                          borderRadius: BorderRadius.circular(14)),
                      child: Row(children: [
                        Expanded(child: Text('${m['content']}')),
                        IconButton(
                          icon: const Icon(Icons.delete_outline,
                              color: Colors.redAccent),
                          tooltip: 'Forget this',
                          onPressed: () => _delete('${m['id']}'),
                        ),
                      ]),
                    );
                  },
                ),
    );
  }
}
