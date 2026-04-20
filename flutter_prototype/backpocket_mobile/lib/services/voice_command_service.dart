import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/voice_command_response.dart';
import 'tts_service.dart';

enum VoiceFlowState { idle, recording, transcribing, processing, speaking, error }

class VoiceCommandService extends ChangeNotifier {
  final String baseUrl;
  final String apiKey;
  late final TtsService _tts;

  VoiceFlowState _state = VoiceFlowState.idle;
  String? _sessionId;
  VoiceCommandResponse? _lastResponse;
  String? _lastTranscript;
  String? _errorMessage;
  String _currentScreen = 'dashboard';
  int? _selectedItemId;
  int? _tabIndex;

  VoiceCommandService({required this.baseUrl, this.apiKey = ''}) {
    _tts = TtsService(baseUrl: baseUrl, apiKey: apiKey);
  }

  VoiceFlowState get state => _state;
  VoiceCommandResponse? get lastResponse => _lastResponse;
  String? get lastTranscript => _lastTranscript;
  String? get errorMessage => _errorMessage;
  String? get sessionId => _sessionId;
  bool get isActive => _state != VoiceFlowState.idle;
  bool get isCollecting => _lastResponse?.sessionState?.isCollecting ?? false;
  bool get isConfirming => _lastResponse?.sessionState?.isConfirming ?? false;
  String? get followUpPrompt => _lastResponse?.followUpPrompt;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
  };

  void setScreenContext(String screen, {int? tabIndex, int? selectedItemId}) {
    _currentScreen = screen;
    _tabIndex = tabIndex;
    _selectedItemId = selectedItemId;
  }

  Future<VoiceCommandResponse?> sendTranscript(String transcript) async {
    if (transcript.trim().isEmpty) return null;

    _state = VoiceFlowState.processing;
    _lastTranscript = transcript;
    _errorMessage = null;
    notifyListeners();

    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/command'),
        headers: _headers,
        body: jsonEncode({
          'transcript': transcript,
          'screen_context': _currentScreen,
          'session_id': _sessionId,
          'metadata': {
            'selected_item_id': _selectedItemId,
            'tab_index': _tabIndex,
          },
        }),
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        _lastResponse = VoiceCommandResponse.fromJson(data);
        _sessionId = _lastResponse?.sessionState?.sessionId ?? _sessionId;
        _state = VoiceFlowState.speaking;
        notifyListeners();
        await _speakResponse(_lastResponse);
        _state = VoiceFlowState.idle;
        notifyListeners();
        return _lastResponse;
      } else {
        _errorMessage = 'Server error: ${resp.statusCode}';
        _state = VoiceFlowState.error;
        notifyListeners();
      }
    } catch (e) {
      _errorMessage = 'Connection error: $e';
      _state = VoiceFlowState.error;
      notifyListeners();
    }
    return null;
  }

  Future<void> _speakResponse(VoiceCommandResponse? response) async {
    final text = response?.speechResponse ?? response?.followUpPrompt;
    if (text != null && text.isNotEmpty) {
      await _tts.speak(text);
    }
  }

  Future<String?> transcribeAudio(String audioPath) async {
    _state = VoiceFlowState.transcribing;
    notifyListeners();

    try {
      final uri = Uri.parse('$baseUrl/api/voice/transcribe');
      final request = http.MultipartRequest('POST', uri)
        ..files.add(await http.MultipartFile.fromPath('audio', audioPath));
      if (apiKey.isNotEmpty) {
        request.headers['X-API-Key'] = apiKey;
      }

      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();

      if (streamed.statusCode == 200) {
        final data = jsonDecode(body);
        final transcript = data['transcript'] as String?;
        if (transcript != null && transcript.isNotEmpty) {
          return transcript;
        }
        _errorMessage = data['error'] ?? 'Empty transcription';
      } else {
        _errorMessage = 'Transcription failed: ${streamed.statusCode}';
      }
    } catch (e) {
      _errorMessage = 'Transcription error: $e';
    }

    _state = VoiceFlowState.error;
    notifyListeners();
    return null;
  }

  Future<VoiceCommandResponse?> processAudio(String audioPath) async {
    final transcript = await transcribeAudio(audioPath);
    if (transcript == null) return null;
    return sendTranscript(transcript);
  }

  /// Web-safe: upload raw bytes (from blob URL) instead of a file path.
  Future<VoiceCommandResponse?> processAudioBytes(
    Uint8List bytes,
    String filename,
  ) async {
    _state = VoiceFlowState.transcribing;
    notifyListeners();

    try {
      final uri = Uri.parse('$baseUrl/api/voice/transcribe');
      final request = http.MultipartRequest('POST', uri)
        ..files.add(http.MultipartFile.fromBytes('audio', bytes, filename: filename));
      if (apiKey.isNotEmpty) request.headers['X-API-Key'] = apiKey;

      final streamed = await request.send();
      final body = await streamed.stream.bytesToString();

      if (streamed.statusCode == 200) {
        final data = jsonDecode(body);
        final transcript = data['transcript'] as String?;
        if (transcript != null && transcript.isNotEmpty) {
          return sendTranscript(transcript);
        }
        _errorMessage = data['error'] ?? 'Empty transcription';
      } else {
        _errorMessage = 'Transcription failed: ${streamed.statusCode}';
      }
    } catch (e) {
      _errorMessage = 'Transcription error: $e';
    }

    _state = VoiceFlowState.error;
    notifyListeners();
    return null;
  }

  Future<VoiceCommandResponse?> sendConfirmation(String response) async {
    if (_sessionId == null) return null;

    _state = VoiceFlowState.processing;
    notifyListeners();

    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/confirm'),
        headers: _headers,
        body: jsonEncode({
          'session_id': _sessionId,
          'response': response,
        }),
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        _lastResponse = VoiceCommandResponse.fromJson(data);
        _state = VoiceFlowState.speaking;
        notifyListeners();
        await _speakResponse(_lastResponse);
        _state = VoiceFlowState.idle;
        notifyListeners();
        return _lastResponse;
      }
    } catch (e) {
      _errorMessage = 'Confirm error: $e';
      _state = VoiceFlowState.error;
      notifyListeners();
    }
    return null;
  }

  Future<List<Map<String, dynamic>>> getScreenIntents(String screen) async {
    try {
      final resp = await http.get(
        Uri.parse('$baseUrl/api/voice/intents?screen=$screen'),
        headers: _headers,
      );
      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body);
        return List<Map<String, dynamic>>.from(data['intents'] ?? []);
      }
    } catch (e) {
      debugPrint('Failed to fetch intents: $e');
    }
    return [];
  }

  void resetSession() {
    _sessionId = null;
    _lastResponse = null;
    _lastTranscript = null;
    _errorMessage = null;
    _state = VoiceFlowState.idle;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    _state = VoiceFlowState.idle;
    notifyListeners();
  }
}
