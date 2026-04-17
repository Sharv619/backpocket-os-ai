import 'dart:math';
import 'package:flutter/material.dart';

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

  bool _isRecording = false;
  bool _showTextInput = false;
  VoiceCommandResponse? _response;
  final List<_ConversationEntry> _conversation = [];

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
  }

  @override
  void dispose() {
    _waveController.dispose();
    _textController.dispose();
    super.dispose();
  }

  Future<void> _handleTextSubmit(String text) async {
    if (text.isEmpty) return;

    setState(() {
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
    setState(() => _isRecording = true);
    // Text fallback since audio recording requires platform-specific setup
    setState(() {
      _isRecording = false;
      _showTextInput = true;
    });
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
            if (!_isRecording) _buildInputArea(),
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
            onTap: () => setState(() => _isRecording = false),
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
