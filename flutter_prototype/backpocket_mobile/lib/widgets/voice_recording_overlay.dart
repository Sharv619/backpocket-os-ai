import 'dart:math';
import 'package:flutter/material.dart';
import '../services/voice_command_service.dart';

class VoiceRecordingOverlay extends StatefulWidget {
  final VoiceCommandService voiceService;
  final String? transcript;
  final String? speechResponse;
  final String? followUpPrompt;
  final VoidCallback onClose;
  final ValueChanged<String>? onTextSubmit;

  const VoiceRecordingOverlay({
    super.key,
    required this.voiceService,
    this.transcript,
    this.speechResponse,
    this.followUpPrompt,
    required this.onClose,
    this.onTextSubmit,
  });

  @override
  State<VoiceRecordingOverlay> createState() => _VoiceRecordingOverlayState();
}

class _VoiceRecordingOverlayState extends State<VoiceRecordingOverlay>
    with TickerProviderStateMixin {
  late AnimationController _waveController;
  final TextEditingController _textController = TextEditingController();
  bool _showTextInput = false;

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat();
  }

  @override
  void dispose() {
    _waveController.dispose();
    _textController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black.withAlpha(204),
      child: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 40),
            _buildStatusIndicator(),
            const Spacer(),
            if (widget.speechResponse != null && widget.speechResponse!.isNotEmpty)
              _buildSpeechBubble(widget.speechResponse!, isPip: true),
            if (widget.transcript != null && widget.transcript!.isNotEmpty)
              _buildSpeechBubble(widget.transcript!, isPip: false),
            if (widget.followUpPrompt != null)
              _buildFollowUpPrompt(),
            const SizedBox(height: 16),
            if (widget.voiceService.state == VoiceFlowState.recording)
              _buildWaveform(),
            if (_showTextInput) _buildTextInput(),
            const SizedBox(height: 24),
            _buildActions(),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusIndicator() {
    String label;
    Color color;
    switch (widget.voiceService.state) {
      case VoiceFlowState.recording:
        label = 'Listening...';
        color = const Color(0xFFEF4444);
      case VoiceFlowState.transcribing:
        label = 'Transcribing...';
        color = const Color(0xFFFBBF24);
      case VoiceFlowState.processing:
        label = 'Processing...';
        color = const Color(0xFFFBBF24);
      case VoiceFlowState.speaking:
        label = 'Pip is speaking...';
        color = const Color(0xFF22C55E);
      case VoiceFlowState.error:
        label = widget.voiceService.errorMessage ?? 'Error';
        color = const Color(0xFFEF4444);
      case VoiceFlowState.queuedOffline:
        label = 'Saved Offline';
        color = const Color(0xFF6B7280);
      case VoiceFlowState.idle:
        label = 'Tap mic or type a command';
        color = const Color(0xFFF97316);
    }

    return Column(
      children: [
        Icon(Icons.mic_rounded, color: color, size: 48),
        const SizedBox(height: 12),
        Text(
          label,
          style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.w600),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildSpeechBubble(String text, {required bool isPip}) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 6),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isPip ? const Color(0xFF1A2A1A) : const Color(0xFF211708),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isPip
              ? const Color(0xFF22C55E).withAlpha(51)
              : const Color(0xFFF97316).withAlpha(51),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            isPip ? Icons.smart_toy_rounded : Icons.person_rounded,
            color: isPip ? const Color(0xFF22C55E) : const Color(0xFFF97316),
            size: 18,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFollowUpPrompt() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 6),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1208),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFBBF24).withAlpha(51)),
      ),
      child: Row(
        children: [
          const Icon(Icons.mic, color: Color(0xFFFBBF24), size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              widget.followUpPrompt!,
              style: const TextStyle(color: Color(0xFFFBBF24), fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWaveform() {
    return AnimatedBuilder(
      animation: _waveController,
      builder: (context, _) {
        return SizedBox(
          height: 60,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(20, (i) {
              final phase = _waveController.value * 2 * pi + i * 0.3;
              final height = 10 + 25 * sin(phase).abs();
              return Container(
                width: 3,
                height: height,
                margin: const EdgeInsets.symmetric(horizontal: 2),
                decoration: BoxDecoration(
                  color: const Color(0xFFF97316).withAlpha((150 + 100 * sin(phase)).toInt().clamp(100, 255)),
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            }),
          ),
        );
      },
    );
  }

  Widget _buildTextInput() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 24),
      child: TextField(
        controller: _textController,
        autofocus: true,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: 'Type a command...',
          hintStyle: const TextStyle(color: Color(0xFF9E8E7E)),
          filled: true,
          fillColor: const Color(0xFF211708),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0x22FFFFFF)),
          ),
          suffixIcon: IconButton(
            icon: const Icon(Icons.send_rounded, color: Color(0xFFF97316)),
            onPressed: () {
              if (_textController.text.isNotEmpty) {
                widget.onTextSubmit?.call(_textController.text);
                _textController.clear();
              }
            },
          ),
        ),
        onSubmitted: (text) {
          if (text.isNotEmpty) {
            widget.onTextSubmit?.call(text);
            _textController.clear();
          }
        },
      ),
    );
  }

  Widget _buildActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(
          icon: const Icon(Icons.keyboard_rounded, color: Color(0xFFD4C4B4), size: 28),
          onPressed: () => setState(() => _showTextInput = !_showTextInput),
          tooltip: 'Type instead',
        ),
        const SizedBox(width: 32),
        IconButton(
          icon: const Icon(Icons.close_rounded, color: Color(0xFFEF4444), size: 32),
          onPressed: widget.onClose,
          tooltip: 'Close',
        ),
      ],
    );
  }
}
