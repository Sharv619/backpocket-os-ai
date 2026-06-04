import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/voice_command_response.dart';
import 'ai_edge_service.dart';
import 'server_url.dart';
import 'tts_service.dart';
import 'offline_queue_service.dart';

enum VoiceFlowState {
  idle,
  recording,
  transcribing,
  processing,
  speaking,
  error,
  queuedOffline,
}

class VoiceCommandService extends ChangeNotifier {
  final String baseUrl;
  final String apiKey;
  late final TtsService _tts;
  final AiEdgeService _aiEdge = AiEdgeService();
  final OfflineQueueService _queueService = OfflineQueueService();

  VoiceFlowState _state = VoiceFlowState.idle;
  String? _sessionId;
  VoiceCommandResponse? _lastResponse;
  String? _lastTranscript;
  String? _errorMessage;
  String _currentScreen = 'dashboard';
  int? _selectedItemId;
  int? _tabIndex;
  AiEdgeCapabilities _capabilities = AiEdgeCapabilities.unsupported();
  int _pendingSyncCount = 0;
  bool _syncingOfflineActions = false;
  String? _currentInferenceRequestId;
  bool _isLocalInferenceActive = false;
  AiEdgeInferenceEvent? _latestInferenceEvent;
  final StreamController<AiEdgeInferenceEvent> _inferenceController =
      StreamController<AiEdgeInferenceEvent>.broadcast();
  StreamSubscription<AiEdgeInferenceEvent>? _inferenceSubscription;
  StreamSubscription<bool>? _connectivitySubscription;

  VoiceCommandService({required String baseUrl, this.apiKey = ''})
    : baseUrl = normalizeServerUrl(baseUrl) {
    _tts = TtsService(baseUrl: this.baseUrl, apiKey: apiKey);
    _connectivitySubscription = _queueService.connectivityChanges().listen((
      hasInternet,
    ) {
      unawaited(_handleConnectivityChange(hasInternet));
    });
    unawaited(_bootstrapOfflineState());
  }

