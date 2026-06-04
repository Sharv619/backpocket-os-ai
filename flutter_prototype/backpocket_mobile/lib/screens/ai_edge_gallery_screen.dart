import 'package:flutter/material.dart';

import '../services/ai_edge_service.dart';
import '../theme.dart';

class AiEdgeGalleryScreen extends StatefulWidget {
  const AiEdgeGalleryScreen({super.key});

  @override
  State<AiEdgeGalleryScreen> createState() => _AiEdgeGalleryScreenState();
}

class _AiEdgeGalleryScreenState extends State<AiEdgeGalleryScreen> {
  final AiEdgeService _aiEdge = AiEdgeService();
  final TextEditingController _promptController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<_EdgeMessage> _messages = [];

  AiEdgeCapabilities _capabilities = AiEdgeCapabilities.unsupported();
  bool _loadingStatus = true;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  @override
  void dispose() {
    _promptController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _loadStatus() async {
    setState(() => _loadingStatus = true);
    final capabilities = await _aiEdge.getCapabilities();
    if (!mounted) return;
    setState(() {
      _capabilities = capabilities;
      _loadingStatus = false;
    });
  }

  Future<void> _sendPrompt() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty || _sending) return;

    _promptController.clear();
    setState(() {
      _messages.add(_EdgeMessage(role: _EdgeRole.user, text: prompt));
      _messages.add(
        const _EdgeMessage(
          role: _EdgeRole.assistant,
          text: 'Thinking locally...',
          pending: true,
        ),
      );
      _sending = true;
    });
    _scrollToBottom();

    final response = await _aiEdge.runLocalPrompt(prompt: prompt);
    if (!mounted) return;

    final status = response?['status'] as String? ?? 'error';
    final answer = response?['response'] as String? ?? '';
    final message = response?['message'] as String? ?? '';
    final runtime = response?['runtime_mode'] as String? ?? '';
    final text = answer.isNotEmpty
        ? answer
        : message.isNotEmpty
        ? message
        : 'No local response returned.';

    setState(() {
      _messages[_messages.length - 1] = _EdgeMessage(
        role: _EdgeRole.assistant,
        text: text,
        status: status,
        runtime: runtime,
      );
      _sending = false;
    });
    _scrollToBottom();
    await _loadStatus();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0D0A07), Color(0xFF151515)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _Header(
                capabilities: _capabilities,
                loading: _loadingStatus,
                onRefresh: _loadStatus,
              ),
              Expanded(
                child: _messages.isEmpty
                    ? _EmptyState(
                        supported: _capabilities.supportedPlatform,
                        modelStatus: _capabilities.modelStatus,
                      )
                    : ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
                        itemCount: _messages.length,
                        itemBuilder: (context, index) {
                          return _MessageBubble(message: _messages[index]);
                        },
                      ),
              ),
              _PromptBar(
                controller: _promptController,
                sending: _sending,
                onSend: _sendPrompt,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final AiEdgeCapabilities capabilities;
  final bool loading;
  final VoidCallback onRefresh;

  const _Header({
    required this.capabilities,
    required this.loading,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final ready =
        capabilities.modelStatus == 'ready' ||
        capabilities.runtimeMode == 'litertlm_streaming';
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 8, 12),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(bottom: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.amber.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: AppColors.amber.withValues(alpha: 0.45),
              ),
            ),
            child: const Icon(Icons.offline_bolt, color: AppColors.amber),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI Edge Gallery',
                  style: TextStyle(
                    color: AppColors.cream,
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  loading
                      ? 'Checking phone runtime...'
                      : '${capabilities.runtimeMode} | ${capabilities.modelStatus}',
                  style: TextStyle(
                    color: ready ? AppColors.green : AppColors.textMuted,
                    fontSize: 11,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: loading ? null : onRefresh,
            icon: loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      color: AppColors.amber,
                      strokeWidth: 2,
                    ),
                  )
                : const Icon(Icons.refresh, color: AppColors.textMuted),
            tooltip: 'Refresh',
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final bool supported;
  final String modelStatus;

  const _EmptyState({required this.supported, required this.modelStatus});

  @override
  Widget build(BuildContext context) {
    final text = !supported
        ? 'Run the Android build on a phone to use local LiteRT-LM.'
        : modelStatus == 'ready'
        ? 'Ask the on-device model anything. Prompts stay on the phone.'
        : 'Import a .litertlm model from Settings, then return here.';
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 48),
        const Icon(Icons.memory, color: AppColors.amber, size: 48),
        const SizedBox(height: 16),
        const Text(
          'Phone-local model lab',
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.cream,
            fontSize: 22,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          text,
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
        ),
        const SizedBox(height: 22),
        ...[
          'Summarise this job note in two bullets',
          'Rewrite this customer reply more professionally',
          'Extract client, job type, location, and budget from this text',
        ].map(
          (sample) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.border),
            ),
            child: Text(
              sample,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
          ),
        ),
      ],
    );
  }
}

class _PromptBar extends StatelessWidget {
  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;

  const _PromptBar({
    required this.controller,
    required this.sending,
    required this.onSend,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
      decoration: const BoxDecoration(
        color: AppColors.surface,
        border: Border(top: BorderSide(color: AppColors.border)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !sending,
              maxLines: null,
              minLines: 1,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              onSubmitted: (_) => onSend(),
              decoration: InputDecoration(
                hintText: 'Prompt the phone model...',
                hintStyle: const TextStyle(color: AppColors.textMuted),
                filled: true,
                fillColor: AppColors.card,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: const BorderSide(color: AppColors.amber),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          IconButton.filled(
            onPressed: sending ? null : onSend,
            icon: sending
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      color: Colors.black,
                      strokeWidth: 2,
                    ),
                  )
                : const Icon(Icons.send_rounded),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.amber,
              foregroundColor: Colors.black,
              disabledBackgroundColor: AppColors.card,
              disabledForegroundColor: AppColors.textMuted,
              fixedSize: const Size(46, 46),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final _EdgeMessage message;

  const _MessageBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.role == _EdgeRole.user;
    final status = message.status.isNotEmpty ? ' ${message.status}' : '';
    final runtime = message.runtime.isNotEmpty ? ' | ${message.runtime}' : '';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 560),
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser ? AppColors.amber : AppColors.card,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isUser ? AppColors.amber : AppColors.border,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message.text,
              style: TextStyle(
                color: isUser ? Colors.black : AppColors.cream,
                fontSize: 14,
                height: 1.35,
              ),
            ),
            if (!isUser && (status.isNotEmpty || runtime.isNotEmpty)) ...[
              const SizedBox(height: 8),
              Text(
                'local$status$runtime',
                style: const TextStyle(color: AppColors.textDim, fontSize: 10),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

enum _EdgeRole { user, assistant }

class _EdgeMessage {
  final _EdgeRole role;
  final String text;
  final String status;
  final String runtime;
  final bool pending;

  const _EdgeMessage({
    required this.role,
    required this.text,
    this.status = '',
    this.runtime = '',
    this.pending = false,
  });
}
