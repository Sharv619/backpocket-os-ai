import 'dart:convert';
import 'package:flutter/foundation.dart'; // For kIsWeb

import 'package:http/http.dart' as http;
// Conditional import for File/PlatformFile
import 'package:file_picker/file_picker.dart'; // For PlatformFile

// Use dart:io for non-web platforms, dart:html for web
import 'dart:io' if (dart.library.html) 'dart:html';

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
  Future<Map<String, dynamic>> uploadDocument(PlatformFile platformFile) async {
    final uri = Uri.parse('$baseUrl/api/documents/upload');
    final req = http.MultipartRequest('POST', uri);

    if (kIsWeb) {
      // For web, use fromBytes
      req.files.add(http.MultipartFile.fromBytes(
        'file', // Field name
        platformFile.bytes!,
        filename: platformFile.name,
      ));
    } else {
      // For mobile/desktop, use fromPath (requires dart:io)
      req.files.add(await http.MultipartFile.fromPath(
        'file', // Field name
        platformFile.path!,
        filename: platformFile.name,
      ));
    }

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
    final data = jsonDecode(res.body);
    return data['documents'] ?? [];
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

  // ── Permanent Memory ──────────────────────────────────────────────────────
  Future<Map<String, dynamic>> promoteInstruction({
    required String text,
    required String category,
    required String refId,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/instructions/promote'),
      headers: _headers,
      body: jsonEncode({
        'instruction_text': text,
        'category': category,
        'ref_id': refId,
      }),
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

  // ── Email Draft + Archive ─────────────────────────────────────────────────
  Future<Map<String, dynamic>> getDraft(String refId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/draft/$refId'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> archiveEmail(String refId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/archive'),
      headers: _headers,
      body: jsonEncode({'ref_id': refId}),
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> reviseDraftWithBody(
    String refId,
    String newDraft, {
    String feedback = 'Edited in app',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/revise'),
      headers: _headers,
      body: jsonEncode({
        'ref_id': refId,
        'new_draft': newDraft,
        'feedback': feedback,
      }),
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> approveAndSend(String refId) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/approve'),
      headers: _headers,
      body: jsonEncode({'ref_id': refId}),
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  // ── SOPs ──────────────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getSops() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/sops'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Email Rules ───────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getEmailRules() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/email-rules'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Sender Instructions ───────────────────────────────────────────────────
  Future<Map<String, dynamic>> getSenderInstructions() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/sender-instructions'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> addSenderInstruction(
    String email,
    String instructions,
    String category,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/sender-instructions'),
      headers: _headers,
      body: jsonEncode({
        'sender_email': email,
        'instructions': instructions,
        'category': category,
      }),
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> deleteSenderInstruction(String email) async {
    final res = await http.delete(
      Uri.parse('$baseUrl/api/sender-instructions/${Uri.encodeComponent(email)}'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Instruction CRUD (update + delete) ────────────────────────────────────
  Future<Map<String, dynamic>> updateInstruction(
    int id, {
    required String text,
    required String category,
    bool isActive = true,
    bool isCritical = false,
  }) async {
    final res = await http.put(
      Uri.parse('$baseUrl/api/instructions/$id'),
      headers: _headers,
      body: jsonEncode({
        'instruction_text': text,
        'category': category,
        'is_active': isActive,
        'is_critical': isCritical,
      }),
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> deleteInstruction(int id) async {
    final res = await http.delete(
      Uri.parse('$baseUrl/api/instructions/$id'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Agentic RAG ───────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> getAgenticRagContext(String refId) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/agentic-rag/context/$refId'),
      headers: _headers,
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  // ── Blog & Content ────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> generateBlogPost(String title, String theme) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/blog/generate?title=${Uri.encodeComponent(title)}&theme=${Uri.encodeComponent(theme)}'),
      headers: _headers,
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  Future<Map<String, dynamic>> generateStartupStory(
    String companyName, {
    String theme = 'entrepreneurship',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/blog/startup-story'),
      headers: _headers,
      body: jsonEncode({'company_name': companyName, 'theme': theme}),
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  // ── Drive Integration ─────────────────────────────────────────────────────
  Future<Map<String, dynamic>> syncDriveToRag(
    String folderId, {
    String twinType = 'admin',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/drive/sync-to-rag'),
      headers: _headers,
      body: jsonEncode({'folder_id': folderId, 'twin_type': twinType}),
    ).timeout(_tAI);
    return await _handleResponse(res);
  }

  // ── Client Master (Google Sheets CRM) ─────────────────────────────────────
  Future<Map<String, dynamic>> getClientMaster() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/client-master'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Invoice PDF Generation ────────────────────────────────────────────────
  Future<List<int>> generateInvoicePdf({
    required String clientName,
    String clientEmail = '',
    required List<Map<String, dynamic>> items,
    String notes = '',
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/invoice/generate'),
      headers: _headers,
      body: jsonEncode({
        'client_name': clientName,
        'client_email': clientEmail,
        'items': items,
        'notes': notes,
      }),
    ).timeout(_tAI);
    if (res.statusCode != 200) {
      throw ApiException('Invoice generation failed', statusCode: res.statusCode);
    }
    return res.bodyBytes;
  }

  // ── Marketing Activity (full stats) ───────────────────────────────────────
  Future<Map<String, dynamic>> getMarketingActivityFull() async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/marketing/activity'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }

  // ── Search Gmail ──────────────────────────────────────────────────────────
  Future<Map<String, dynamic>> searchGmail(String query, {int maxResults = 10}) async {
    final res = await http.get(
      Uri.parse('$baseUrl/api/search-gmail?q=${Uri.encodeComponent(query)}&max_results=$maxResults'),
      headers: _headers,
    ).timeout(_tFast);
    return await _handleResponse(res);
  }
}
