import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const Color kBg = Color(0xFF0D0A07);
const Color kSurface = Color(0xFF1A1208);
const Color kCard = Color(0xFF211708);
const Color kBorder = Color(0x22FFFFFF);
const Color kAmber = Color(0xFFFBBF24);
const Color kOrange = Color(0xFFF97316);
const Color kRed = Color(0xFFEF4444);
const Color kGreen = Color(0xFF22C55E);
const Color kTextDim = Color(0x99FFFFFF);
const Color kTextMuted = Color(0x44FFFFFF);

class DocumentsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const DocumentsScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<DocumentsScreen> createState() => _DocumentsScreenState();
}

class _DocumentsScreenState extends State<DocumentsScreen> {
  List<dynamic> _documents = [];
  bool _loading = true;
  bool _analyzing = false;

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    setState(() => _loading = true);
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/documents'),
        headers: headers,
      );
      setState(() => _documents = jsonDecode(res.body) ?? []);
    } catch (e) {
      debugPrint('Load docs error: $e');
    }
    setState(() => _loading = false);
  }

  Future<void> _uploadAndAnalyze() async {
    final picker = ImagePicker();
    final xfile = await picker.pickImage(source: ImageSource.gallery);
    if (xfile == null) return;

    setState(() => _analyzing = true);

    try {
      final headers = {
        if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
      };

      final bytes = await xfile.readAsBytes();
      final fileName = xfile.name;

      // Try multipart first (works on mobile), fall back to base64 (web)
      try {
        final uri = Uri.parse('${widget.serverUrl}/api/documents/upload');
        final request = http.MultipartRequest('POST', uri);
        request.files.add(
          http.MultipartFile.fromBytes('file', bytes, filename: fileName),
        );
        final streamed = await request.send();
        final body = await streamed.stream.bytesToString();
        var uploadResult = jsonDecode(body);

        if (uploadResult['status'] != 'success') {
          throw Exception(uploadResult['message'] ?? 'Upload failed');
        }
        var docId = uploadResult['document_id'];

        // Analyze
        final analyzeRes = await http.post(
          Uri.parse('${widget.serverUrl}/api/documents/analyze/$docId'),
          headers: {'Content-Type': 'application/json', ...headers},
        );
        final analysis = jsonDecode(analyzeRes.body);

        setState(() => _analyzing = false);

        if (analysis['status'] == 'success') {
          _showSnack('Document analyzed!', isError: false);
          _loadDocuments();
        } else {
          _showSnack('Analysis failed: ${analysis['message']}', isError: true);
        }
      } catch (multipartError) {
        // Fall back to base64 for web/unsupported platforms
        final base64File = base64Encode(bytes);
        final uploadRes = await http.post(
          Uri.parse('${widget.serverUrl}/api/documents/upload'),
          headers: {'Content-Type': 'application/json', ...headers},
          body: jsonEncode({'file': base64File, 'filename': fileName}),
        );
        final uploadResult = jsonDecode(uploadRes.body);

        if (uploadResult['status'] != 'success') {
          throw Exception(uploadResult['message'] ?? 'Upload failed');
        }

        final docId = uploadResult['document_id'];
        final analyzeRes = await http.post(
          Uri.parse('${widget.serverUrl}/api/documents/analyze/$docId'),
          headers: {'Content-Type': 'application/json', ...headers},
        );
        final analysis = jsonDecode(analyzeRes.body);

        setState(() => _analyzing = false);

        if (analysis['status'] == 'success') {
          _showSnack('Document analyzed!', isError: false);
          _loadDocuments();
        } else {
          _showSnack('Analysis failed: ${analysis['message']}', isError: true);
        }
      }
    } catch (e) {
      setState(() => _analyzing = false);
      _showSnack('Error: $e', isError: true);
    }
  }

  void _showSnack(String msg, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: isError ? kRed : kGreen,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [kBg, Color(0xFF1A1008)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: kAmber))
          : Column(
              children: [
                // Upload button
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: GestureDetector(
                    onTap: _analyzing ? null : _uploadAndAnalyze,
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        gradient: _analyzing
                            ? null
                            : const LinearGradient(
                                colors: [kOrange, Color(0xFFEA580C)],
                              ),
                        color: _analyzing ? kSurface : null,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: kBorder),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (_analyzing)
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(
                                color: kAmber,
                                strokeWidth: 2,
                              ),
                            )
                          else
                            const Icon(Icons.cloud_upload, color: Colors.white),
                          const SizedBox(width: 8),
                          Text(
                            _analyzing
                                ? 'Analyzing...'
                                : 'Upload & Analyze with AI',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                // Documents list
                Expanded(
                  child: _documents.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.folder_open,
                                color: kTextMuted,
                                size: 48,
                              ),
                              const SizedBox(height: 12),
                              const Text(
                                'No documents yet',
                                style: TextStyle(color: kTextDim),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Upload an image to analyze',
                                style: TextStyle(
                                  color: kTextMuted,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _documents.length,
                          itemBuilder: (context, index) {
                            final doc = _documents[index];
                            return _DocumentCard(
                              doc: doc,
                              onAnalyze: () => _analyzeDoc(doc['id']),
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Future<void> _analyzeDoc(int docId) async {
    setState(() => _analyzing = true);
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/documents/analyze/$docId'),
        headers: headers,
      );
      final analysis = jsonDecode(res.body);
      setState(() => _analyzing = false);

      if (analysis['status'] == 'success') {
        _showSnack('Analysis complete!', isError: false);
        _loadDocuments();
      } else {
        _showSnack('Failed: ${analysis['message']}', isError: true);
      }
    } catch (e) {
      setState(() => _analyzing = false);
      _showSnack('Error: $e', isError: true);
    }
  }
}

class _DocumentCard extends StatelessWidget {
  final Map<String, dynamic> doc;
  final VoidCallback onAnalyze;

  const _DocumentCard({required this.doc, required this.onAnalyze});

  @override
  Widget build(BuildContext context) {
    final status = doc['status'] ?? 'pending';
    final hasAnalysis =
        doc['ai_analysis'] != null && (doc['ai_analysis'] as String).isNotEmpty;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: kBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: kAmber.withAlpha(26),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.description, color: kAmber, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      doc['original_name'] ?? doc['filename'] ?? 'Document',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      doc['created_at']?.toString().split('.').first ?? '',
                      style: const TextStyle(color: kTextMuted, fontSize: 11),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: hasAnalysis
                      ? kGreen.withAlpha(26)
                      : (status == 'analyzing'
                            ? kAmber.withAlpha(26)
                            : kSurface),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                    color: hasAnalysis
                        ? kGreen.withAlpha(102)
                        : (status == 'analyzing'
                              ? kAmber.withAlpha(102)
                              : kBorder),
                  ),
                ),
                child: Text(
                  hasAnalysis
                      ? 'Analyzed'
                      : (status == 'analyzing' ? 'Analyzing...' : 'Pending'),
                  style: TextStyle(
                    color: hasAnalysis
                        ? kGreen
                        : (status == 'analyzing' ? kAmber : kTextMuted),
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          if (hasAnalysis) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: kSurface,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                doc['ai_analysis'],
                style: const TextStyle(
                  color: kTextDim,
                  fontSize: 12,
                  height: 1.5,
                ),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
