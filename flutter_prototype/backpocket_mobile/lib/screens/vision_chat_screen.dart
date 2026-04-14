import 'dart:convert';
import 'dart:io';
import 'dart:ui';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';

// ─── Warehouse Sunrise palette (matches main.dart) ────────────────────────────
const Color _kBg = Color(0xFF121212);
const Color _kSurface = Color(0xFF1E1E1E);
const Color _kCard = Color(0xFF252525);
const Color _kBorder = Color(0x20FFFFFF);
const Color _kPrimary = Color(0xFFFFB300); // amber/gold
const Color _kOrange = Color(0xFFF97316);
const Color _kRed = Color(0xFFEF4444);
const Color _kGreen = Color(0xFF22C55E);
const Color _kDim = Color(0x99FFFFFF);
const Color _kMuted = Color(0x44FFFFFF);

// ─────────────────────────────────────────────────────────────────────────────
/// Entry point — picks the right initial state based on camera availability.
/// Call this directly: `Navigator.push(..., VisionChatScreen(...))`
// ─────────────────────────────────────────────────────────────────────────────
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

// ─── Screen phases ────────────────────────────────────────────────────────────
enum _Phase { camera, processing, chat }

// ─── A single chat message in the analysis conversation ──────────────────────
class _Message {
  final String role; // 'system' | 'user' | 'assistant'
  final String content;
  const _Message(this.role, this.content);
}

