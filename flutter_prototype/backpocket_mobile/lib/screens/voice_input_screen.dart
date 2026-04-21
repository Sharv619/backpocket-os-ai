import 'dart:convert';
import 'dart:math';
// dart:io is stubbed on Flutter web — safe to import, guarded at runtime via kIsWeb
import 'dart:io'; // ignore: dart_io_import
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';

import '../theme.dart';
import '../services/voice_command_service.dart';
import '../models/voice_command_response.dart';

class VoiceInputScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  final String screenContext;

  const VoiceInputScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
    this.screenContext = 'dashboard',
  });

  @override
  State<VoiceInputScreen> createState() => _VoiceInputScreenState();
}

class _VoiceInputScreenState extends State<VoiceInputScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _waveController;
  late VoiceCommandService _voiceService;
  final TextEditingController _textController = TextEditingController();
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();

  bool _isRecording = false;
  bool _showTextInput = false;
  bool _isProcessing = false;
  bool _isRecorderInitialized = false;
  VoiceCommandResponse? _response;
  final List<_ConversationEntry> _conversation = [];
  String _lastTranscript = '';

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
    _voiceService = VoiceCommandService(
      baseUrl: widget.serverUrl,
      apiKey: widget.apiKey,
    );
    _voiceService.setScreenContext(widget.screenContext);
    _initRecorder();
  }

  Future<void> _initRecorder() async {
    if (!kIsWeb) {
      final status = await Permission.microphone.request();
      if (status != PermissionStatus.granted) {
        if (mounted) setState(() => _showTextInput = true);
        return;
      }
    }
    await _recorder.openRecorder();
    _isRecorderInitialized = true;
  }

  @override
  void dispose() {
    _waveController.dispose();
    _textController.dispose();
    if (_isRecorderInitialized) {
      _recorder.closeRecorder();
    }
    super.dispose();
  }

  Future<void> _handleTextSubmit(String text) async {
    if (text.isEmpty) return;

    setState(() {
      _lastTranscript = text;
      _conversation.add(_ConversationEntry(text: text, isUser: true));
    });
    _textController.clear();

    final response = await _voiceService.sendTranscript(text);
    if (response != null && mounted) {
      setState(() {
        _response = response;
        if (response.speechResponse.isNotEmpty) {
          _conversation.add(_ConversationEntry(
            text: response.speechResponse,
            isUser: false,
          ));
        }
      });
    }
  }

  Future<void> _handleConfirm(String answer) async {
    setState(() {
      _conversation.add(_ConversationEntry(text: answer, isUser: true));
    });

    final response = await _voiceService.sendConfirmation(answer);
    if (response != null && mounted) {
      setState(() {
        _response = response;
        if (response.speechResponse.isNotEmpty) {
          _conversation.add(_ConversationEntry(
            text: response.speechResponse,
            isUser: false,
          ));
        }
      });
    }
  }

  Future<void> _startRecording() async {
    if (!_isRecorderInitialized) {
      await _initRecorder();
      if (!_isRecorderInitialized) return;
    }

    if (kIsWeb) {
      // Web: path is ignored, returns blob URL
      await _recorder.startRecorder(toFile: 'voice_cmd.wav', codec: Codec.pcm16WAV);
    } else {
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/voice_cmd_${DateTime.now().millisecondsSinceEpoch}.m4a';
      await _recorder.startRecorder(toFile: path, codec: Codec.aacADTS);
    }
    if (mounted) setState(() => _isRecording = true);
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stopRecorder();
    if (mounted) setState(() { _isRecording = false; _isProcessing = true; });

    VoiceCommandResponse? response;

    if (kIsWeb) {
      // flutter_sound web: stop() returns a blob URL — fetch bytes then upload
      if (path != null && path.isNotEmpty) {
        try {
          final blobRes = await http.get(Uri.parse(path));
          response = await _voiceService.processAudioBytes(blobRes.bodyBytes, 'recording.wav');
        } catch (_) {}
      }
    } else {
      if (path == null) {
        if (mounted) setState(() => _isProcessing = false);
        return;
      }
      response = await _voiceService.processAudio(path);
      try { File(path).deleteSync(); } catch (_) {}
    }

    if (mounted) {
      setState(() {
        _isProcessing = false;
        if (response != null) {
          _response = response;
          final transcript = _voiceService.lastTranscript;
          if (transcript != null && transcript.isNotEmpty) {
            _lastTranscript = transcript;
            _conversation.add(_ConversationEntry(text: transcript, isUser: true));
          }
          if (response.speechResponse.isNotEmpty) {
            _conversation.add(_ConversationEntry(
              text: response.speechResponse,
              isUser: false,
            ));
          }
        }
      });
    }
  }

  Future<void> _showInvoiceSheet() async {
    if (_lastTranscript.isEmpty && _conversation.isEmpty) return;

    final transcript = _lastTranscript.isNotEmpty
        ? _lastTranscript
        : _conversation.where((e) => e.isUser).map((e) => e.text).join(' ');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.card,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _InvoiceSheet(
        serverUrl: widget.serverUrl,
        apiKey: widget.apiKey,
        transcript: transcript,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppColors.amber),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Voice Command',
          style: TextStyle(color: AppColors.cream, fontWeight: FontWeight.bold),
        ),
        actions: [
          if (_conversation.isNotEmpty)
            TextButton.icon(
              icon: const Icon(Icons.receipt_long, size: 16, color: AppColors.amber),
              label: const Text('Invoice', style: TextStyle(color: AppColors.amber, fontSize: 13)),
              onPressed: _showInvoiceSheet,
            ),
          IconButton(
            icon: Icon(
              _showTextInput ? Icons.mic_rounded : Icons.keyboard_rounded,
              color: AppColors.textDim,
            ),
            onPressed: () => setState(() => _showTextInput = !_showTextInput),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(child: _buildConversation()),
            if (_response?.needsConfirmation == true) _buildConfirmBar(),
            if (_response?.followUpPrompt != null &&
                _response?.needsConfirmation != true)
              _buildFollowUpHint(),
            if (_isProcessing) _buildProcessingArea(),
            if (!_isRecording && !_isProcessing) _buildInputArea(),
            if (_isRecording) _buildRecordingArea(),
          ],
        ),
      ),
    );
  }

  Widget _buildConversation() {
    if (_conversation.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.mic_rounded, color: AppColors.amber.withAlpha(77), size: 64),
            const SizedBox(height: 16),
            const Text(
              'Say something or type a command',
              style: TextStyle(color: AppColors.textMuted, fontSize: 16),
            ),
            const SizedBox(height: 8),
            const Text(
              '"Show me my leads"\n"Create a quote for the Penrith job"\n"What\'s my pipeline?"',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _conversation.length,
      itemBuilder: (context, index) {
        final entry = _conversation[index];
        return _buildBubble(entry.text, isUser: entry.isUser);
      },
    );
  }

  Widget _buildBubble(String text, {required bool isUser}) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
        margin: const EdgeInsets.symmetric(vertical: 4),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser ? AppColors.orange.withAlpha(38) : AppColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isUser
                ? AppColors.orange.withAlpha(51)
                : AppColors.border,
          ),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: isUser ? AppColors.cream : Colors.white,
            fontSize: 14,
            height: 1.4,
          ),
        ),
      ),
    );
  }

  Widget _buildConfirmBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      color: AppColors.card,
      child: Row(
        children: [
          Expanded(
            child: OutlinedButton(
              onPressed: () => _handleConfirm('cancel'),
              style: OutlinedButton.styleFrom(
                foregroundColor: AppColors.textDim,
                side: const BorderSide(color: AppColors.border),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              child: const Text('Cancel'),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: ElevatedButton(
              onPressed: () => _handleConfirm('yes'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.orange,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              child: const Text('Confirm', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFollowUpHint() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: AppColors.surface,
      child: Row(
        children: [
          const Icon(Icons.arrow_forward_ios, color: AppColors.amber, size: 12),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _response!.followUpPrompt!,
              style: const TextStyle(color: AppColors.amber, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: const BoxDecoration(
        color: AppColors.card,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.mic_rounded, color: AppColors.orange),
            onPressed: _startRecording,
          ),
          Expanded(
            child: TextField(
              controller: _textController,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: _response?.followUpPrompt ?? 'Type a voice command...',
                hintStyle: const TextStyle(color: AppColors.textMuted, fontSize: 14),
                filled: true,
                fillColor: AppColors.surface,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(20),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              onSubmitted: _handleTextSubmit,
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.send_rounded, color: AppColors.orange),
            onPressed: () => _handleTextSubmit(_textController.text),
          ),
        ],
      ),
    );
  }

  Widget _buildProcessingArea() {
    return Container(
      padding: const EdgeInsets.all(24),
      color: AppColors.card,
      child: const Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(color: AppColors.orange, strokeWidth: 2),
          ),
          SizedBox(width: 12),
          Text('Processing...', style: TextStyle(color: AppColors.orange, fontSize: 16)),
        ],
      ),
    );
  }

  Widget _buildRecordingArea() {
    return Container(
      padding: const EdgeInsets.all(24),
      color: AppColors.card,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          AnimatedBuilder(
            animation: _waveController,
            builder: (context, _) {
              return CustomPaint(
                size: const Size(double.infinity, 60),
                painter: _WaveformPainter(
                  progress: _waveController.value,
                  isRecording: true,
                  color: AppColors.orange,
                ),
              );
            },
          ),
          const SizedBox(height: 16),
          const Text('Listening...', style: TextStyle(color: AppColors.orange, fontSize: 16)),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: _stopRecording,
            child: Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.red,
                boxShadow: [
                  BoxShadow(color: AppColors.red.withAlpha(77), blurRadius: 16, spreadRadius: 4),
                ],
              ),
              child: const Icon(Icons.stop, color: Colors.white, size: 28),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConversationEntry {
  final String text;
  final bool isUser;
  _ConversationEntry({required this.text, required this.isUser});
}

// ── Voice → Invoice bottom sheet ─────────────────────────────────────────────
class _InvoiceSheet extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  final String transcript;

  const _InvoiceSheet({
    required this.serverUrl,
    required this.apiKey,
    required this.transcript,
  });

  @override
  State<_InvoiceSheet> createState() => _InvoiceSheetState();
}

class _InvoiceSheetState extends State<_InvoiceSheet> {
  bool _parsing = false;
  bool _generating = false;
  Map<String, dynamic>? _quoteDraft;
  String? _invoiceUrl;
  String? _error;

  @override
  void initState() {
    super.initState();
    _parseTranscript();
  }

  Future<void> _parseTranscript() async {
    setState(() { _parsing = true; _error = null; });
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/voice/quote-from-transcript'),
        headers: headers,
        body: jsonEncode({'transcript': widget.transcript}),
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      setState(() => _quoteDraft = data['quote_draft'] as Map<String, dynamic>?);
    } catch (e) {
      setState(() => _error = 'Parse error: $e');
    } finally {
      setState(() => _parsing = false);
    }
  }

  Future<void> _generateInvoice() async {
    if (_quoteDraft == null) return;
    setState(() { _generating = true; _error = null; });
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    final items = (_quoteDraft!['items'] as List?)?.map((i) => {
      'description': i['description'] ?? 'Labour',
      'qty': i['quantity'] ?? 1,
      'rate': i['unit_cost'] ?? 0,
      'gst': true,
    }).toList() ?? [
      {
        'description': _quoteDraft!['job_description'] ?? 'Construction Work',
        'qty': _quoteDraft!['labor_hours'] ?? 2,
        'rate': 150,
        'gst': true,
      },
      if ((_quoteDraft!['materials_cost'] ?? 0) > 0)
        {
          'description': 'Materials',
          'qty': 1,
          'rate': _quoteDraft!['materials_cost'],
          'gst': true,
        },
    ];

    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/invoice/generate'),
        headers: headers,
        body: jsonEncode({
          'client_name': _quoteDraft!['client_name'] ?? 'Client',
          'client_email': _quoteDraft!['client_email'] ?? '',
          'items': items,
          'notes': _quoteDraft!['notes'] ?? '',
        }),
      ).timeout(const Duration(seconds: 30));

      if (res.statusCode == 200 && res.headers['content-type']?.contains('pdf') == true) {
        setState(() => _invoiceUrl = 'Invoice PDF generated successfully');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Invoice PDF generated'),
              backgroundColor: AppColors.green,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      } else {
        final data = jsonDecode(res.body);
        setState(() => _error = data['error'] ?? 'Invoice failed');
      }
    } catch (e) {
      setState(() => _error = 'Invoice error: $e');
    } finally {
      setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20, right: 20, top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.receipt_long, color: AppColors.amber, size: 20),
              const SizedBox(width: 8),
              const Text(
                'Generate Invoice',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const Spacer(),
              IconButton(
                icon: const Icon(Icons.close, color: AppColors.textDim, size: 20),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (_parsing)
            const Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(width: 18, height: 18, child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2)),
                  SizedBox(width: 10),
                  Text('Parsing transcript...', style: TextStyle(color: AppColors.textDim)),
                ],
              ),
            )
          else if (_error != null)
            Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 13))
          else if (_invoiceUrl != null)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.green.withAlpha(26),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.green.withAlpha(77)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.check_circle, color: AppColors.green, size: 20),
                  SizedBox(width: 8),
                  Text('Invoice PDF generated', style: TextStyle(color: AppColors.green, fontWeight: FontWeight.bold)),
                ],
              ),
            )
          else if (_quoteDraft != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _DraftRow('Client', _quoteDraft!['client_name']?.toString() ?? 'TBD'),
                  _DraftRow('Job', _quoteDraft!['job_description']?.toString() ?? 'Construction Work'),
                  _DraftRow('Location', _quoteDraft!['location']?.toString() ?? 'TBD'),
                  _DraftRow('Labour hrs', '${_quoteDraft!['labor_hours'] ?? 2}'),
                  _DraftRow('Materials', '\$${_quoteDraft!['materials_cost'] ?? 0}'),
                  _DraftRow('Markup', '${_quoteDraft!['markup_percent'] ?? 20}%'),
                ],
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: _generating
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                    : const Icon(Icons.picture_as_pdf, size: 18),
                label: Text(_generating ? 'Generating PDF...' : 'Generate Invoice PDF'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: _generating ? null : _generateInvoice,
              ),
            ),
          ],
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _DraftRow extends StatelessWidget {
  final String label;
  final String value;
  const _DraftRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(
            width: 90,
            child: Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(color: Colors.white, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  final double progress;
  final bool isRecording;
  final Color color;

  _WaveformPainter({
    required this.progress,
    required this.isRecording,
    required this.color,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    final centerX = size.width / 2;
    for (var i = 0; i < 20; i++) {
      final x = centerX + (i - 10) * 8;
      final phase = (i * 0.3 + progress * 2 * pi);
      paint.color = color.withAlpha((150 + 100 * sin(phase)).toInt().clamp(100, 255));
      final h = isRecording ? size.height * 0.4 * sin(phase).abs() + 4 : 8.0;
      canvas.drawLine(
        Offset(x, size.height / 2 - h),
        Offset(x, size.height / 2 + h),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter old) =>
      progress != old.progress || isRecording != old.isRecording;
}
