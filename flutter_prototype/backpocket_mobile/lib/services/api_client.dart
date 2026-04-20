import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/pending_email.dart';
import '../models/lead.dart';
import '../models/quote.dart';
import '../models/payment.dart';

class ApiClient {
  static ApiClient? _instance;
  static String _baseUrl = 'http://127.0.0.1:8000';
  static String _apiKey = '';

  static Future<ApiClient> getInstance() async {
    if (_instance != null) return _instance!;
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('server_url') ?? 'http://127.0.0.1:8000';
    _apiKey = prefs.getString('api_key') ?? '';
    _instance = ApiClient._();
    return _instance!;
  }

  ApiClient._();

  String get baseUrl => _baseUrl;
  String get apiKey => _apiKey;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (_apiKey.isNotEmpty) 'X-API-Key': _apiKey,
  };

  Future<void> setCredentials(String url, String key) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', url);
    await prefs.setString('api_key', key);
    _baseUrl = url;
    _apiKey = key;
  }

  Future<List<PendingEmail>> getPendingEmails() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/mobile/pending'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return (data['items'] as List?)
            ?.map((e) => PendingEmail.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];
  }

  Future<bool> approveEmail(String refId, {String? note}) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/mobile/approve'),
      headers: _headers,
      body: jsonEncode({
        'ref_id': refId,
        'note': note ?? 'approved via mobile',
      }),
    );
    final data = jsonDecode(res.body);
    final status = data['status'] as String? ?? '';
    return status == 'approved' || status == 'demo';
  }

  Future<List<Lead>> getLeads() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/construction/leads'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return (data['leads'] as List?)
            ?.map((e) => Lead.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];
  }

  Future<Lead> createLead({
    required String clientName,
    required String email,
    required String jobType,
    required String location,
    required String urgency,
    required int estimatedBudget,
  }) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/construction/leads'),
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
    final data = jsonDecode(res.body);
    return Lead.fromJson(data);
  }

  Future<List<Quote>> getQuotes() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/construction/quotes'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return (data['quotes'] as List?)
            ?.map((e) => Quote.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];
  }

  Future<Quote> createQuote({
    required int leadId,
    required double materialsCost,
    required double laborHours,
    required int markupPercent,
  }) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/construction/quotes'),
      headers: _headers,
      body: jsonEncode({
        'lead_id': leadId,
        'materials_cost': materialsCost,
        'labor_hours': laborHours,
        'markup_percent': markupPercent,
      }),
    );
    final data = jsonDecode(res.body);
    return Quote.fromJson(data);
  }

  Future<List<Payment>> getPayments() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/api/construction/payments'),
      headers: _headers,
    );
    final data = jsonDecode(res.body);
    return (data['payments'] as List?)
            ?.map((e) => Payment.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];
  }

  Future<bool> recordPayment(int quoteId, double amount) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/construction/payments'),
      headers: _headers,
      body: jsonEncode({'quote_id': quoteId, 'amount': amount}),
    );
    return res.statusCode == 200;
  }

  Future<Map<String, dynamic>> sendChat(String message) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/api/mobile/chat'),
      headers: _headers,
      body: jsonEncode({'message': message}),
    );
    return jsonDecode(res.body);
  }
}
