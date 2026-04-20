import 'dart:convert';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import '../theme.dart';

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
  bool _uploading = false;
  bool _paperlessActive = false;
  String _paperlessUiUrl = '';
  String _searchQuery = '';
  final TextEditingController _searchCtrl = TextEditingController();

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
      };

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadDocuments({String query = ''}) async {
    setState(() => _loading = true);
    try {
      final uri = Uri.parse('${widget.serverUrl}/api/documents').replace(
        queryParameters: {
          if (query.isNotEmpty) 'query': query,
        },
      );
      final res = await http.get(uri, headers: _headers);
      final body = jsonDecode(res.body) as Map<String, dynamic>;
      final docs = (body['documents'] as List?) ?? [];
      setState(() {
        _documents = docs;
        _paperlessActive = body['storage'] == 'paperless';
        _paperlessUiUrl = body['paperless_ui'] as String? ?? '';
      });
    } catch (e) {
      debugPrint('Load docs error: $e');
    }
    setState(() => _loading = false);
  }

  Future<void> _uploadAndAnalyze() async {
    final picker = ImagePicker();
    final source = await _pickSource();
    if (source == null) return;

    final xfile = await picker.pickImage(source: source, imageQuality: 85);
    if (xfile == null) return;

    setState(() => _uploading = true);

    try {
      final bytes = await xfile.readAsBytes();
      final filename = xfile.name.isNotEmpty ? xfile.name : 'document.jpg';
      final category = await _pickCategory();

      final base64File = base64Encode(bytes);
      Map<String, dynamic>? result;
      String lastErr = 'Upload failed';

      for (var attempt = 1; attempt <= 3; attempt++) {
        try {
          final res = await http
              .post(
                Uri.parse('${widget.serverUrl}/api/documents/upload'),
                headers: _headers,
                body: jsonEncode({
                  'file': base64File,
                  'filename': filename,
                  'category': category,
                }),
              )
              .timeout(const Duration(seconds: 60));
          if (res.statusCode == 200) {
            result = jsonDecode(res.body) as Map<String, dynamic>;
            if (result['status'] == 'success') break;
            lastErr = result['message'] ?? 'Upload failed';
          } else {
            lastErr = 'HTTP ${res.statusCode}';
          }
        } catch (e) {
          lastErr = e.toString();
          if (attempt < 3) await Future.delayed(Duration(milliseconds: 500 * attempt));
        }
      }

      setState(() => _uploading = false);

      if (result == null || result['status'] != 'success') {
        _showSnack('Upload failed: $lastErr', isError: true);
        return;
      }

      final storage = result['storage'] ?? 'local';
      if (storage == 'paperless') {
        _showSnack('Uploaded to Paperless — OCR queued', isError: false);
        await Future.delayed(const Duration(seconds: 3));
      } else {
        // Local storage: trigger AI analysis
        final docId = result['document_id'];
        if (docId != null) {
          await http
              .post(
                Uri.parse('${widget.serverUrl}/api/documents/analyze/$docId'),
                headers: _headers,
              )
              .timeout(const Duration(seconds: 120));
        }
        _showSnack('Document saved & analysed', isError: false);
      }
      _loadDocuments(query: _searchQuery);
    } catch (e) {
      setState(() => _uploading = false);
      _showSnack('Error: $e', isError: true);
    }
  }

  Future<ImageSource?> _pickSource() => showModalBottomSheet<ImageSource>(
        context: context,
        backgroundColor: AppColors.card,
        shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        builder: (_) => Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Select Source',
                  style: TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              if (!kIsWeb)
                ListTile(
                  leading: const Icon(Icons.camera_alt, color: AppColors.amber),
                  title: const Text('Camera',
                      style: TextStyle(color: Colors.white)),
                  onTap: () => Navigator.pop(context, ImageSource.camera),
                ),
              ListTile(
                leading:
                    const Icon(Icons.photo_library, color: AppColors.amber),
                title: const Text('Gallery',
                    style: TextStyle(color: Colors.white)),
                onTap: () => Navigator.pop(context, ImageSource.gallery),
              ),
            ],
          ),
        ),
      );

  Future<String> _pickCategory() async {
    const cats = <(String, IconData, String)>[
      ('invoice', Icons.receipt, 'Invoice'),
      ('receipt', Icons.receipt_long, 'Receipt'),
      ('quote', Icons.request_quote, 'Quote'),
      ('contract', Icons.assignment, 'Contract'),
      ('permit', Icons.verified, 'Permit'),
      ('photo', Icons.photo, 'Photo'),
      ('other', Icons.folder, 'Other'),
    ];
    final picked = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: AppColors.card,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Document Type',
                style: TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: cats
                  .map((c) => ActionChip(
                        avatar: Icon(c.$2, color: AppColors.amber, size: 16),
                        label: Text(c.$3,
                            style: const TextStyle(color: Colors.white)),
                        backgroundColor: AppColors.surface,
                        side: const BorderSide(color: AppColors.border),
                        onPressed: () => Navigator.pop(context, c.$1),
                      ))
                  .toList(),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
    return picked ?? 'other';
  }

  void _showSnack(String msg, {bool isError = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: isError ? AppColors.red : AppColors.green,
      behavior: SnackBarBehavior.floating,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.surface,
      child: Column(
        children: [
          // ── Header bar ──────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    decoration: InputDecoration(
                      hintText: 'Search documents…',
                      hintStyle:
                          const TextStyle(color: AppColors.textMuted, fontSize: 14),
                      prefixIcon: const Icon(Icons.search,
                          color: AppColors.textMuted, size: 18),
                      suffixIcon: _searchQuery.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear,
                                  color: AppColors.textMuted, size: 16),
                              onPressed: () {
                                _searchCtrl.clear();
                                setState(() => _searchQuery = '');
                                _loadDocuments();
                              },
                            )
                          : null,
                      filled: true,
                      fillColor: AppColors.card,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding:
                          const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                    ),
                    onSubmitted: (v) {
                      setState(() => _searchQuery = v);
                      _loadDocuments(query: v);
                    },
                  ),
                ),
                const SizedBox(width: 10),
                _buildUploadButton(),
              ],
            ),
          ),

          // ── Paperless badge ─────────────────────────────────────────────
          if (_paperlessActive)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
              child: Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.green.withAlpha(26),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.green.withAlpha(77)),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.check_circle,
                            color: AppColors.green, size: 12),
                        SizedBox(width: 4),
                        Text('Paperless-ngx',
                            style: TextStyle(
                                color: AppColors.green,
                                fontSize: 11,
                                fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                  const Spacer(),
                  if (_paperlessUiUrl.isNotEmpty)
                    TextButton.icon(
                      icon: const Icon(Icons.open_in_new,
                          color: AppColors.amber, size: 12),
                      label: const Text('Open Paperless',
                          style:
                              TextStyle(color: AppColors.amber, fontSize: 12)),
                      onPressed: () => _showSnack(
                          'Open $_paperlessUiUrl in browser'),
                    ),
                ],
              ),
            ),

          const SizedBox(height: 8),

          // ── Document list ───────────────────────────────────────────────
          Expanded(
            child: _loading
                ? const Center(
                    child: CircularProgressIndicator(color: AppColors.amber))
                : _documents.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        color: AppColors.amber,
                        onRefresh: () =>
                            _loadDocuments(query: _searchQuery),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _documents.length,
                          itemBuilder: (context, i) {
                            final doc = _documents[i]
                                as Map<String, dynamic>;
                            return _paperlessActive
                                ? _PaperlessDocCard(
                                    doc: doc,
                                    serverUrl: widget.serverUrl,
                                    headers: _headers,
                                  )
                                : _LocalDocCard(doc: doc);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildUploadButton() {
    return GestureDetector(
      onTap: _uploading ? null : _uploadAndAnalyze,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          gradient: _uploading
              ? null
              : const LinearGradient(
                  colors: [AppColors.orange, Color(0xFFEA580C)]),
          color: _uploading ? AppColors.card : null,
          borderRadius: BorderRadius.circular(12),
        ),
        child: _uploading
            ? const Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                      color: AppColors.amber, strokeWidth: 2),
                ),
              )
            : const Icon(Icons.add_a_photo, color: Colors.white, size: 22),
      ),
    );
  }

  Widget _buildEmptyState() => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.folder_open,
                color: AppColors.textMuted.withAlpha(128), size: 56),
            const SizedBox(height: 12),
            const Text('No documents yet',
                style:
                    TextStyle(color: AppColors.textDim, fontSize: 16)),
            const SizedBox(height: 4),
            Text(
              _paperlessActive
                  ? 'Tap + to snap or upload — OCR is automatic'
                  : 'Tap + to upload & analyse with AI',
              style:
                  const TextStyle(color: AppColors.textMuted, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
}

// ── Paperless document card ────────────────────────────────────────────────

class _PaperlessDocCard extends StatelessWidget {
  final Map<String, dynamic> doc;
  final String serverUrl;
  final Map<String, String> headers;

  const _PaperlessDocCard({
    required this.doc,
    required this.serverUrl,
    required this.headers,
  });

  @override
  Widget build(BuildContext context) {
    final title = doc['title'] as String? ?? 'Untitled';
    final created = (doc['created'] as String? ?? '').split('T').first;
    final correspondent = doc['correspondent'];
    final docType = doc['document_type'];
    final tags = (doc['tags'] as List?) ?? [];
    final ocrPreview = doc['content'] as String? ?? '';
    final thumbnailUrl = doc['thumbnail_url'] as String?;
    final downloadUrl = doc['download_url'] as String?;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Thumbnail + meta ─────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Thumbnail
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: thumbnailUrl != null
                      ? Image.network(
                          '$serverUrl$thumbnailUrl',
                          headers: headers,
                          width: 56,
                          height: 56,
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) => _docIcon(),
                        )
                      : _docIcon(),
                ),
                const SizedBox(width: 12),
                // Title / date / type
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w600,
                            fontSize: 14),
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          if (created.isNotEmpty)
                            Text(created,
                                style: const TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 11)),
                          if (docType != null) ...[
                            const Text('  ·  ',
                                style: TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 11)),
                            Text(docType.toString(),
                                style: const TextStyle(
                                    color: AppColors.amber, fontSize: 11)),
                          ],
                        ],
                      ),
                      if (correspondent != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 3),
                          child: Text(
                            correspondent.toString(),
                            style: const TextStyle(
                                color: AppColors.textDim, fontSize: 12),
                          ),
                        ),
                    ],
                  ),
                ),
                // Download / PDF button
                if (downloadUrl != null)
                  IconButton(
                    icon: const Icon(Icons.picture_as_pdf,
                        color: AppColors.orange, size: 20),
                    tooltip: 'Download PDF',
                    onPressed: () {
                      // Opens the proxied PDF download URL
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                        content: Text(
                            'PDF: $serverUrl$downloadUrl',
                            overflow: TextOverflow.ellipsis),
                        behavior: SnackBarBehavior.floating,
                        backgroundColor: AppColors.card,
                        duration: const Duration(seconds: 4),
                        action: SnackBarAction(
                          label: 'OK',
                          textColor: AppColors.amber,
                          onPressed: () {},
                        ),
                      ));
                    },
                  ),
              ],
            ),
          ),

          // ── OCR preview ──────────────────────────────────────────────
          if (ocrPreview.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  ocrPreview,
                  style: const TextStyle(
                      color: AppColors.textDim,
                      fontSize: 11,
                      height: 1.5),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),

          // ── Tags ─────────────────────────────────────────────────────
          if (tags.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: Wrap(
                spacing: 6,
                runSpacing: 4,
                children: tags
                    .map((t) => Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.amber.withAlpha(20),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                                color: AppColors.amber.withAlpha(51)),
                          ),
                          child: Text(
                            t.toString(),
                            style: const TextStyle(
                                color: AppColors.amber,
                                fontSize: 10,
                                fontWeight: FontWeight.w500),
                          ),
                        ))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _docIcon() => Container(
        width: 56,
        height: 56,
        decoration: BoxDecoration(
          color: AppColors.amber.withAlpha(26),
          borderRadius: BorderRadius.circular(8),
        ),
        child: const Icon(Icons.description, color: AppColors.amber, size: 28),
      );
}

