class VoiceUiAction {
  final String? navigateTo;
  final int? tabIndex;
  final dynamic highlightItem;
  final String? showModal;
  final bool refreshData;
  final int? filterTier;
  final bool? clearChat;

  VoiceUiAction({
    this.navigateTo,
    this.tabIndex,
    this.highlightItem,
    this.showModal,
    this.refreshData = false,
    this.filterTier,
    this.clearChat,
  });

  factory VoiceUiAction.fromJson(Map<String, dynamic> json) {
    return VoiceUiAction(
      navigateTo: json['navigate_to'],
      tabIndex: json['tab_index'],
      highlightItem: json['highlight_item'],
      showModal: json['show_modal'],
      refreshData: json['refresh_data'] ?? false,
      filterTier: json['filter_tier'],
      clearChat: json['clear_chat'],
    );
  }
}

class VoiceSessionState {
  final String sessionId;
  final String state;
  final String? intent;
  final Map<String, dynamic> collectedParams;
  final List<String> missingParams;
  final String? nextQuestion;
  final Map<String, dynamic> defaults;
  final Map<String, dynamic>? lastEntity;
  final int ttl;

  VoiceSessionState({
    required this.sessionId,
    required this.state,
    this.intent,
    this.collectedParams = const {},
    this.missingParams = const [],
    this.nextQuestion,
    this.defaults = const {},
    this.lastEntity,
    this.ttl = 300,
  });

  factory VoiceSessionState.fromJson(Map<String, dynamic> json) {
    return VoiceSessionState(
      sessionId: json['session_id'] ?? '',
      state: json['state'] ?? 'IDLE',
      intent: json['intent'],
      collectedParams: Map<String, dynamic>.from(json['collected_params'] ?? {}),
      missingParams: List<String>.from(json['missing_params'] ?? []),
      nextQuestion: json['next_question'],
      defaults: Map<String, dynamic>.from(json['defaults'] ?? {}),
      lastEntity: json['last_entity'],
      ttl: json['ttl'] ?? 300,
    );
  }

  bool get isCollecting => state == 'COLLECTING';
  bool get isConfirming => state == 'CONFIRMING';
  bool get isIdle => state == 'IDLE';
}

class VoiceCommandResponse {
  final String? intent;
  final double confidence;
  final String action;
  final Map<String, dynamic> result;
  final String speechResponse;
  final VoiceUiAction uiAction;
  final bool needsConfirmation;
  final String? followUpPrompt;
  final VoiceSessionState? sessionState;

  VoiceCommandResponse({
    this.intent,
    this.confidence = 0.0,
    this.action = 'display',
    this.result = const {},
    this.speechResponse = '',
    required this.uiAction,
    this.needsConfirmation = false,
    this.followUpPrompt,
    this.sessionState,
  });

  factory VoiceCommandResponse.fromJson(Map<String, dynamic> json) {
    return VoiceCommandResponse(
      intent: json['intent'],
      confidence: (json['confidence'] ?? 0.0).toDouble(),
      action: json['action'] ?? 'display',
      result: Map<String, dynamic>.from(json['result'] ?? {}),
      speechResponse: json['speech_response'] ?? '',
      uiAction: json['ui_action'] != null
          ? VoiceUiAction.fromJson(json['ui_action'])
          : VoiceUiAction(),
      needsConfirmation: json['needs_confirmation'] ?? false,
      followUpPrompt: json['follow_up_prompt'],
      sessionState: json['session_state'] != null
          ? VoiceSessionState.fromJson(json['session_state'])
          : null,
    );
  }

  bool get isError => result.containsKey('error');
  bool get needsMoreInput => action == 'collect' || action == 'clarify';
  bool get shouldNavigate => action == 'navigate' || uiAction.navigateTo != null;
}
