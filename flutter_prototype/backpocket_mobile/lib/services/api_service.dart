import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  final String baseUrl;
  final String apiKey;

  ApiService({required this.baseUrl, this.apiKey = ''});

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
  };

  // ── Status & Workflow ───────────────────────────────────────────────────
  Future<Map<String, dynamic>> getStatus() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/status'),
      headers: _headers,
    );
    return jsonDecode(res.body);
  }

  Future<List<dynamic>> getWorkflowStages() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/workflow/stages'),
      headers: _headers,
    );
    return jsonDecode(res.body)['stages'] ?? [];
  }

  Future<Map<String, dynamic>> getCurrentStage() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/workflow/current'),
      headers: _headers,
    );
    return jsonDecode(res.body);
  }

  // ── Pending Emails (Inbox) ───────────────────────────────────────────────
  Future<List<dynamic>> getPendingEmails() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/mobile/pending'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return data['items'] ?? [];
  }

  Future<Map<String, dynamic>> approveEmail(
    String refId, {
    String? note,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/mobile/approve'),
      headers: _headers,
      body: jsonEncode({
        'ref_id': refId,
        'note': note ?? 'approved via mobile',
      }),
    );
    return jsonDecode(res.body);
  }

  // ── Documents ──────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> uploadDocument(File file) async {
    final uri = Uri.parse('$baseUrl/api/documents/upload');
    final req = http.MultipartRequest('POST', uri)
      ..files.add(await http.MultipartFile.fromPath('file', file.path));
    final streamed = await req.send();
    final body = await streamed.stream.bytesToString();
    return jsonDecode(body);
  }

  Future<Map<String, dynamic>> analyzeDocument(int docId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/documents/analyze/$docId'),
      headers: _headers,
    );
    return jsonDecode(res.body);
  }

  Future<List<dynamic>> getDocuments() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/documents'),
      headers: _headers,
    );
    return jsonDecode(res.body) ?? [];
  }

  // ── Marketing ──────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> createGbpPost(
    String jobDesc,
    String suburb,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/marketing/gbp-post'),
      headers: _headers,
      body: jsonEncode({'job_description': jobDesc, 'suburb': suburb}),
    );
    return jsonDecode(res.body);
  }

  Future<Map<String, dynamic>> getMarketingInsights() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/marketing/insights'),
      headers: _headers,
    );
    return jsonDecode(res.body);
  }

  Future<List<dynamic>> getMarketingActivity() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/marketing/activity'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return data['activity'] ?? [];
  }

  // ── Twin Chat ──────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> sendChatMessage(String message) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/mobile/chat'),
      headers: _headers,
      body: jsonEncode({'message': message}),
    );
    return jsonDecode(res.body);
  }

  // ── Instructions ────────────────────────────────────────────────────────────
  Future<List<dynamic>> getInstructions() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/instructions'),
      headers: _headers,
    );
    return jsonDecode(res.body) ?? [];
  }

  Future<Map<String, dynamic>> saveInstruction(
    String text,
    String category,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/instruction'),
      headers: _headers,
      body: jsonEncode({
        'instruction_text': text,
        'category': category,
        'is_active': 1,
      }),
    );
    return jsonDecode(res.body);
  }

  // ── Voice TTS ─────────────────────────────────────────────────────────────
  Future<String?> testVoice(String text) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/api/voice/tts'),
        headers: {
          'Content-Type': 'application/json',
          if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
        },
        body: jsonEncode({'text': text, 'voice': 'male'}),
      );
      if (res.statusCode == 200) return 'elevenlabs';
    } catch (e) {
      // Fall back to web speech
    }
    return null;
  }
}
