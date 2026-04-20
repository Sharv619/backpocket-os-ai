import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class DriveScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const DriveScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<DriveScreen> createState() => _DriveScreenState();
}

class _DriveScreenState extends State<DriveScreen> {
  final _folderIdCtrl = TextEditingController();
  bool _syncing = false;
  Map<String, dynamic>? _result;
  String? _error;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _sync() async {
    final folderId = _folderIdCtrl.text.trim();
    if (folderId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a Google Drive Folder ID')),
      );
      return;
    }
    setState(() { _syncing = true; _error = null; _result = null; });
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/drive/sync-to-rag'),
        headers: _headers,
        body: jsonEncode({'folder_id': folderId, 'twin_type': 'admin'}),
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      setState(() { _result = data; _syncing = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _syncing = false; });
    }
  }

  @override
  void dispose() {
    _folderIdCtrl.dispose();
    super.dispose();
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
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const SizedBox(height: 20),
          const Center(child: Icon(Icons.cloud_outlined, color: AppColors.amber, size: 56)),
          const SizedBox(height: 16),
          const Center(
            child: Text('Google Drive', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 8),
          const Center(
            child: Text(
              'Sync a Drive folder to the RAG system\nfor AI-powered document analysis.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.5),
            ),
          ),
          const SizedBox(height: 28),
          TextField(
            controller: _folderIdCtrl,
            style: const TextStyle(color: Colors.white, fontSize: 14),
            decoration: InputDecoration(
              labelText: 'Google Drive Folder ID',
              labelStyle: const TextStyle(color: AppColors.textMuted),
              hintText: 'Paste folder ID from Drive URL',
              hintStyle: const TextStyle(color: AppColors.textMuted),
              filled: true,
              fillColor: AppColors.card,
              prefixIcon: const Icon(Icons.folder_outlined, color: AppColors.textMuted),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.border)),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.border)),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppColors.amber)),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _syncing ? null : _sync,
            icon: _syncing
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                : const Icon(Icons.sync),
            label: Text(_syncing ? 'Syncing...' : 'Sync Folder to RAG'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.orange,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: AppColors.red.withAlpha(30), borderRadius: BorderRadius.circular(8)),
              child: Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
            ),
          ],
          if (_result != null) ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.green.withAlpha(20),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.green.withAlpha(76)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.check_circle, color: AppColors.green, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Synced ${_result!['ingested'] ?? 0} / ${_result!['total_files'] ?? 0} files to RAG',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
