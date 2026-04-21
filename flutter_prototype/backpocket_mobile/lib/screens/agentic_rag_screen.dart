import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_service.dart';
import '../theme.dart';

class AgenticRagScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const AgenticRagScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _AgenticRagScreenState createState() => _AgenticRagScreenState();
}

class _AgenticRagScreenState extends State<AgenticRagScreen> {
  late ApiService _apiService;
  Map<String, dynamic>? _ragContext;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _fetchRagContext();
  }

  Future<void> _fetchRagContext() async {
    try {
      final pendingEmails = await _apiService.getPendingEmails();
      if (pendingEmails.isNotEmpty) {
        final refId = pendingEmails.first['ref_id'];
        final data = await _apiService.getAgenticRagContext(refId);
        setState(() {
          _ragContext = data;
          _loading = false;
        });
      } else {
        setState(() {
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (_ragContext != null) ...[
                    Text('Email Analysis', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    SizedBox(height: 10),
                    Card(
                      color: AppColors.card,
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Subject: ${_ragContext!['email']['subject'] ?? 'N/A'}', style: TextStyle(color: Colors.white)),
                            Text('Twin: ${_ragContext!['agentic_analysis']['twin'] ?? 'N/A'}', style: TextStyle(color: Colors.white)),
                            Text('System Prompt: ${_ragContext!['agentic_analysis']['system_prompt'] ?? 'N/A'}', style: TextStyle(color: AppColors.textDim)),
                            Text('Learned Patterns: ${_ragContext!['agentic_analysis']['learned_patterns']?.length ?? 0}', style: TextStyle(color: AppColors.textDim)),
                          ],
                        ),
                      ),
                    ),
                  ],
                  SizedBox(height: 20),
                  Text('Pip Agents', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _agentCard('Accountant Twin', 'Handles invoicing, BAS, tax compliance', Icons.account_balance, Colors.blue),
                      _agentCard('Auditor Twin', 'Reviews documents, verifies compliance', Icons.check_circle, Colors.green),
                      _agentCard('Admin Twin', 'Email triage, scheduling, automation', Icons.settings, Colors.red),
                    ],
                  ),
                ],
              ),
            ),
    );
  }

  Widget _agentCard(String title, String subtitle, IconData icon, Color color) {
    return Card(
      color: AppColors.card,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Icon(icon, color: color, size: 40),
            SizedBox(height: 10),
            Text(title, style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            SizedBox(height: 5),
            Text(subtitle, style: TextStyle(color: AppColors.textDim), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