// ── Local (non-Paperless) document card ────────────────────────────────────

class _LocalDocCard extends StatelessWidget {
  final Map<String, dynamic> doc;
  const _LocalDocCard({required this.doc});

  @override
  Widget build(BuildContext context) {
    final hasAnalysis =
        (doc['ai_analysis'] as String? ?? '').isNotEmpty;
    final status = doc['status'] as String? ?? 'pending';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.amber.withAlpha(26),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.description,
                    color: AppColors.amber, size: 20),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      doc['original_name'] as String? ??
                          doc['filename'] as String? ??
                          'Document',
                      style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w600),
                    ),
                    Text(
                      (doc['created_at']?.toString() ?? '')
                          .split('.')
                          .first,
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 11),
                    ),
                  ],
                ),
              ),
              _StatusBadge(hasAnalysis: hasAnalysis, status: status),
            ],
          ),
          if (hasAnalysis) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                doc['ai_analysis'] as String,
                style: const TextStyle(
                    color: AppColors.textDim,
                    fontSize: 12,
                    height: 1.5),
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

class _StatusBadge extends StatelessWidget {
  final bool hasAnalysis;
  final String status;
  const _StatusBadge({required this.hasAnalysis, required this.status});

  @override
  Widget build(BuildContext context) {
    final Color color = hasAnalysis
        ? AppColors.green
        : (status == 'analyzing' ? AppColors.amber : AppColors.textMuted);
    final String label = hasAnalysis
        ? 'Analysed'
        : (status == 'analyzing' ? 'Analysing…' : 'Pending');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withAlpha(102)),
      ),
      child: Text(label,
          style: TextStyle(
              color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}
