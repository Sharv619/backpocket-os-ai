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

    // Show option to choose camera or gallery
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Select Source',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.camera_alt, color: kAmber),
              title: const Text('Camera'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library, color: kAmber),
              title: const Text('Gallery'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );

    if (source == null) return;

    final xfile = await picker.pickImage(source: source, imageQuality: 85);
    if (xfile == null) return;

    setState(() => _analyzing = true);

    try {
      final headers = {
        'Content-Type': 'application/json',
        if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
      };

      // Read file with error handling
      final bytes = await xfile.readAsBytes();
      final fileName = xfile.name;

      debugPrint('Uploading: $fileName (${bytes.length} bytes)');

      // Try base64 approach - more reliable across platforms
      final base64File = base64Encode(bytes);

      // Upload with retry logic (3 attempts)
      var uploadResult;
      var lastError;

      for (var attempt = 1; attempt <= 3; attempt++) {
        try {
          debugPrint('Upload attempt $attempt...');

          final uploadRes = await http
              .post(
                Uri.parse('${widget.serverUrl}/api/documents/upload'),
                headers: {'Content-Type': 'application/json', ...headers},
                body: jsonEncode({'file': base64File, 'filename': fileName}),
              )
              .timeout(const Duration(seconds: 60));

          if (uploadRes.statusCode == 200) {
            uploadResult = jsonDecode(uploadRes.body);
            debugPrint('Upload success: $uploadResult');
            break;
          } else {
            lastError = 'HTTP ${uploadRes.statusCode}: ${uploadRes.body}';
            debugPrint('Upload failed: $lastError');
          }
        } catch (e) {
          lastError = e.toString();
          debugPrint('Upload error (attempt $attempt): $lastError');

          // Wait before retry (exponential backoff)
          if (attempt < 3) {
            await Future.delayed(Duration(milliseconds: 500 * attempt));
          }
        }
      }

      if (uploadResult == null || uploadResult['status'] != 'success') {
        throw Exception(lastError ?? 'Upload failed after 3 attempts');
      }

      var docId = uploadResult['document_id'];
      debugPrint('Document uploaded, ID: $docId');

      // Now analyze the document
      final analyzeRes = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/documents/analyze/$docId'),
            headers: {'Content-Type': 'application/json', ...headers},
          )
          .timeout(const Duration(seconds: 120)); // Analysis can take longer

      final analysis = jsonDecode(analyzeRes.body);

      setState(() => _analyzing = false);

      if (analysis['status'] == 'success') {
        _showSnack('Document analyzed successfully!', isError: false);
        _loadDocuments();
      } else {
        _showSnack('Analysis: ${analysis['message']}', isError: true);
      }
    } catch (e) {
      debugPrint('Full error: $e');
      setState(() => _analyzing = false);
      _showSnack('Upload failed: $e', isError: true);
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
