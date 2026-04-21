import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

class DriveScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const DriveScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _DriveScreenState createState() => _DriveScreenState();
}

class _DriveScreenState extends State<DriveScreen> {
  late ApiService _apiService;
  final _folderIdController = TextEditingController();
  Map<String, dynamic>? _syncResult;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
  }

  void _syncFolder() async {
    setState(() {
      _isLoading = true;
      _syncResult = null;
    });
    try {
      final result = await _apiService.syncDriveToRag(_folderIdController.text);
      setState(() {
        _syncResult = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            const Icon(Icons.cloud_sync, size: 80, color: AppColors.amber),
            const SizedBox(height: 20),
            const Text(
              'Sync Google Drive to RAG',
              style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 10),
            const Text(
              'Connect a Google Drive folder to sync files to the RAG system.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textDim),
            ),
            const SizedBox(height: 30),
            TextField(
              controller: _folderIdController,
              decoration: const InputDecoration(
                labelText: 'Google Drive Folder ID',
                border: OutlineInputBorder(),
              ),
              style: const TextStyle(color: Colors.white),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _isLoading ? null : _syncFolder,
              child: _isLoading ? const CircularProgressIndicator() : const Text('Sync Folder'),
            ),
            if (_syncResult != null)
              Padding(
                padding: const EdgeInsets.only(top: 20.0),
                child: Text(
                  'Synced ${_syncResult!['ingested']}/${_syncResult!['total_files']} files to RAG',
                  style: const TextStyle(color: AppColors.green),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
