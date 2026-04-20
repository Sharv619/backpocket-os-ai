import 'package:flutter/material.dart';
import '../services/voice_command_service.dart';

class VoiceFab extends StatefulWidget {
  final VoiceCommandService voiceService;
  final VoidCallback? onTap;
  final VoidCallback? onLongPress;

  const VoiceFab({
    super.key,
    required this.voiceService,
    this.onTap,
    this.onLongPress,
  });

  @override
  State<VoiceFab> createState() => _VoiceFabState();
}

class _VoiceFabState extends State<VoiceFab> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    widget.voiceService.addListener(_onStateChange);
  }

  void _onStateChange() {
    final isActive = widget.voiceService.isActive;
    final reduce = mounted ? MediaQuery.of(context).disableAnimations : false;
    if (isActive && !reduce && !_pulseController.isAnimating) {
      _pulseController.repeat(reverse: true);
    } else if ((!isActive || reduce) && _pulseController.isAnimating) {
      _pulseController.stop();
      _pulseController.reset();
    }
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    widget.voiceService.removeListener(_onStateChange);
    _pulseController.dispose();
    super.dispose();
  }

  Color _fabColor() {
    switch (widget.voiceService.state) {
      case VoiceFlowState.recording:
        return const Color(0xFFEF4444);
      case VoiceFlowState.transcribing:
      case VoiceFlowState.processing:
        return const Color(0xFFFBBF24);
      case VoiceFlowState.speaking:
        return const Color(0xFF22C55E);
      case VoiceFlowState.error:
        return const Color(0xFFEF4444);
      case VoiceFlowState.idle:
        return const Color(0xFFF97316);
    }
  }

  IconData _fabIcon() {
    switch (widget.voiceService.state) {
      case VoiceFlowState.recording:
        return Icons.stop_rounded;
      case VoiceFlowState.transcribing:
      case VoiceFlowState.processing:
        return Icons.hourglass_top_rounded;
      case VoiceFlowState.speaking:
        return Icons.volume_up_rounded;
      case VoiceFlowState.error:
        return Icons.error_outline_rounded;
      case VoiceFlowState.idle:
        return Icons.mic_rounded;
    }
  }

  String? _statusLabel() {
    switch (widget.voiceService.state) {
      case VoiceFlowState.recording:
        return 'Listening...';
      case VoiceFlowState.transcribing:
        return 'Transcribing...';
      case VoiceFlowState.processing:
        return 'Thinking...';
      case VoiceFlowState.speaking:
        return 'Speaking...';
      case VoiceFlowState.error:
        return 'Error';
      case VoiceFlowState.idle:
        return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final label = _statusLabel();
    final isProcessing = widget.voiceService.state == VoiceFlowState.transcribing ||
        widget.voiceService.state == VoiceFlowState.processing;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null)
          Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1208),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: _fabColor().withAlpha(77)),
            ),
            child: Text(
              label,
              style: TextStyle(color: _fabColor(), fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ),
        Semantics(
          label: label ?? 'Activate voice command',
          hint: 'Double-tap to activate. Long-press to open full voice screen.',
          button: true,
          child: AnimatedBuilder(
            animation: _pulseAnimation,
            builder: (context, child) {
              return Transform.scale(
                scale: widget.voiceService.isActive ? _pulseAnimation.value : 1.0,
                child: child,
              );
            },
            child: GestureDetector(
              onLongPress: widget.onLongPress,
              child: FloatingActionButton(
                heroTag: 'voice_fab',
                onPressed: widget.onTap,
                backgroundColor: _fabColor(),
                elevation: 6,
                child: isProcessing
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          color: Colors.white,
                        ),
                      )
                    : Icon(_fabIcon(), color: Colors.white, size: 28),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
