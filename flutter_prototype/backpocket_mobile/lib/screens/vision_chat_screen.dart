import 'dart:convert';
import 'dart:io';
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

const Color _kBg = Color(0xFF121212);
const Color _kSurface = Color(0xFF1E1E1E);
const Color _kCard = Color(0xFF252525);
const Color _kBorder = Color(0x20FFFFFF);
const Color _kPrimary = Color(0xFFFFB300); 
const Color _kOrange = Color(0xFFF97316);
const Color _kRed = Color(0xFFEF4444);
const Color _kGreen = Color(0xFF22C55E);
const Color _kDim = Color(0xFFD4C4B4);
const Color _kMuted = Color(0xFF9E8E7E);

class VisionChatScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const VisionChatScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<VisionChatScreen> createState() => _VisionChatScreenState();
}

enum _Phase { picker, processing, chat }

class _Message {
  final String role;
  final String content;
  const _Message(this.role, this.content);
}

class _VisionChatScreenState extends State<VisionChatScreen> {
  _Phase _phase = _Phase.picker;
  double _uploadProgress = 0; 
  String _processingLabel = 'Initialising...';

  int? _documentId;
  String _docContext = ''; 
  final List<_Message> _messages = [];
  final TextEditingController _chatCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  bool _chatSending = false;

