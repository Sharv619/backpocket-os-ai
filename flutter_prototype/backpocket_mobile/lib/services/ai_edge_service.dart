import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

enum AiEdgeInferenceEventType {
  started,
  chunk,
  completed,
  error,
  fallback,
  unknown,
}

class AiEdgeInferenceEvent {
  final String requestId;
  final AiEdgeInferenceEventType type;
  final String chunk;
  final String textAccumulation;
  final String finalResponse;
  final String message;
  final String runtimeMode;

  const AiEdgeInferenceEvent({
    required this.requestId,
    required this.type,
    this.chunk = '',
    this.textAccumulation = '',
    this.finalResponse = '',
    this.message = '',
    this.runtimeMode = '',
  });

  factory AiEdgeInferenceEvent.fromJson(
    Map<String, dynamic> json, {
    required String textAccumulation,
  }) {
    final type = _parseInferenceEventType(json['type'] as String?);
    return AiEdgeInferenceEvent(
      requestId: json['request_id'] as String? ?? '',
      type: type,
      chunk: json['chunk'] as String? ?? '',
      textAccumulation: textAccumulation,
      finalResponse: switch (type) {
        AiEdgeInferenceEventType.completed => textAccumulation,
        AiEdgeInferenceEventType.error =>
          json['message'] as String? ?? textAccumulation,
        AiEdgeInferenceEventType.fallback =>
          json['reason'] as String? ?? textAccumulation,
        _ => '',
      },
      message: json['message'] as String? ?? json['reason'] as String? ?? '',
      runtimeMode: json['runtime_mode'] as String? ?? '',
    );
  }

  bool get isTerminal =>
      type == AiEdgeInferenceEventType.completed ||
      type == AiEdgeInferenceEventType.error ||
      type == AiEdgeInferenceEventType.fallback;
}

AiEdgeInferenceEventType _parseInferenceEventType(String? raw) {
  return switch (raw) {
    'inference_started' => AiEdgeInferenceEventType.started,
    'inference_chunk' => AiEdgeInferenceEventType.chunk,
    'inference_completed' => AiEdgeInferenceEventType.completed,
    'inference_error' => AiEdgeInferenceEventType.error,
    'inference_fallback' => AiEdgeInferenceEventType.fallback,
    _ => AiEdgeInferenceEventType.unknown,
  };
}

class AiEdgeCapabilities {
  final bool supportedPlatform;
  final bool nativeBridgeAvailable;
  final bool localTtsAvailable;
  final bool offlineSpeechAvailable;
  final bool litertlmLibraryPresent;
  final String sdkVersion;
  final String modelStatus;
  final String modelPath;
  final String modelMessage;
  final String discoveredSourcePath;
  final List<String> supportedIntents;
  final String runtimeMode;

  const AiEdgeCapabilities({
    required this.supportedPlatform,
    required this.nativeBridgeAvailable,
    required this.localTtsAvailable,
    required this.offlineSpeechAvailable,
    required this.litertlmLibraryPresent,
    required this.sdkVersion,
    required this.modelStatus,
    required this.modelPath,
    required this.modelMessage,
    required this.discoveredSourcePath,
    required this.supportedIntents,
    required this.runtimeMode,
  });

  factory AiEdgeCapabilities.unsupported() {
    return const AiEdgeCapabilities(
      supportedPlatform: false,
      nativeBridgeAvailable: false,
      localTtsAvailable: false,
      offlineSpeechAvailable: false,
      litertlmLibraryPresent: false,
      sdkVersion: '',
      modelStatus: 'unsupported',
      modelPath: '',
      modelMessage: '',
      discoveredSourcePath: '',
      supportedIntents: <String>[],
      runtimeMode: 'unavailable',
    );
  }

  factory AiEdgeCapabilities.fromJson(Map<dynamic, dynamic> json) {
    return AiEdgeCapabilities(
      supportedPlatform: json['supported_platform'] == true,
      nativeBridgeAvailable: json['native_bridge_available'] == true,
      localTtsAvailable: json['local_tts_available'] == true,
      offlineSpeechAvailable: json['offline_speech_available'] == true,
      litertlmLibraryPresent: json['litertlm_library_present'] == true,
      sdkVersion: json['sdk_version'] as String? ?? '',
      modelStatus: json['model_status'] as String? ?? 'missing',
      modelPath: json['model_path'] as String? ?? '',
      modelMessage: json['model_message'] as String? ?? '',
      discoveredSourcePath: json['discovered_source_path'] as String? ?? '',
      supportedIntents: List<String>.from(json['supported_intents'] ?? const []),
      runtimeMode: json['runtime_mode'] as String? ?? 'heuristic',
    );
  }
}

class AiEdgeModelStatus {
  final String modelId;
  final String status;
  final String localPath;
  final String sourcePath;
  final String sdkVersion;
  final String message;

