// Mirrors the backend's scan endpoints. Screens call these methods and
// never touch Dio/JSON directly.
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http_parser/http_parser.dart';

import '../../core/api/api_client.dart';

class ScanSummary {
  ScanSummary({
    required this.id,
    required this.status,
    required this.createdAt,
    this.category,
    this.summary,
  });

  final String id;
  final String status;
  final DateTime createdAt;
  final String? category;
  final String? summary;

  factory ScanSummary.fromJson(Map<String, dynamic> json) => ScanSummary(
        id: json['id'],
        status: json['status'],
        createdAt: DateTime.parse(json['created_at']),
        category: json['category'],
        summary: json['summary'],
      );
}

class ScanDetail extends ScanSummary {
  ScanDetail({
    required super.id,
    required super.status,
    required super.createdAt,
    super.category,
    super.summary,
    this.confidence,
    this.details = const {},
    this.suggestedActions = const [],
  });

  final double? confidence;
  final Map<String, dynamic> details;
  final List<String> suggestedActions;

  factory ScanDetail.fromJson(Map<String, dynamic> json) => ScanDetail(
        id: json['id'],
        status: json['status'],
        createdAt: DateTime.parse(json['created_at']),
        category: json['category'],
        summary: json['summary'],
        confidence: (json['confidence'] as num?)?.toDouble(),
        details: Map<String, dynamic>.from(json['details'] ?? {}),
        suggestedActions: List<String>.from(json['suggested_actions'] ?? []),
      );
}

class ChatMessage {
  ChatMessage({required this.role, required this.content});
  final String role;
  final String content;

  factory ChatMessage.fromJson(Map<String, dynamic> json) =>
      ChatMessage(role: json['role'], content: json['content']);
}


class MemoryAnswer {
  MemoryAnswer({required this.answer, required this.scans});
  final String answer;
  final List<ScanSummary> scans;
}

class ScanRepository {
  ScanRepository(this._dio);
  final Dio _dio;
  final Map<String, Uint8List> _imageCache = {};

  Future<ScanSummary> upload(Uint8List bytes) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        bytes,
        filename: 'scan.jpg',
        contentType: MediaType('image', 'jpeg'),
      ),
    });
    final r = await _dio.post('/scans', data: form);
    return ScanSummary.fromJson(r.data);
  }

  Future<ScanDetail> scan(String id) async {
    final r = await _dio.get('/scans/$id');
    return ScanDetail.fromJson(r.data);
  }

  Future<List<ScanSummary>> history() async {
    final r = await _dio.get('/scans');
    return (r.data['scans'] as List)
        .map((j) => ScanSummary.fromJson(j))
        .toList();
  }

  Future<Uint8List> image(String scanId) async {
    final cached = _imageCache[scanId];
    if (cached != null) return cached;
    final r = await _dio.get<List<int>>(
      '/scans/$scanId/image',
      options: Options(responseType: ResponseType.bytes),
    );
    final bytes = Uint8List.fromList(r.data!);
    _imageCache[scanId] = bytes;
    return bytes;
  }


  Future<MemoryAnswer> askMemory(String question) async {
    final r = await _dio.post('/memory/ask', data: {'question': question});
    return MemoryAnswer(
      answer: r.data['answer'] ?? '',
      scans: (r.data['scans'] as List)
          .map((j) => ScanSummary.fromJson(j))
          .toList(),
    );
  }


  Future<String> runAction(String scanId, String actionType) async {
    final r = await _dio.post('/scans/$scanId/actions',
        data: {'action_type': actionType});
    return r.data['message'] ?? 'Done.';
  }



  Future<int> batchDelete(List<String> scanIds) async {
    final r = await _dio.post('/scans/batch-delete',
        data: {'scan_ids': scanIds});
    for (final id in scanIds) {
      _imageCache.remove(id);
    }
    return r.data['deleted'] ?? 0;
  }

  Future<void> deleteScan(String scanId) async {
    await _dio.delete('/scans/$scanId');
    _imageCache.remove(scanId);
  }

  Future<List<Map<String, dynamic>>> listMemories() async {
    final r = await _dio.get('/memory');
    return List<Map<String, dynamic>>.from(r.data['memories']);
  }

  Future<void> deleteMemory(String id) async {
    await _dio.delete('/memory/$id');
  }

  Future<Map<String, dynamic>> me() async {
    final r = await _dio.get('/users/me');
    return Map<String, dynamic>.from(r.data);
  }

  Future<List<ChatMessage>> messages(String scanId) async {
    final r = await _dio.get('/scans/$scanId/messages');
    return (r.data['messages'] as List)
        .map((j) => ChatMessage.fromJson(j))
        .toList();
  }

  Future<ChatMessage> sendMessage(String scanId, String content) async {
    final r = await _dio.post('/scans/$scanId/messages',
        data: {'content': content});
    return ChatMessage.fromJson(r.data);
  }
}

final scanRepositoryProvider =
    Provider((ref) => ScanRepository(ref.read(dioProvider)));
