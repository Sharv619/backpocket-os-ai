import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/voice_command_response.dart';
import 'tts_service.dart';
import 'offline_queue_service.dart';

enum VoiceFlowState { idle, recording, transcribing, processing, speaking, error, queuedOffline }

class VoiceCommandService extends ChangeNotifier {
  final String baseUrl;
  final String apiKey;
  late final TtsService _tts;
  final OfflineQueueService _queueService = OfflineQueueService();

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
  bool get isActive => _state != VoiceFlowState.idle && _state != VoiceFlowState.queuedOffline;
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

    if (!await _queueService.hasInternet()) {
      await _queueService.queueVoiceCommand(
        transcript: transcript,
        screenContext: _currentScreen,
        sessionId: _sessionId,
        metadata: {
          'selected_item_id': _selectedItemId,
          'tab_index': _tabIndex,
        },
      );
      _errorMessage = 'No reception. Pip saved your command and will process it when online.';
      _state = VoiceFlowState.queuedOffline;
      notifyListeners();
      return null;
    }

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

  Future<String?> transcribeAudio(PlatformFile platformFile) async {
    _state = VoiceFlowState.transcribing;
    notifyListeners();

    if (!await _queueService.hasInternet()) {
      await _queueService.queueVoiceCommand(
        transcript: "Pending transcription...",
        screenContext: _currentScreen,
        sessionId: _sessionId,
        metadata: {
          'selected_item_id': _selectedItemId,
          'tab_index': _tabIndex,
        },
        // audioPath: platformFile.path, // This would be problematic for web, queue raw bytes if possible
      );
      _errorMessage = 'No reception. Pip saved your recording and will transcribe it when online.';
      _state = VoiceFlowState.queuedOffline;
      notifyListeners();
      return null;
    }

    try {
      final uri = Uri.parse('$baseUrl/api/voice/transcribe');
      final request = http.MultipartRequest('POST', uri);

      if (kIsWeb) {
        // For web, use fromBytes
        request.files.add(http.MultipartFile.fromBytes(
          'audio',
          platformFile.bytes!,
          filename: platformFile.name,
        ));
      } else {
        // For mobile/desktop, use fromPath (requires dart:io)
        request.files.add(await http.MultipartFile.fromPath(
          'audio',
          platformFile.path!,
          filename: platformFile.name,
        ));
      }

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

  Future<VoiceCommandResponse?> processAudio(PlatformFile platformFile) async {
    final transcript = await transcribeAudio(platformFile);
    if (transcript == null) return null;
    return sendTranscript(transcript);
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

  Future<void> syncOfflineCommands() async {
    if (!await _queueService.hasInternet()) return;

    final commands = await _queueService.getQueuedCommands();
    if (commands.isEmpty) return;

    for (final cmd in commands) {
      final id = cmd['id'] as int;
      final transcript = cmd['transcript'] as String;
      final screenContext = cmd['screen_context'] as String;
      final sessionId = cmd['session_id'] as String?;
      final metadataStr = cmd['metadata'] as String?;
      final audioPath = cmd['audio_path'] as String?;

      Map<String, dynamic>? metadata;
      if (metadataStr != null) {
        try {
          metadata = jsonDecode(metadataStr);
        } catch (_) {}
      }

      bool success = false;
      if (audioPath != null) {
        // Upload audio
        try {
          final uri = Uri.parse('$baseUrl/api/voice/transcribe');
          final request = http.MultipartRequest('POST', uri)
            ..files.add(await http.MultipartFile.fromPath('audio', audioPath));
          if (apiKey.isNotEmpty) request.headers['X-API-Key'] = apiKey;

          final streamed = await request.send();
          final body = await streamed.stream.bytesToString();

          if (streamed.statusCode == 200) {
            final data = jsonDecode(body);
            final newTranscript = data['transcript'] as String?;
            if (newTranscript != null && newTranscript.isNotEmpty) {
              success = await _sendRawCommand(newTranscript, screenContext, sessionId, metadata);
            }
          }
        } catch (_) {}
      } else {
        success = await _sendRawCommand(transcript, screenContext, sessionId, metadata);
      }

      if (success) {
        await _queueService.removeCommand(id);
      }
    }
  }

  Future<bool> _sendRawCommand(String transcript, String screen, String? sessionId, Map<String, dynamic>? metadata) async {
    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/command'),
        headers: _headers,
        body: jsonEncode({
          'transcript': transcript,
          'screen_context': screen,
          'session_id': sessionId,
          'metadata': metadata,
        }),
      );
      return resp.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}