  const AiEdgeModelStatus({
    required this.modelId,
    required this.status,
    required this.localPath,
    required this.sourcePath,
    required this.sdkVersion,
    required this.message,
  });

  factory AiEdgeModelStatus.fromJson(Map<dynamic, dynamic> json) {
    return AiEdgeModelStatus(
      modelId: json['model_id'] as String? ?? 'gemma-3n-e2b-it',
      status: json['status'] as String? ?? 'missing',
      localPath: json['local_path'] as String? ?? '',
      sourcePath: json['source_path'] as String? ?? '',
      sdkVersion: json['sdk_version'] as String? ?? '',
      message: json['message'] as String? ?? '',
    );
  }
}

class AiEdgeService {
  AiEdgeService._internal();

  static final AiEdgeService instance = AiEdgeService._internal();
  static const MethodChannel _channel = MethodChannel('backpocket/ai_edge');
  static const EventChannel _events = EventChannel('backpocket/ai_edge/events');
  static const String defaultModelId = 'gemma-3n-e2b-it';

  factory AiEdgeService() => instance;

  bool get isAndroidNative =>
      !kIsWeb && defaultTargetPlatform == TargetPlatform.android;

  Future<AiEdgeCapabilities> getCapabilities() async {
    if (!isAndroidNative) return AiEdgeCapabilities.unsupported();
    try {
      final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
        'getCapabilities',
      );
      if (result == null) return AiEdgeCapabilities.unsupported();
      return AiEdgeCapabilities.fromJson(result);
    } catch (_) {
      return AiEdgeCapabilities.unsupported();
    }
  }

  Future<AiEdgeModelStatus> ensureModelInstalled({
    String modelId = defaultModelId,
  }) async {
    if (!isAndroidNative) {
      return const AiEdgeModelStatus(
        modelId: defaultModelId,
        status: 'unsupported',
        localPath: '',
        sourcePath: '',
        sdkVersion: '',
        message: 'Android-only in this release.',
      );
    }
    final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
      'ensureModelInstalled',
      {'model_id': modelId},
    );
    return AiEdgeModelStatus.fromJson(result ?? const {});
  }

  Future<AiEdgeModelStatus> importModelFromPath(
    String sourcePath, {
    String modelId = defaultModelId,
  }) async {
    if (!isAndroidNative) {
      return const AiEdgeModelStatus(
        modelId: defaultModelId,
        status: 'unsupported',
        localPath: '',
        sourcePath: '',
        sdkVersion: '',
        message: 'Android-only in this release.',
      );
    }
    final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
      'importModelFromPath',
      {'model_id': modelId, 'source_path': sourcePath},
    );
    return AiEdgeModelStatus.fromJson(result ?? const {});
  }

  Future<Map<String, dynamic>?> runIntentPipeline({
    required String transcript,
    required String screenContext,
    String? sessionId,
    String? requestId,
    Map<String, dynamic>? metadata,
  }) async {
    if (!isAndroidNative) return null;
    final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
      'runIntentPipeline',
      {
        'transcript': transcript,
        'screen_context': screenContext,
        'session_id': sessionId,
        'request_id': requestId,
        'metadata': metadata ?? const {},
      },
    );
    if (result == null) return null;
    return Map<String, dynamic>.from(result);
  }

  Stream<AiEdgeInferenceEvent> getInferenceStream(String? requestId) async* {
    if (!isAndroidNative) {
      return;
    }
    if (requestId == null || requestId.isEmpty) {
      return;
    }

    var textAccumulation = '';
    await for (final rawEvent
        in _events.receiveBroadcastStream().map((dynamic event) {
          return Map<String, dynamic>.from(event as Map);
        }).where((event) => event['request_id'] == requestId)) {
      final type = _parseInferenceEventType(rawEvent['type'] as String?);
      if (type == AiEdgeInferenceEventType.started) {
        textAccumulation = '';
      } else if (type == AiEdgeInferenceEventType.chunk) {
        textAccumulation += rawEvent['chunk'] as String? ?? '';
      }

      yield AiEdgeInferenceEvent.fromJson(
        rawEvent,
        textAccumulation: textAccumulation,
      );
    }
  }

  Future<String?> recognizeOfflineSpeech({String prompt = ''}) async {
    if (!isAndroidNative) return null;
    final result = await _channel.invokeMethod<Map<dynamic, dynamic>>(
      'recognizeOfflineSpeech',
      {'prompt': prompt},
    );
    if (result == null) return null;
    final error = result['error'] as String?;
    if (error != null && error.isNotEmpty) return null;
    return result['transcript'] as String?;
  }

  Future<bool> speakOffline(String text) async {
    if (!isAndroidNative || text.isEmpty) return false;
    final result = await _channel.invokeMethod<bool>(
      'speakOffline',
      {'text': text},
    );
    return result ?? false;
  }
}
