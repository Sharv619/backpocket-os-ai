import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:audioplayers/audioplayers.dart';

class TtsService {
  final String baseUrl;
  final String apiKey;
  final AudioPlayer _player = AudioPlayer();
  bool _isSpeaking = false;

  TtsService({required this.baseUrl, this.apiKey = ''});

  bool get isSpeaking => _isSpeaking;

  Future<void> speak(String text, {String voice = 'male'}) async {
    if (text.isEmpty) return;
    final bytes = await _fetchAudio(text, voice: voice);
    if (bytes != null) await _playBytes(bytes);
  }

  Future<Uint8List?> synthesize(String text, {String voice = 'male'}) async {
    return _fetchAudio(text, voice: voice);
  }

  Future<Uint8List?> _fetchAudio(String text, {String voice = 'male'}) async {
    try {
      _isSpeaking = true;
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/tts'),
        headers: {
          'Content-Type': 'application/json',
          if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
        },
        body: jsonEncode({'text': text, 'voice': voice}),
      );

      if (resp.statusCode == 200) {
        final contentType = resp.headers['content-type'] ?? '';
        if (contentType.contains('audio')) {
          return resp.bodyBytes;
        }
        // Fallback: base64 in JSON body
        final data = jsonDecode(resp.body);
        final audioBase64 = data['audio'] as String?;
        if (audioBase64 != null) return base64Decode(audioBase64);
      }
    } catch (e) {
      debugPrint('TTS fetch error: $e');
    } finally {
      _isSpeaking = false;
    }
    return null;
  }

  Future<void> _playBytes(Uint8List bytes) async {
    try {
      _isSpeaking = true;
      if (kIsWeb) {
        // Web: use BytesSource directly (audioplayers 6.x web support)
        await _player.play(BytesSource(bytes));
      } else {
        await _player.play(BytesSource(bytes));
      }
      // Wait for completion
      await _player.onPlayerComplete.first;
    } catch (e) {
      debugPrint('TTS playback error: $e');
    } finally {
      _isSpeaking = false;
    }
  }

  Future<void> stop() async {
    _isSpeaking = false;
    await _player.stop();
  }

  Future<bool> testConnection() async {
    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/tts'),
        headers: {
          'Content-Type': 'application/json',
          if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
        },
        body: jsonEncode({'text': 'test', 'voice': 'male'}),
      );
      return resp.statusCode == 200 &&
          (resp.headers['content-type'] ?? '').contains('audio');
    } catch (_) {
      return false;
    }
  }

  void dispose() {
    _player.dispose();
  }
}
