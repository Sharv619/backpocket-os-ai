import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../theme.dart';

// Stub for audio recording - using text input fallback for now
// TODO: Fix record package version mismatch - using stub implementation
class AudioRecorder {
  bool _hasPermission = false;
  bool _isRecording = false;

  Future<bool> hasPermission() async => _hasPermission;

  Future<void> start(Object config, String path) async {
    _isRecording = true;
    _hasPermission = true;
  }

  Future<String?> stop() async {
    _isRecording = false;
    return '/tmp/voice_stub.m4a';
  }

  Future<bool> isRecording() async => _isRecording;

  void dispose() {}
}

class RecordConfig {
  final int encoder;
  final int sampleRate;
  final int bitRate;

  RecordConfig({
    this.encoder = 0,
    this.sampleRate = 16000,
    this.bitRate = 128000,
  });
}

class AudioEncoder {
  static const int aacLc = 0;
}

class VoiceInputScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const VoiceInputScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<VoiceInputScreen> createState() => _VoiceInputScreenState();
}

class _VoiceInputScreenState extends State<VoiceInputScreen>
    with SingleTickerProviderStateMixin {
  final AudioRecorder _recorder = AudioRecorder();
  late AnimationController _waveController;

  bool _isRecording = false;
  bool _isProcessing = false;
  String? _error;
  String? _transcript;
  List<double> _waveform = [];

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  @override
  void dispose() {
    _waveController.dispose();
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    // For now, show a text input dialog as fallback since audio recording is broken
    // TODO: Fix record package and re-enable voice recording
    final text = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Voice Input'),
        content: const Text(
          'Voice recording is temporarily unavailable. Type your request:',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
        ],
      ),
    );

    if (text != null && text.isNotEmpty) {
      setState(() {
        _transcript = text;
        _isProcessing = true;
      });
      // Use text-to-quote endpoint instead of voice
      await _processTextToQuote(text);
    }
  }

  Future<void> _processTextToQuote(String text) async {
    try {
      final response = await http.post(
        Uri.parse('${widget.serverUrl}/api/voice/quote-from-transcript'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'transcript': text}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _transcript = text;
          _isProcessing = false;
        });
      } else {
        setState(() {
          _error = 'Failed to process: ${response.statusCode}';
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error: $e';
        _isProcessing = false;
      });
    }
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stop();
    setState(() {
      _isRecording = false;
      _isProcessing = true;
    });

    if (path != null) {
      await _processAudio(path);
    }
  }

  Future<void> _processAudio(String filePath) async {
    try {
      final file = File(filePath);
      final bytes = await file.readAsBytes();

      final uri = Uri.parse('${widget.serverUrl}/api/voice/transcribe');
      final request = http.MultipartRequest('POST', uri)
        ..files.add(
          http.MultipartFile.fromBytes('audio', bytes, filename: 'voice.m4a'),
        )
        ..headers['X-API-Key'] = widget.apiKey;

      final streamed = await request.send();
      final response = await http.Response.fromStream(streamed);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _transcript = data['transcript'];
        });

        if (_transcript != null && _transcript!.isNotEmpty) {
          await _generateQuote(_transcript!);
        }
      } else {
        setState(() {
          _error = 'Transcription failed: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error processing audio: $e';
      });
    } finally {
      setState(() {
        _isProcessing = false;
      });
      if (filePath.isNotEmpty) {
        File(filePath).delete();
      }
    }
  }

  Future<void> _generateQuote(String transcript) async {
    try {
      final uri = Uri.parse(
        '${widget.serverUrl}/api/voice/quote-from-transcript',
      );
      final response = await http.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
        },
        body: jsonEncode({'transcript': transcript}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (mounted && data['quote_draft'] != null) {
          Navigator.pushReplacementNamed(
            context,
            '/quote-review',
            arguments: data['quote_draft'],
          );
        }
      } else {
        setState(() {
          _error = 'Quote generation failed';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error generating quote: $e';
      });
    }
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
          'Voice-to-Quote',
          style: TextStyle(color: AppColors.cream, fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              const Spacer(),
              _buildVisualizer(),
              const SizedBox(height: 48),
              _buildPrompt(),
              const Spacer(),
              _buildRecordButton(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildVisualizer() {
    return Container(
      height: 120,
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Center(
        child: AnimatedBuilder(
          animation: _waveController,
          builder: (context, child) {
            return CustomPaint(
              size: const Size(double.infinity, 120),
              painter: _WaveformPainter(
                progress: _waveController.value,
                isRecording: _isRecording,
                color: _isRecording ? AppColors.orange : AppColors.amber,
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildPrompt() {
    return Column(
      children: [
        Text(
          _isRecording
              ? 'Listening...'
              : _transcript ?? 'Tell me about the job',
          style: const TextStyle(
            color: AppColors.cream,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 8),
        const Text(
          'Describe the work needed and I\'ll create a quote',
          style: TextStyle(color: AppColors.textMuted, fontSize: 14),
          textAlign: TextAlign.center,
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.red.withAlpha(26),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              _error!,
              style: const TextStyle(color: AppColors.red, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildRecordButton() {
    return GestureDetector(
      onTap: _isRecording ? _stopRecording : _startRecording,
      child: Container(
        width: 80,
        height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: _isRecording ? AppColors.red : AppColors.orange,
          boxShadow: [
            BoxShadow(
              color: (_isRecording ? AppColors.red : AppColors.orange)
                  .withAlpha(77),
              blurRadius: 20,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Center(
          child: _isProcessing
              ? const SizedBox(
                  width: 32,
                  height: 32,
                  child: CircularProgressIndicator(
                    color: AppColors.cream,
                    strokeWidth: 3,
                  ),
                )
              : Icon(
                  _isRecording ? Icons.stop : Icons.mic,
                  color: AppColors.cream,
                  size: 36,
                ),
        ),
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

    final center = size.width / 2;
    final frequency = isRecording ? 5.0 : 1.0;

    for (var i = 0; i < 20; i++) {
      final x = center + (i - 10) * 8;
      final offset = (i * 0.1 + progress) * 3.14159 * 2;
      final alpha = (0.3 + (i % 3) * 0.2);
      paint.color = color.withAlpha((alpha * 255).toInt());

      final height = isRecording
          ? (size.height / 2) * 0.6 * (0.5 + 0.5 * (offset % 1) * frequency)
          : 10.0;

      canvas.drawLine(
        Offset(x, size.height / 2 - height),
        Offset(x, size.height / 2 + height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) {
    return progress != oldDelegate.progress ||
        isRecording != oldDelegate.isRecording ||
        color != oldDelegate.color;
  }
}
