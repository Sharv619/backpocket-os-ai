import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class AgenticRagScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const AgenticRagScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<AgenticRagScreen> createState() => _AgenticRagScreenState();
}

class _AgenticRagScreenState extends State<AgenticRagScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _ragData;
  String _emailSubject = '';

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      // Get first pending email
      final pendingRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/pending'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      final pendingData = jsonDecode(pendingRes.body) as Map<String, dynamic>;
      final items = pendingData['items'] as List? ?? [];

      if (items.isEmpty) {
        setState(() { _loading = false; _error = 'No emails to analyze'; });
        return;
      }

      final refId = items[0]['ref_id'] as String? ?? '';
      _emailSubject = items[0]['subject'] as String? ?? 'Unknown';

      final ragRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/agentic-rag/context/$refId'),
        headers: _headers,
      ).timeout(const Duration(seconds: 30));
      final data = jsonDecode(ragRes.body) as Map<String, dynamic>;

      if (mounted) setState(() { _ragData = data; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF1A1008)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : _error != null
              ? _buildError()
              : _buildContent(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.psychology_outlined, color: AppColors.textMuted, size: 48),
          const SizedBox(height: 16),
          Text(_error!, style: const TextStyle(color: AppColors.textDim), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          TextButton.icon(
            onPressed: _load,
            icon: const Icon(Icons.refresh, size: 16),
            label: const Text('Retry'),
            style: TextButton.styleFrom(foregroundColor: AppColors.amber),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    final analysis = _ragData?['agentic_analysis'] as Map<String, dynamic>? ?? {};
    final twin = analysis['twin'] as String? ?? 'N/A';
    final prompt = analysis['system_prompt'] as String? ?? 'N/A';
    final patterns = analysis['learned_patterns']?.toString() ?? 'No patterns found';

    return RefreshIndicator(
      color: AppColors.amber,
      backgroundColor: AppColors.card,
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Email Analysis
          Text('RAG Analysis', style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(_emailSubject, style: const TextStyle(color: AppColors.textDim, fontSize: 13)),
          const SizedBox(height: 20),

          _card(
            icon: Icons.smart_toy_outlined,
            iconColor: AppColors.amber,
            title: 'Twin Selected',
            child: Text(twin, style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600)),
          ),
          const SizedBox(height: 12),

          _card(
            icon: Icons.description_outlined,
            iconColor: AppColors.orange,
            title: 'System Prompt',
            child: Text(prompt, style: const TextStyle(color: AppColors.textDim, fontSize: 12, height: 1.5)),
          ),
          const SizedBox(height: 12),

          _card(
            icon: Icons.auto_awesome_outlined,
            iconColor: AppColors.green,
            title: 'Learned Patterns',
            child: Text(patterns, style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.5)),
          ),
          const SizedBox(height: 24),

          // Twin agents display
          const Text('Your Twin Agents', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          _agentCard('Estimator Twin', 'Handles Measurements, parsing Construction Leads, and calculating Quotes/Payments.', Icons.calculate_outlined, const Color(0xFF2663EB)),
          const SizedBox(height: 8),
          _agentCard('Site Manager Twin', 'Handles Documents (OCR scanning of receipts/materials) and pushes Marketing posts from completed jobs.', Icons.construction_outlined, AppColors.green),
          const SizedBox(height: 8),
          _agentCard('Admin Twin', 'Handles Inbox Triage, email drafting, and the conversational Pip Chat.', Icons.admin_panel_settings_outlined, AppColors.red),
        ],
      ),
    );
  }

  Widget _card({required IconData icon, required Color iconColor, required String title, required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor, size: 18),
              const SizedBox(width: 8),
              Text(title, style: TextStyle(color: iconColor, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
            ],
          ),
          const SizedBox(height: 10),
          child,
        ],
      ),
    );
  }

  Widget _agentCard(String name, String desc, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(12),
        border: Border(left: BorderSide(color: color, width: 3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 28),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 2),
                Text(desc, style: const TextStyle(color: AppColors.textDim, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
