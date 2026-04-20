import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class ClientCrmScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const ClientCrmScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<ClientCrmScreen> createState() => _ClientCrmScreenState();
}

class _ClientCrmScreenState extends State<ClientCrmScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _clients = [];
  int _totalCount = 0;

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
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/client-master'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(res.body) as Map<String, dynamic>;

      if (data['status'] == 'error') {
        setState(() { _error = data['message'] as String? ?? 'Failed to load'; _loading = false; });
        return;
      }

      final clients = (data['clients'] as List? ?? [])
          .map((c) => Map<String, dynamic>.from(c as Map))
          .toList();

      setState(() {
        _clients = clients;
        _totalCount = data['count'] as int? ?? clients.length;
        _loading = false;
      });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
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
              : _clients.isEmpty
                  ? _buildEmpty()
                  : _buildList(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.error_outline, color: AppColors.red, size: 48),
          const SizedBox(height: 16),
          Text(_error!, style: const TextStyle(color: AppColors.textDim), textAlign: TextAlign.center),
          const SizedBox(height: 16),
          TextButton.icon(onPressed: _load, icon: const Icon(Icons.refresh, size: 16), label: const Text('Retry'),
            style: TextButton.styleFrom(foregroundColor: AppColors.amber)),
        ],
      ),
    );
  }

  Widget _buildEmpty() {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.people_outline, color: AppColors.textMuted, size: 48),
          SizedBox(height: 16),
          Text('No Clients', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text('No clients in BPS_Client_Master yet.', style: TextStyle(color: AppColors.textDim, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildList() {
    return RefreshIndicator(
      color: AppColors.amber,
      backgroundColor: AppColors.card,
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              const Icon(Icons.people, color: AppColors.amber, size: 20),
              const SizedBox(width: 8),
              Text('Client CRM', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.amber.withAlpha(30),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text('$_totalCount clients', style: const TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ..._clients.take(50).map((client) {
            final name = '${client['first_name'] ?? ''} ${client['last_name'] ?? ''}'.trim();
            final email = client['primary_email'] as String? ?? client['email'] as String? ?? '';
            final status = client['client_status'] as String? ?? '';
            final mobile = client['mobile'] as String? ?? '';
            final bg = client['background_info'] as String? ?? '';

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(14),
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
                      Expanded(
                        child: Text(
                          name.isNotEmpty ? name : 'Unknown',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                        ),
                      ),
                      if (status.isNotEmpty)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.amber.withAlpha(25),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(status, style: const TextStyle(color: AppColors.amber, fontSize: 10, fontWeight: FontWeight.w600)),
                        ),
                    ],
                  ),
                  if (email.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.email_outlined, color: AppColors.textMuted, size: 12),
                        const SizedBox(width: 6),
                        Expanded(child: Text(email, style: const TextStyle(color: AppColors.textDim, fontSize: 12), overflow: TextOverflow.ellipsis)),
                      ],
                    ),
                  ],
                  if (mobile.isNotEmpty) ...[
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.phone_outlined, color: AppColors.textMuted, size: 12),
                        const SizedBox(width: 6),
                        Text(mobile, style: const TextStyle(color: AppColors.textDim, fontSize: 12)),
                      ],
                    ),
                  ],
                  if (bg.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(bg, style: const TextStyle(color: AppColors.textMuted, fontSize: 11, height: 1.4), maxLines: 2, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
