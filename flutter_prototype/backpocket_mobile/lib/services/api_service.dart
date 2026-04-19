import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

// ── Exception Handling ──────────────────────────────────────────────────────
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  final String baseUrl;
  final String apiKey;

  // Timeout tiers matched to actual backend processing time
  static const _tFast = Duration(seconds: 10); // status, lists, CRUD
  static const _tAI      = Duration(seconds: 45);   // chat, twin, draft generation
  static const _tVision  = Duration(seconds: 90);   // vision analysis (Ollama + OpenRouter)
  static const _tAudio   = Duration(seconds: 30);   // ElevenLabs TTS

  ApiService({required this.baseUrl, this.apiKey = ''});

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
  };

  // ── Response Handler ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> _handleResponse(http.Response response) async {
    if (response.statusCode != 200) {
      try {
        final error = jsonDecode(response.body);
        throw ApiException(
          error['message'] ?? 'API Error',
          statusCode: response.statusCode,
        );
      } catch (e) {
        throw ApiException(
          'Failed with status ${response.statusCode}',
          statusCode: response.statusCode,
        );
      }
    }
    return jsonDecode(response.body) ?? {};
  }

  // ── Status & Workflow ───────────────────────────────────────────────────
  Future<Map<String, dynamic>> getStatus() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/status'),
      headers: _headers,
    ).timeout(_tFast);
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
    ).timeout(_tVision);
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
    ).timeout(_tAI);
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
      Uri.parse('$baseUrl/api/instructions'),
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
      ).timeout(_tAudio);
      if (res.statusCode == 200) return 'elevenlabs';
    } catch (e) {
      // Fall back to web speech
    }
    return null;
  }

  // ── Construction (Leads, Quotes, Payments) ──────────────────────────────────
  Future<List<dynamic>> getConstructionLeads() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/leads'),
      headers: _headers,
    );
    final data = await _handleResponse(res);
    return data['leads'] ?? [];
  }

  Future<Map<String, dynamic>> createLead({
    required String clientName,
    required String email,
    required String jobType,
    required String location,
    required String urgency,
    required int estimatedBudget,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/construction/leads'),
      headers: _headers,
      body: jsonEncode({
        'client_name': clientName,
        'email': email,
        'job_type': jobType,
        'location': location,
        'urgency': urgency,
        'estimated_budget': estimatedBudget,
      }),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> getLead(int id) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/leads/$id'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> updateLeadStatus(
    int id,
    String status,
  ) async {
    final res = await http.patch(
      Uri.parse('$baseUrl/api/construction/leads/$id'),
      headers: _headers,
      body: jsonEncode({'status': status}),
    );
    return await _handleResponse(res);
  }

  Future<List<dynamic>> getConstructionQuotes() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/quotes'),
      headers: _headers,
    );
    final data = await _handleResponse(res);
    return data['quotes'] ?? [];
  }

  Future<Map<String, dynamic>> createQuote({
    required int leadId,
    required double materialsCost,
    required double laborCost,
    required double markupPercent,
    String clientName = '',
    String jobType = '',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/construction/quotes'),
      headers: _headers,
      body: jsonEncode({
        'lead_id': leadId,
        'client_name': clientName,
        'job_type': jobType,
        'materials_cost': materialsCost,
        'labor_cost': laborCost,
        'markup_percent': markupPercent,
      }),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> getQuote(int id) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/quotes/$id'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> updateQuoteStatus(
    int id,
    String status,
  ) async {
    final res = await http.patch(
      Uri.parse('$baseUrl/api/construction/quotes/$id'),
      headers: _headers,
      body: jsonEncode({'status': status}),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> getConstructionPipeline() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/pipeline'),
      headers: _headers,
    );
    final body = await _handleResponse(res);
    final data = body['data'];
    if (data is Map<String, dynamic>) return data;
    return body;
  }

  Future<List<dynamic>> getConstructionPayments() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/construction/payments'),
      headers: _headers,
    );
    final data = await _handleResponse(res);
    return data['payments'] ?? [];
  }

  Future<Map<String, dynamic>> recordPayment({
    required int quoteId,
    required double amount,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/construction/payments'),
      headers: _headers,
      body: jsonEncode({
        'quote_id': quoteId,
        'amount': amount,
      }),
    );
    return await _handleResponse(res);
  }

  // ── Conversations ──────────────────────────────────────────────────────────
  Future<List<dynamic>> getConversations() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/conversations'),
      headers: _headers,
    );
    final data = await _handleResponse(res);
    return data['conversations'] ?? [];
  }

  Future<Map<String, dynamic>> getConversation(String id) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/conversations/$id'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> deleteConversation(String id) async {
    final res = await http.delete(
      Uri.parse('$baseUrl/api/conversations/$id'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  // ── Draft Editing ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> reviseDraft(
    String refId,
    String instructions,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/revise'),
      headers: _headers,
      body: jsonEncode({
        'ref_id': refId,
        'instructions': instructions,
      }),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> saveDraft(
    String refId,
    String newText,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/draft/$refId'),
      headers: _headers,
      body: jsonEncode({'body': newText}),
    );
    return await _handleResponse(res);
  }

  // ── Voice Commands ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> sendVoiceCommand({
    required String transcript,
    required String screenContext,
    String? sessionId,
    int? selectedItemId,
    int? tabIndex,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/voice/command'),
      headers: _headers,
      body: jsonEncode({
        'transcript': transcript,
        'screen_context': screenContext,
        'session_id': sessionId,
        'metadata': {
          'selected_item_id': selectedItemId,
          'tab_index': tabIndex,
        },
      }),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> confirmVoiceAction({
    required String sessionId,
    required String response,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/voice/confirm'),
      headers: _headers,
      body: jsonEncode({
        'session_id': sessionId,
        'response': response,
      }),
    );
    return await _handleResponse(res);
  }

  Future<List<dynamic>> getVoiceIntents(String screen) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/voice/intents?screen=$screen'),
      headers: _headers,
    );
    final data = await _handleResponse(res);
    return data['intents'] ?? [];
  }

  Future<Map<String, dynamic>> createVoiceSession() async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/voice/session'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  // ── SOVEREIGN ENGINE — Bring Your Own Key (BYOK) ──────────────────────────
  Future<Map<String, dynamic>> setBYOKKey({
    required String provider,
    required String apiKey,
    String? voiceId,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/settings/byok'),
      headers: _headers,
      body: jsonEncode({
        'provider': provider,
        'api_key': apiKey,
        if (voiceId != null) 'voice_id': voiceId,
      }),
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> getBYOKStatus() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/settings/byok-status'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> clearBYOKKey(String provider) async {
    final res = await http.delete(
      Uri.parse('$baseUrl/api/settings/byok/$provider'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  // ── Style Scanner ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> scanWritingStyle({String tokenFile = 'token.json'}) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/style/scan-sent'),
      headers: _headers,
      body: jsonEncode({'token_file': tokenFile}),
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> getCurrentStyle() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/style/current'),
      headers: _headers,
    );
    return await _handleResponse(res);
  }

  // ── Material Vision Analysis ───────────────────────────────────────────────
  Future<Map<String, dynamic>> analyzeMaterialImage({
    required String imageBase64,
    String analysisType = 'material',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/documents/analyze-material'),
      headers: _headers,
      body: jsonEncode({
        'image_base64': imageBase64,
        'analysis_type': analysisType,
      }),
    ).timeout(_tVision);
    return await _handleResponse(res);
  }
}
