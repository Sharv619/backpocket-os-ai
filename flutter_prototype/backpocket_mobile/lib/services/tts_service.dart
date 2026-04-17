import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class TtsService {
  final String baseUrl;
  final String apiKey;
  bool _isSpeaking = false;

  TtsService({required this.baseUrl, this.apiKey = ''});

  bool get isSpeaking => _isSpeaking;

  Future<Uint8List?> synthesize(String text, {String voice = 'male'}) async {
    if (text.isEmpty) return null;

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
        final data = jsonDecode(resp.body);
        final audioBase64 = data['audio'] as String?;
        if (audioBase64 != null) {
          return base64Decode(audioBase64);
        }
      }
    } catch (e) {
      debugPrint('TTS synthesis error: $e');
    } finally {
      _isSpeaking = false;
    }
    return null;
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
      return resp.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  void stop() {
    _isSpeaking = false;
  }
}