  VoiceFlowState get state => _state;
  VoiceCommandResponse? get lastResponse => _lastResponse;
  String? get lastTranscript => _lastTranscript;
  String? get errorMessage => _errorMessage;
  String? get sessionId => _sessionId;
  bool get isActive =>
      _state != VoiceFlowState.idle && _state != VoiceFlowState.queuedOffline;
  bool get isCollecting => _lastResponse?.sessionState?.isCollecting ?? false;
  bool get isConfirming => _lastResponse?.sessionState?.isConfirming ?? false;
  String? get followUpPrompt => _lastResponse?.followUpPrompt;
  AiEdgeCapabilities get offlineCapabilities => _capabilities;
  int get pendingSyncCount => _pendingSyncCount;
  String? get currentInferenceRequestId => _currentInferenceRequestId;
  bool get isLocalInferenceActive => _isLocalInferenceActive;
  AiEdgeInferenceEvent? get latestInferenceEvent => _latestInferenceEvent;
  Stream<AiEdgeInferenceEvent> get inferenceEvents => _inferenceController.stream;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (apiKey.isNotEmpty) 'X-API-Key': apiKey,
  };

  void setScreenContext(String screen, {int? tabIndex, int? selectedItemId}) {
    _currentScreen = screen;
    _tabIndex = tabIndex;
    _selectedItemId = selectedItemId;
  }

  Future<void> refreshOfflineState() async {
    _capabilities = await _aiEdge.getCapabilities();
    _pendingSyncCount = await _queueService.getPendingOfflineActionCount();
    notifyListeners();
  }

  Future<void> _bootstrapOfflineState() async {
    await refreshOfflineState();
    if (_pendingSyncCount == 0) return;
    if (!await _queueService.hasInternet()) return;

    await _syncOfflineActions();
    await refreshOfflineState();
  }

  Future<void> _handleConnectivityChange(bool hasInternet) async {
    if (!hasInternet) {
      await refreshOfflineState();
      return;
    }

    await _syncOfflineActions();
    await refreshOfflineState();
  }

  Future<VoiceCommandResponse?> sendTranscript(String transcript) async {
    if (transcript.trim().isEmpty) return null;

    _state = VoiceFlowState.processing;
    _lastTranscript = transcript;
    _errorMessage = null;
    notifyListeners();

    final metadata = {
      'selected_item_id': _selectedItemId,
      'tab_index': _tabIndex,
    };

    final hasInternet = await _queueService.hasInternet();
    if (hasInternet) {
      await _syncOfflineActions();
    }

    if (!hasInternet) {
      final localResponse = await _runOfflinePipeline(
        transcript: transcript,
        metadata: metadata,
      );
      if (localResponse != null) {
        return localResponse;
      }
      await _queueService.queueVoiceCommand(
        transcript: transcript,
        screenContext: _currentScreen,
        sessionId: _sessionId,
        metadata: metadata,
      );
      _errorMessage =
          'No reception. This command was queued because the offline executor could not run it locally.';
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
          'metadata': metadata,
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

    if (!await _queueService.hasInternet()) {
      await _queueService.queueVoiceCommand(
        transcript: "Pending transcription...",
        screenContext: _currentScreen,
        sessionId: _sessionId,
        metadata: {'selected_item_id': _selectedItemId, 'tab_index': _tabIndex},
        audioPath: audioPath,
      );
      _errorMessage =
          'No reception. Pip saved your recording and will transcribe it when online.';
      _state = VoiceFlowState.queuedOffline;
      notifyListeners();
      return null;
    }

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

  Future<bool> canUseOfflineSpeechInput() async {
    final capabilities = await _aiEdge.getCapabilities();
    return capabilities.offlineSpeechAvailable;
  }

  Future<bool> hasInternet() => _queueService.hasInternet();

  Future<VoiceCommandResponse?> captureOfflineSpeech({String? prompt}) async {
    _state = VoiceFlowState.recording;
    _errorMessage = null;
    notifyListeners();

    final transcript = await _aiEdge.recognizeOfflineSpeech(
      prompt: prompt ?? 'Talk to Pip',
    );
    if (transcript == null || transcript.trim().isEmpty) {
      _errorMessage =
          'Offline dictation is unavailable on this device. Type the command instead.';
      _state = VoiceFlowState.error;
      notifyListeners();
      return null;
    }

    _lastTranscript = transcript;
    _state = VoiceFlowState.transcribing;
    notifyListeners();
    return sendTranscript(transcript);
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
        ..files.add(
          http.MultipartFile.fromBytes('audio', bytes, filename: filename),
        );
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

    if (!await _queueService.hasInternet()) {
      final localResponse = await _runOfflinePipeline(
        transcript: response,
        metadata: {
          'selected_item_id': _selectedItemId,
          'tab_index': _tabIndex,
        },
      );
      if (localResponse != null) {
        return localResponse;
      }
    }

    try {
      final resp = await http.post(
        Uri.parse('$baseUrl/api/voice/confirm'),
        headers: _headers,
        body: jsonEncode({'session_id': _sessionId, 'response': response}),
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
    _currentInferenceRequestId = null;
    _isLocalInferenceActive = false;
    _latestInferenceEvent = null;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    _state = VoiceFlowState.idle;
    notifyListeners();
  }

  @override
  void dispose() {
    _connectivitySubscription?.cancel();
    _inferenceSubscription?.cancel();
    _inferenceController.close();
    super.dispose();
  }

  Future<VoiceCommandResponse?> _runOfflinePipeline({
    required String transcript,
    required Map<String, dynamic> metadata,
  }) async {
    final requestId = DateTime.now().microsecondsSinceEpoch.toString();
    _currentInferenceRequestId = requestId;
    _isLocalInferenceActive = true;
    _latestInferenceEvent = null;
    await _inferenceSubscription?.cancel();
    _inferenceSubscription = _aiEdge
        .getInferenceStream(requestId)
        .listen((event) {
          _latestInferenceEvent = event;
          _inferenceController.add(event);
          notifyListeners();
        });
    notifyListeners();

    final Map<String, dynamic>? data;
    try {
      data = await _aiEdge.runIntentPipeline(
        transcript: transcript,
        screenContext: _currentScreen,
        sessionId: _sessionId,
        requestId: requestId,
        metadata: metadata,
      );
    } finally {
      _isLocalInferenceActive = false;
      await _inferenceSubscription?.cancel();
      _inferenceSubscription = null;
      notifyListeners();
    }

    if (data == null) return null;

    final response = VoiceCommandResponse.fromJson(data);
    _lastResponse = response;
    _sessionId = response.sessionState?.sessionId ?? _sessionId;
    await _persistOfflineResult(transcript, response);

    _state = VoiceFlowState.speaking;
    notifyListeners();
    await _speakResponse(response);
    _state = response.isQueuedForSync
        ? VoiceFlowState.queuedOffline
        : VoiceFlowState.idle;
    notifyListeners();
    return response;
  }

  Future<void> _persistOfflineResult(
    String transcript,
    VoiceCommandResponse response,
  ) async {
    final clientActionId = response.result['client_action_id'] as String?;
    if (clientActionId == null || clientActionId.isEmpty) {
      return;
    }

    final payload = response.result['sync_payload'];
    await _queueService.recordOfflineAction(
      clientActionId: clientActionId,
      intent: response.intent ?? 'unknown',
      transcript: transcript,
      screenContext: _currentScreen,
      payload: payload is Map
          ? Map<String, dynamic>.from(payload)
          : <String, dynamic>{},
      responseJson: {
        'intent': response.intent,
        'action': response.action,
        'speech_response': response.speechResponse,
        'result': response.result,
      },
      syncRequired: response.result['sync_required'] == true,
    );
    _pendingSyncCount = await _queueService.getPendingOfflineActionCount();
  }

  Future<void> _syncOfflineActions() async {
    if (_syncingOfflineActions) return;
    _syncingOfflineActions = true;
    try {
      final actions = await _queueService.getPendingOfflineActions();
      for (final action in actions) {
        try {
          final response = await _queueService.syncActionToServer(
            baseUrl: baseUrl,
            apiKey: apiKey,
            action: action,
          );
          if (response != null) {
            await _queueService.markOfflineActionSynced(
              action['id'] as int,
              serverResponse: response,
            );
          }
        } catch (e) {
          await _queueService.markOfflineActionError(
            action['id'] as int,
            e.toString(),
          );
        }
      }
    } finally {
      _pendingSyncCount = await _queueService.getPendingOfflineActionCount();
      _syncingOfflineActions = false;
      notifyListeners();
    }
  }
}