// ─────────────────────────────────────────────────────────────────────────────
class _VisionChatScreenState extends State<VisionChatScreen>
    with WidgetsBindingObserver {
  // Camera
  List<CameraDescription> _cameras = [];
  CameraController? _cameraCtrl;
  bool _cameraReady = false;

  // Processing
  _Phase _phase = _Phase.camera;
  double _uploadProgress = 0; // 0.0 → 1.0
  String _processingLabel = 'Initialising...';

  // Chat
  int? _documentId;
  String _docContext = ''; // raw analysis text stored for Twin forwarding
  final List<_Message> _messages = [];
  final TextEditingController _chatCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  bool _chatSending = false;

  // No additional local state needed for invoice pre-fill (data extracted on demand)

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final ctrl = _cameraCtrl;
    if (ctrl == null || !ctrl.value.isInitialized) return;
    if (state == AppLifecycleState.inactive) {
      ctrl.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initCamera();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cameraCtrl?.dispose();
    _chatCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  // ─── Camera init ───────────────────────────────────────────────────────────
  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isEmpty) {
        _showSnack('No camera found on this device.', error: true);
        return;
      }
      final ctrl = CameraController(
        _cameras.first,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );
      await ctrl.initialize();
      if (!mounted) return;
      setState(() {
        _cameraCtrl = ctrl;
        _cameraReady = true;
      });
    } catch (e) {
      if (mounted) _showSnack('Camera error: $e', error: true);
    }
  }

  // ─── Capture (camera) or pick from gallery ─────────────────────────────────
  Future<void> _capturePhoto() async {
    if (_cameraCtrl == null || !_cameraCtrl!.value.isInitialized) return;
    try {
      final xfile = await _cameraCtrl!.takePicture();
      await _processFile(File(xfile.path));
    } catch (e) {
      _showSnack('Capture failed: $e', error: true);
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final picker = ImagePicker();
      final xfile = await picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 90,
      );
      if (xfile == null) return;
      await _processFile(File(xfile.path));
    } catch (e) {
      _showSnack('Gallery error: $e', error: true);
    }
  }

  // ─── Upload → Analyse pipeline ─────────────────────────────────────────────
  Future<void> _processFile(File file) async {
    setState(() {
      _phase = _Phase.processing;
      _uploadProgress = 0;
      _processingLabel = 'Uploading document...';
    });

    final headers = <String, String>{
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    // 1. Upload
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

      // Simulate progress since MultipartRequest doesn't expose byte-level progress
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
      setState(() => _phase = _Phase.camera);
      _showSnack('Upload error: $e', error: true);
      return;
    }

    // 2. Analyse
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

      // Short pause so the bar visually completes
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
      setState(() => _phase = _Phase.camera);
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

  // ─── Action chip handlers ─────────────────────────────────────────────────

  Future<void> _extractAbn() async {
    if (_documentId == null) return;
    setState(() => _chatSending = true);
    _messages.add(const _Message('user', '📄 Extract ABN'));
    _scrollToBottom();

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/documents/analyze/$_documentId'),
            headers: {
              'Content-Type': 'application/json',
              if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
            },
            body: jsonEncode({'prompt': 'Extract ABN'}),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final result =
          (data['analysis'] as String?) ??
          (data['result'] as String?) ??
          (data['message'] as String?) ??
          'Could not extract ABN.';
      setState(() => _messages.add(_Message('assistant', result)));
    } catch (e) {
      setState(
        () => _messages.add(_Message('assistant', 'ABN extraction error: $e')),
      );
    } finally {
      setState(() => _chatSending = false);
      _scrollToBottom();
    }
  }

  void _draftInvoice() {
    // Parse extracted data for pre-fill hints
    final abn = _tryExtract(r'ABN[:\s]+(\d[\d\s]+\d)', _docContext);
    final name = _tryExtract(
      r'(?:Name|Client)[:\s]+([A-Za-z\s]+)',
      _docContext,
    );
    final amount = _tryExtract(r'\$\s*([\d,]+(?:\.\d{2})?)', _docContext);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: _kSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => _InvoicePreFillSheet(
        abn: abn,
        clientName: name,
        amount: amount,
        docContext: _docContext,
        serverUrl: widget.serverUrl,
        apiKey: widget.apiKey,
      ),
    );
  }

  Future<void> _askTwin() async {
    setState(() => _chatSending = true);
    _messages.add(const _Message('user', '🧠 Ask Pip about this document'));
    _scrollToBottom();

    try {
      final prompt =
          'I have just scanned a document. Here is the AI analysis:\n\n'
          '$_docContext\n\n'
          'What should I do next regarding this document?';

      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/chat'),
            headers: {
              'Content-Type': 'application/json',
              if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
            },
            body: jsonEncode({'message': prompt}),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final reply = data['response'] as String? ?? 'No response from Pip.';
      setState(() => _messages.add(_Message('assistant', reply)));
    } catch (e) {
      setState(() => _messages.add(_Message('assistant', 'Pip error: $e')));
    } finally {
      setState(() => _chatSending = false);
      _scrollToBottom();
    }
  }

  Future<void> _sendChatMessage() async {
    final text = _chatCtrl.text.trim();
    if (text.isEmpty || _chatSending) return;
    _chatCtrl.clear();
    setState(() {
      _messages.add(_Message('user', text));
      _chatSending = true;
    });
    _scrollToBottom();

    try {
      final prompt =
          'Regarding the document I scanned:\n\n'
          'Document context:\n$_docContext\n\n'
          'User question: $text';

      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/documents/analyze/$_documentId'),
            headers: {
              'Content-Type': 'application/json',
              if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
            },
            body: jsonEncode({'prompt': prompt}),
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
      // Fall back to twin chat
      try {
        final res = await http
            .post(
              Uri.parse('${widget.serverUrl}/api/mobile/chat'),
              headers: {
                'Content-Type': 'application/json',
                if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
              },
              body: jsonEncode({
                'message': 'Document context: $_docContext\n\nQuestion: $text',
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

  // ─── Helpers ──────────────────────────────────────────────────────────────

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

  // ─── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kBg,
      appBar: _buildAppBar(),
      body: switch (_phase) {
        _Phase.camera => _buildCameraView(),
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
            _phase == _Phase.camera
                ? Icons.camera_alt_outlined
                : _phase == _Phase.processing
                ? Icons.hourglass_top_rounded
                : Icons.chat_bubble_outline_rounded,
            color: _kPrimary,
            size: 18,
          ),
          const SizedBox(width: 8),
          Text(
            _phase == _Phase.camera
                ? 'Scan Document'
                : _phase == _Phase.processing
                ? 'Processing'
                : 'Document Analysis',
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
              _phase = _Phase.camera;
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

  // ─── Phase 1: Camera ──────────────────────────────────────────────────────
  Widget _buildCameraView() {
    return Stack(
      fit: StackFit.expand,
      children: [
        // Camera preview or placeholder
        if (_cameraReady && _cameraCtrl != null)
          CameraPreview(_cameraCtrl!)
        else
          Container(
            color: _kBg,
            child: const Center(
              child: CircularProgressIndicator(color: _kPrimary),
            ),
          ),

        // Viewfinder overlay
        if (_cameraReady) CustomPaint(painter: _ViewfinderPainter()),

        // Bottom controls
        Positioned(left: 0, right: 0, bottom: 0, child: _buildCameraControls()),
      ],
    );
  }

  Widget _buildCameraControls() {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          color: Colors.black.withAlpha(153),
          padding: const EdgeInsets.fromLTRB(32, 20, 32, 40),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              // Gallery picker
              _circleBtn(
                icon: Icons.photo_library_outlined,
                label: 'Gallery',
                onTap: _pickFromGallery,
                size: 52,
              ),

              // Shutter
              GestureDetector(
                onTap: _cameraReady ? _capturePhoto : null,
                child: Container(
                  width: 76,
                  height: 76,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: _kPrimary, width: 3),
                    color: Colors.transparent,
                  ),
                  child: Center(
                    child: Container(
                      width: 58,
                      height: 58,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white,
                      ),
                    ),
                  ),
                ),
              ),

              // Flip camera
              _circleBtn(
                icon: Icons.flip_camera_ios_outlined,
                label: 'Flip',
                size: 52,
                onTap: _cameras.length > 1
                    ? () async {
                        final current = _cameras.indexOf(
                          _cameraCtrl!.description,
                        );
                        final next = _cameras[(current + 1) % _cameras.length];
                        await _cameraCtrl?.dispose();
                        final ctrl = CameraController(
                          next,
                          ResolutionPreset.high,
                          enableAudio: false,
                        );
                        await ctrl.initialize();
                        if (mounted) setState(() => _cameraCtrl = ctrl);
                      }
                    : null,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _circleBtn({
    required IconData icon,
    required String label,
    required VoidCallback? onTap,
    double size = 48,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: size,
            height: size,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: Colors.white.withAlpha(26),
              border: Border.all(color: Colors.white.withAlpha(51)),
            ),
            child: Icon(icon, color: Colors.white, size: size * 0.42),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(color: _kDim, fontSize: 11)),
        ],
      ),
    );
  }

  // ─── Phase 2: Processing ──────────────────────────────────────────────────
  Widget _buildProcessingOverlay() {
    return Container(
      color: _kBg,
      child: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Animated document icon
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

              // Label
              Text(
                _processingLabel,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 20),

              // Warehouse sunrise progress bar
              _WarehouseProgressBar(progress: _uploadProgress),
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

  // ─── Phase 3: Chat ────────────────────────────────────────────────────────
  Widget _buildChatView() {
    return Column(
      children: [
        // Message list
        Expanded(
          child: ListView.builder(
            controller: _scrollCtrl,
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            itemCount: _messages.length,
            itemBuilder: (_, i) => _GlassBubble(msg: _messages[i]),
          ),
        ),

        // Typing indicator
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

        // Action chips
        _buildActionChips(),

        // Text input bar
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
            label: '📄 Extract ABN',
            onTap: _chatSending ? null : _extractAbn,
          ),
          const SizedBox(width: 8),
          _ActionChip(
            label: '💰 Draft Invoice',
            onTap: _chatSending ? null : _draftInvoice,
          ),
          const SizedBox(width: 8),
          _ActionChip(
            label: '🧠 Ask Pip',
            onTap: _chatSending ? null : _askTwin,
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
                enabledBorder: OutlineInputBorder(
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

// ─── Glassmorphism chat bubble ────────────────────────────────────────────────
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
            // Avatar
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

          // Glass bubble
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

// ─── Action chip widget ───────────────────────────────────────────────────────
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

// ─── Warehouse Sunrise progress bar ──────────────────────────────────────────
class _WarehouseProgressBar extends StatelessWidget {
  final double progress; // 0.0 → 1.0

  const _WarehouseProgressBar({required this.progress});

  @override
  Widget build(BuildContext context) {
    return Container(
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
                width: constraints.maxWidth * progress.clamp(0.0, 1.0),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFF6B00), _kPrimary, Color(0xFFFFE066)],
                  ),
                  borderRadius: BorderRadius.circular(3),
                  boxShadow: [
                    BoxShadow(
                      color: _kPrimary.withAlpha(128),
                      blurRadius: 6,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ─── Camera viewfinder overlay ────────────────────────────────────────────────
class _ViewfinderPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFFFFB300)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    const margin = 48.0;
    const corner = 24.0;
    final rect = Rect.fromLTRB(
      margin,
      margin * 2,
      size.width - margin,
      size.height - margin * 2,
    );

    // Draw corner brackets only
    final corners = [
      // TL
      [
        Offset(rect.left, rect.top + corner),
        Offset(rect.left, rect.top),
        Offset(rect.left + corner, rect.top),
      ],
      // TR
      [
        Offset(rect.right - corner, rect.top),
        Offset(rect.right, rect.top),
        Offset(rect.right, rect.top + corner),
      ],
      // BR
      [
        Offset(rect.right, rect.bottom - corner),
        Offset(rect.right, rect.bottom),
        Offset(rect.right - corner, rect.bottom),
      ],
      // BL
      [
        Offset(rect.left + corner, rect.bottom),
        Offset(rect.left, rect.bottom),
        Offset(rect.left, rect.bottom - corner),
      ],
    ];

    for (final pts in corners) {
      final path = Path()
        ..moveTo(pts[0].dx, pts[0].dy)
        ..lineTo(pts[1].dx, pts[1].dy)
        ..lineTo(pts[2].dx, pts[2].dy);
      canvas.drawPath(path, paint);
    }

    // Subtle centre cross
    final crossPaint = Paint()
      ..color = const Color(0x33FFB300)
      ..strokeWidth = 1;
    final cx = size.width / 2;
    final cy = size.height / 2;
    canvas.drawLine(Offset(cx - 12, cy), Offset(cx + 12, cy), crossPaint);
    canvas.drawLine(Offset(cx, cy - 12), Offset(cx, cy + 12), crossPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

// ─── Invoice pre-fill bottom sheet ───────────────────────────────────────────
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
              'client_abn': _abnCtrl.text.trim(),
              'amount':
                  double.tryParse(
                    _amountCtrl.text.replaceAll(',', '').trim(),
                  ) ??
                  0,
              'description': _descCtrl.text.trim(),
              'gst_inclusive': true,
            }),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            data['message'] ?? data['invoice_path'] ?? 'Invoice generated!',
          ),
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
                'Draft Invoice',
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
            'Pre-filled from document scan',
            style: TextStyle(color: _kDim, fontSize: 12),
          ),
          const SizedBox(height: 20),
          _field(_nameCtrl, 'Client Name'),
          const SizedBox(height: 12),
          _field(_abnCtrl, 'Client ABN'),
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