  @override
  void dispose() {
    _chatCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final picker = ImagePicker();
      final xfile = await picker.pickImage(
        source: source,
        imageQuality: 90,
      );
      if (xfile == null) return;
      await _processFile(File(xfile.path));
    } catch (e) {
      _showSnack('Image error: $e', error: true);
    }
  }

  Future<void> _processFile(File file) async {
    setState(() {
      _phase = _Phase.processing;
      _uploadProgress = 0;
      _processingLabel = 'Uploading document...';
    });

    final headers = <String, String>{
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    int? docId;
    try {
      final uri = Uri.parse('${widget.serverUrl}/api/documents/upload');
      final req = http.MultipartRequest('POST', uri)
        ..headers.addAll(headers)
        ..fields['category'] = 'vision'
        ..files.add(
          await http.MultipartFile.fromPath(
            'file',
            file.path,
            filename: 'capture_${DateTime.now().millisecondsSinceEpoch}.jpg',
          ),
        );

      _animateProgress(0, 0.6, const Duration(milliseconds: 800));

      final streamed = await req.send().timeout(const Duration(seconds: 30));
      final body = await streamed.stream.bytesToString();

      if (streamed.statusCode != 200) {
        throw Exception('Upload failed (${streamed.statusCode}): $body');
      }

      final data = jsonDecode(body) as Map<String, dynamic>;
      if (data['status'] != 'success') {
        throw Exception(data['message'] ?? 'Upload returned non-success');
      }

      docId = data['document_id'] as int?;
      _documentId = docId;
      setState(() => _processingLabel = 'Analysing with AI...');
      _animateProgress(0.6, 0.9, const Duration(milliseconds: 600));
    } catch (e) {
      setState(() => _phase = _Phase.picker);
      _showSnack('Upload error: $e', error: true);
      return;
    }

    try {
      final analysisUri = Uri.parse(
        '${widget.serverUrl}/api/documents/analyze/$docId',
      );
      final res = await http
          .post(
            analysisUri,
            headers: {'Content-Type': 'application/json', ...headers},
            body: jsonEncode({'prompt': 'Describe this document in detail.'}),
          )
          .timeout(const Duration(seconds: 60));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final analysis =
          (data['analysis'] as String?) ??
          (data['result'] as String?) ??
          (data['message'] as String?) ??
          'Analysis complete.';

      _animateProgress(0.9, 1.0, const Duration(milliseconds: 300));
      await Future<void>.delayed(const Duration(milliseconds: 400));

      _docContext = analysis;
      setState(() {
        _phase = _Phase.chat;
        _messages.add(
          _Message('assistant', '📄 **Document analysed**\n\n$analysis'),
        );
      });
      _scrollToBottom();
    } catch (e) {
      setState(() => _phase = _Phase.picker);
      _showSnack('Analysis error: $e', error: true);
    }
  }

  void _animateProgress(double from, double to, Duration duration) {
    final steps = 20;
    final stepDuration = duration ~/ steps;
    final increment = (to - from) / steps;
    int step = 0;
    Future.doWhile(() async {
      await Future<void>.delayed(stepDuration);
      if (!mounted) return false;
      setState(() => _uploadProgress = from + increment * step);
      step++;
      return step <= steps;
    });
  }

  void _extractAbn() {
    final extracted = _tryExtract(r'ABN[:\s]*([\d\s]{11,14})', _docContext);
    if (extracted != null) {
      setState(() {
        _messages.add(_Message('user', 'Extract ABN'));
        _messages.add(_Message('assistant', 'Found ABN: **$extracted**'));
      });
      _scrollToBottom();
    } else {
      _showSnack('No ABN found in document');
    }
  }

  void _draftInvoice() {
    final name = _tryExtract(r'Name[:\s]*([A-Za-z\s]+)\n', _docContext) ?? 'Client';
    final abn = _tryExtract(r'ABN[:\s]*([\d\s]{11,14})', _docContext) ?? '';
    final amount = _tryExtract(r'Total[:\s\$]*([\d\.\,]+)', _docContext) ?? '0.00';

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: _kSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => _InvoicePreFillSheet(
        clientName: name,
        abn: abn,
        amount: amount,
        docContext: _docContext,
        serverUrl: widget.serverUrl,
        apiKey: widget.apiKey,
      ),
    );
  }

  Future<void> _askTwin() async {
    setState(() {
      _messages.add(_Message('user', 'Ask Pip to review'));
      _chatSending = true;
    });
    _scrollToBottom();
    _sendChatMessage(text: 'Review this document analysis and provide advice: \n\n$_docContext');
  }

  Future<void> _sendChatMessage({String? text}) async {
    final msg = text ?? _chatCtrl.text.trim();
    if (msg.isEmpty) return;

    if (text == null) {
      setState(() {
        _messages.add(_Message('user', msg));
        _chatSending = true;
      });
      _chatCtrl.clear();
      _scrollToBottom();
    }

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/documents/chat/$_documentId'),
            headers: {
              'Content-Type': 'application/json',
              if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
            },
            body: jsonEncode({'message': msg}),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final reply =
          (data['analysis'] as String?) ??
          (data['result'] as String?) ??
          (data['message'] as String?) ??
          'No response.';
      setState(() => _messages.add(_Message('assistant', reply)));
    } catch (e) {
      try {
        final res = await http
            .post(
              Uri.parse('${widget.serverUrl}/api/mobile/chat'),
              headers: {
                'Content-Type': 'application/json',
                if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
              },
              body: jsonEncode({
                'message': 'Document context: $_docContext\n\nQuestion: $msg',
              }),
            )
            .timeout(const Duration(seconds: 30));
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        final reply = data['response'] as String? ?? 'No response.';
        setState(() => _messages.add(_Message('assistant', reply)));
      } catch (e2) {
        setState(() => _messages.add(_Message('assistant', 'Error: $e2')));
      }
    } finally {
      setState(() => _chatSending = false);
      _scrollToBottom();
    }
  }

  String? _tryExtract(String pattern, String text) {
    final match = RegExp(pattern, caseSensitive: false).firstMatch(text);
    return match?.group(1)?.trim();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _showSnack(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? _kRed : _kGreen,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kBg,
      appBar: _buildAppBar(),
      body: switch (_phase) {
        _Phase.picker => _buildPickerView(),
        _Phase.processing => _buildProcessingOverlay(),
        _Phase.chat => _buildChatView(),
      },
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: _kSurface,
      elevation: 0,
      leading: IconButton(
        icon: const Icon(Icons.arrow_back_ios_new, color: _kPrimary, size: 18),
        onPressed: () => Navigator.pop(context),
      ),
      title: Row(
        children: [
          Icon(
            _phase == _Phase.picker
                ? Icons.document_scanner_outlined
                : _phase == _Phase.processing
                ? Icons.hourglass_top_rounded
                : Icons.chat_bubble_outline_rounded,
            color: _kPrimary,
            size: 18,
          ),
          const SizedBox(width: 8),
          Text(
            _phase == _Phase.picker
                ? 'Scan Receipt / Cost Estimate'
                : _phase == _Phase.processing
                ? 'Processing'
                : 'Vision Analysis',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        ],
      ),
      actions: [
        if (_phase == _Phase.chat)
          IconButton(
            tooltip: 'Scan another',
            icon: const Icon(Icons.camera_alt_outlined, color: _kMuted),
            onPressed: () => setState(() {
              _phase = _Phase.picker;
              _messages.clear();
              _documentId = null;
              _docContext = '';
            }),
          ),
      ],
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: const Color(0x20FFFFFF)),
      ),
    );
  }

  Widget _buildPickerView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.document_scanner, size: 80, color: _kMuted),
          const SizedBox(height: 24),
          const Text(
            'Scan a Document or Receipt',
            style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'Upload a photo for OCR or Cost Estimation.',
            style: TextStyle(color: _kDim, fontSize: 14),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 48),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _bigButton(
                icon: Icons.camera_alt,
                label: 'Camera',
                onTap: () => _pickImage(ImageSource.camera),
              ),
              const SizedBox(width: 24),
              _bigButton(
                icon: Icons.photo_library,
                label: 'Gallery',
                onTap: () => _pickImage(ImageSource.gallery),
              ),
            ],
          )
        ],
      ),
    );
  }

  Widget _bigButton({required IconData icon, required String label, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 120,
        height: 120,
        decoration: BoxDecoration(
          color: _kCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: _kBorder),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40, color: _kPrimary),
            const SizedBox(height: 12),
            Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }

  Widget _buildProcessingOverlay() {
    return Container(
      color: _kBg,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TweenAnimationBuilder<double>(
                tween: Tween(begin: 0.8, end: 1.0),
                duration: const Duration(milliseconds: 900),
                curve: Curves.easeInOut,
                builder: (_, scale, child) =>
                    Transform.scale(scale: scale, child: child),
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: _kPrimary.withAlpha(26),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: _kPrimary.withAlpha(102),
                      width: 1.5,
                    ),
                  ),
                  child: const Icon(
                    Icons.document_scanner_outlined,
                    color: _kPrimary,
                    size: 36,
                  ),
                ),
              ),
              const SizedBox(height: 28),
              Text(
                _processingLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 20),
              Container(
                height: 6,
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(20),
                  borderRadius: BorderRadius.circular(3),
                ),
                child: LayoutBuilder(
                  builder: (_, constraints) {
                    return Stack(
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: constraints.maxWidth * _uploadProgress.clamp(0.0, 1.0),
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFFFF6B00), _kPrimary, Color(0xFFFFE066)],
                            ),
                            borderRadius: BorderRadius.circular(3),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
              const SizedBox(height: 10),
              Text(
                '${(_uploadProgress * 100).round()}%',
                style: const TextStyle(color: _kDim, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChatView() {
    return Column(
      children: [
        Expanded(
          child: ListView.builder(
            controller: _scrollCtrl,
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            itemCount: _messages.length,
            itemBuilder: (_, i) => _GlassBubble(msg: _messages[i]),
          ),
        ),
        if (_chatSending)
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 20, vertical: 4),
            child: Row(
              children: [
                SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(
                    color: _kPrimary,
                    strokeWidth: 2,
                  ),
                ),
                SizedBox(width: 8),
                Text(
                  'Pip is thinking...',
                  style: TextStyle(color: _kDim, fontSize: 12),
                ),
              ],
            ),
          ),
        _buildActionChips(),
        _buildInputBar(),
      ],
    );
  }

  Widget _buildActionChips() {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          _ActionChip(
            label: '🧾 Extract Receipt Line Items',
            onTap: _chatSending ? null : () => _sendChatMessage(text: 'Extract the line items and total from this receipt so I can invoice it.'),
          ),
          const SizedBox(width: 8),
          _ActionChip(
            label: '🏗️ Cost Estimate',
            onTap: _chatSending ? null : () => _sendChatMessage(text: 'Provide a cost estimate for building what is shown in this document/plan.'),
          ),
          const SizedBox(width: 8),
          _ActionChip(
            label: '💰 Draft Voice Invoice',
            onTap: _chatSending ? null : _draftInvoice,
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      decoration: const BoxDecoration(
        color: _kSurface,
        border: Border(top: BorderSide(color: _kBorder)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _chatCtrl,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              maxLines: null,
              onSubmitted: (_) => _sendChatMessage(),
              decoration: InputDecoration(
                hintText: 'Ask about this document...',
                hintStyle: const TextStyle(color: _kMuted),
                filled: true,
                fillColor: _kCard,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: _kBorder),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: _kPrimary, width: 1.5),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          GestureDetector(
            onTap: _chatSending ? null : _sendChatMessage,
            child: Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                gradient: _chatSending
                    ? null
                    : const LinearGradient(
                        colors: [_kOrange, Color(0xFFEA580C)],
                      ),
                color: _chatSending ? _kCard : null,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(
                Icons.send_rounded,
                color: _chatSending ? _kMuted : Colors.white,
                size: 18,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GlassBubble extends StatelessWidget {
  final _Message msg;
  const _GlassBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isUser = msg.role == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [_kPrimary, _kOrange]),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Center(
                child: Icon(
                  Icons.document_scanner_outlined,
                  color: Colors.black,
                  size: 14,
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: ClipRRect(
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isUser ? 16 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 16),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: isUser
                        ? _kOrange.withAlpha(51)
                        : Colors.white.withAlpha(13),
                    border: Border.all(
                      color: isUser
                          ? _kOrange.withAlpha(76)
                          : Colors.white.withAlpha(26),
                    ),
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(isUser ? 16 : 4),
                      bottomRight: Radius.circular(isUser ? 4 : 16),
                    ),
                  ),
                  child: Text(
                    msg.content,
                    style: TextStyle(
                      color: isUser ? Colors.white : _kDim,
                      fontSize: 13,
                      height: 1.55,
                    ),
                  ),
                ),
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  final String label;
  final VoidCallback? onTap;

  const _ActionChip({required this.label, this.onTap});

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: enabled ? _kPrimary.withAlpha(26) : Colors.white.withAlpha(10),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: enabled
                ? _kPrimary.withAlpha(102)
                : Colors.white.withAlpha(20),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: enabled ? _kPrimary : _kMuted,
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class _InvoicePreFillSheet extends StatefulWidget {
  final String? abn;
  final String? clientName;
  final String? amount;
  final String docContext;
  final String serverUrl;
  final String apiKey;

  const _InvoicePreFillSheet({
    this.abn,
    this.clientName,
    this.amount,
    required this.docContext,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<_InvoicePreFillSheet> createState() => _InvoicePreFillSheetState();
}

class _InvoicePreFillSheetState extends State<_InvoicePreFillSheet> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _abnCtrl;
  late final TextEditingController _amountCtrl;
  late final TextEditingController _descCtrl;
  bool _generating = false;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.clientName ?? '');
    _abnCtrl = TextEditingController(text: widget.abn ?? '');
    _amountCtrl = TextEditingController(text: widget.amount ?? '');
    _descCtrl = TextEditingController(text: 'Professional services');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _abnCtrl.dispose();
    _amountCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _generate() async {
    setState(() => _generating = true);
    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/invoice/generate'),
            headers: {
              'Content-Type': 'application/json',
              if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
            },
            body: jsonEncode({
              'client_name': _nameCtrl.text.trim(),
              'client_email': _abnCtrl.text.trim(), // Use as email for now
              'items': [
                {'description': _descCtrl.text.trim(), 'qty': 1, 'rate': double.tryParse(_amountCtrl.text) ?? 0, 'gst': true}
              ],
              'notes': 'Generated via BackPocket Mobile OS',
            }),
          )
          .timeout(const Duration(seconds: 30));

      if (res.statusCode != 200) {
        throw Exception('Server error: ${res.statusCode}');
      }
      
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Invoice generated as PDF successfully!'),
          backgroundColor: _kGreen,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Invoice error: $e'),
            backgroundColor: _kRed,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
        left: 24,
        right: 24,
        top: 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.receipt_long_outlined,
                color: _kPrimary,
                size: 20,
              ),
              const SizedBox(width: 8),
              const Text(
                'Draft Voice Invoice',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const Spacer(),
              GestureDetector(
                onTap: () => Navigator.pop(context),
                child: const Icon(Icons.close, color: _kMuted, size: 20),
              ),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Pre-filled from document scan & OCR',
            style: TextStyle(color: _kDim, fontSize: 12),
          ),
          const SizedBox(height: 20),
          _field(_nameCtrl, 'Client Name'),
          const SizedBox(height: 12),
          _field(_abnCtrl, 'Client Email'),
          const SizedBox(height: 12),
          _field(
            _amountCtrl,
            'Amount (\$)',
            keyboardType: TextInputType.number,
          ),
          const SizedBox(height: 12),
          _field(_descCtrl, 'Description'),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: _kOrange,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onPressed: _generating ? null : _generate,
              icon: _generating
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(Icons.picture_as_pdf_outlined),
              label: Text(
                _generating ? 'Generating...' : 'Generate PDF Invoice',
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _field(
    TextEditingController ctrl,
    String label, {
    TextInputType? keyboardType,
  }) {
    return TextField(
      controller: ctrl,
      keyboardType: keyboardType,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: _kDim),
        filled: true,
        fillColor: _kCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: _kBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: _kBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: _kPrimary, width: 1.5),
        ),
      ),
    );
  }
}
