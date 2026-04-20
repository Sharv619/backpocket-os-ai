import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

const Color kBg = Color(0xFF0D0A07);

class _SlashCommand {
  final String command;
  final String description;
  final IconData icon;
  final bool autoSend;

  const _SlashCommand(this.command, this.description, this.icon, {this.autoSend = false});
}

const _commands = [
  _SlashCommand('/pending', 'Show pending approvals', Icons.inbox_outlined, autoSend: true),
  _SlashCommand('/approve ', 'Approve and send email (add ref)', Icons.check_circle_outline),
  _SlashCommand('/revise ', 'Revise draft (add ref + feedback)', Icons.edit_outlined),
  _SlashCommand('/coach ', 'Analyze draft tone & clarity', Icons.school_outlined),
  _SlashCommand('/status', 'System health check', Icons.monitor_heart_outlined, autoSend: true),
  _SlashCommand('/help', 'List all commands', Icons.help_outline, autoSend: true),
];

class TwinChatScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const TwinChatScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<TwinChatScreen> createState() => _TwinChatScreenState();
}

class _TwinChatScreenState extends State<TwinChatScreen> {
  final List<Map<String, String>> _messages = [];
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final FocusNode _focusNode = FocusNode();
  bool _sending = false;
  bool _showCommands = false;
  List<_SlashCommand> _filteredCommands = [];

  // Conversation history
  List<Map<String, dynamic>> _twinConvs = [];
  List<Map<String, dynamic>> _openConvs = [];
  bool _loadingHistory = false;
  String? _activeConvId;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  @override
  void initState() {
    super.initState();
    _ctrl.addListener(_onTextChanged);
    _loadConversations();
  }

  @override
  void dispose() {
    _ctrl.removeListener(_onTextChanged);
    _ctrl.dispose();
    _scroll.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _onTextChanged() {
    final text = _ctrl.text;
    if (text.startsWith('/')) {
      final query = text.toLowerCase();
      final matches = _commands.where((c) => c.command.startsWith(query)).toList();
      setState(() {
        _filteredCommands = matches;
        _showCommands = matches.isNotEmpty;
      });
    } else {
      if (_showCommands) setState(() => _showCommands = false);
    }
  }

  void _selectCommand(_SlashCommand cmd) {
    _ctrl.text = cmd.command;
    _ctrl.selection = TextSelection.fromPosition(TextPosition(offset: _ctrl.text.length));
    setState(() => _showCommands = false);
    if (cmd.autoSend) {
      _send();
    } else {
      _focusNode.requestFocus();
    }
  }

  Future<void> _loadConversations() async {
    setState(() => _loadingHistory = true);
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/conversations'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final all = (data['conversations'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
      if (mounted) {
        setState(() {
          _twinConvs = all.where((c) => c['source'] == 'twin').take(8).toList();
          _openConvs = all.where((c) => c['source'] == 'opencode').take(8).toList();
          _loadingHistory = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingHistory = false);
    }
  }

  Future<void> _loadConversation(String convId) async {
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/conversations/$convId'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final msgs = (data['messages'] as List? ?? [])
          .map((m) => {
                'role': (m['role'] as String? ?? 'assistant') == 'user' ? 'user' : 'assistant',
                'content': m['content'] as String? ?? m['text'] as String? ?? '',
              })
          .toList();
      if (mounted) {
        setState(() {
          _messages.clear();
          _messages.addAll(msgs);
          _activeConvId = convId;
        });
        _scrollToBottom();
        Navigator.pop(context); // close drawer
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Failed to load conversation: $e'),
          backgroundColor: AppColors.red,
          behavior: SnackBarBehavior.floating,
        ));
      }
    }
  }

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _sending = true;
      _showCommands = false;
    });
    _scrollToBottom();

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/chat'),
            headers: _headers,
            body: jsonEncode({'message': text}),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (mounted) {
        setState(() {
          _messages.add({
            'role': 'assistant',
            'content': data['response'] as String? ?? 'No response.',
          });
          _sending = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add({'role': 'assistant', 'content': 'Error: $e'});
          _sending = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _newChat() {
    setState(() {
      _messages.clear();
      _activeConvId = null;
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _formatTime(String? timestamp) {
    if (timestamp == null || timestamp.isEmpty) return '';
    try {
      final date = DateTime.parse(timestamp);
      final diff = DateTime.now().difference(date);
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      if (diff.inDays < 7) return '${diff.inDays}d ago';
      return '${date.month}/${date.day}';
    } catch (_) {
      return '';
    }
  }

  Widget _buildHistoryDrawer() {
    return Drawer(
      backgroundColor: AppColors.surface,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Chat History',
                      style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add, color: AppColors.amber, size: 20),
                    onPressed: () {
                      _newChat();
                      Navigator.pop(context);
                    },
                    tooltip: 'New Chat',
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh, color: AppColors.textMuted, size: 18),
                    onPressed: _loadConversations,
                  ),
                ],
              ),
            ),
            const Divider(color: AppColors.border, height: 1),
            if (_loadingHistory)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2)),
              )
            else
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  children: [
                    if (_twinConvs.isNotEmpty) ...[
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 8, 16, 4),
                        child: Text('Pip Chat', style: TextStyle(color: AppColors.amber, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
                      ),
                      ..._twinConvs.map((c) => _ConvTile(
                        title: c['title'] as String? ?? 'New Chat',
                        time: _formatTime(c['updated_at'] as String?),
                        active: c['id'].toString() == _activeConvId,
                        onTap: () => _loadConversation(c['id'].toString()),
                      )),
                    ],
                    if (_openConvs.isNotEmpty) ...[
                      const Padding(
                        padding: EdgeInsets.fromLTRB(16, 16, 16, 4),
                        child: Text('Open Chat', style: TextStyle(color: AppColors.amber, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
                      ),
                      ..._openConvs.map((c) => _ConvTile(
                        title: c['title'] as String? ?? 'New Chat',
                        time: _formatTime(c['updated_at'] as String?),
                        active: c['id'].toString() == _activeConvId,
                        onTap: () => _loadConversation(c['id'].toString()),
                      )),
                    ],
                    if (_twinConvs.isEmpty && _openConvs.isEmpty)
                      const Padding(
                        padding: EdgeInsets.all(24),
                        child: Center(
                          child: Text('No conversations yet', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
                        ),
                      ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      endDrawer: _buildHistoryDrawer(),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [kBg, Color(0xFF1A1008)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Column(
          children: [
            // Header bar with history toggle
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 8, 8),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Pip',
                      style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                  if (_messages.isNotEmpty)
                    IconButton(
                      icon: const Icon(Icons.add, color: AppColors.textMuted, size: 20),
                      onPressed: _newChat,
                      tooltip: 'New Chat',
                    ),
                  Builder(
                    builder: (ctx) => IconButton(
                      icon: const Icon(Icons.history, color: AppColors.textMuted, size: 20),
                      onPressed: () => Scaffold.of(ctx).openEndDrawer(),
                      tooltip: 'Chat History',
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: _messages.isEmpty
                  ? _buildWelcome()
                  : ListView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.all(16),
                      itemCount: _messages.length,
                      itemBuilder: (_, i) => _ChatBubble(msg: _messages[i]),
                    ),
            ),
            if (_sending)
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                child: Row(
                  children: [
                    SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
                    ),
                    SizedBox(width: 8),
                    Text('Pip is thinking...', style: TextStyle(color: AppColors.textDim, fontSize: 12)),
                  ],
                ),
              ),
            // Slash command dropdown
            if (_showCommands && _filteredCommands.isNotEmpty)
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                  boxShadow: [BoxShadow(color: Colors.black.withAlpha(100), blurRadius: 12, offset: const Offset(0, -4))],
                ),
                constraints: const BoxConstraints(maxHeight: 220),
                child: ListView(
                  shrinkWrap: true,
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  children: _filteredCommands.map((cmd) => InkWell(
                    onTap: () => _selectCommand(cmd),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      child: Row(
                        children: [
                          Icon(cmd.icon, color: AppColors.amber, size: 18),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  cmd.command.trim(),
                                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13, fontFamily: 'monospace'),
                                ),
                                Text(
                                  cmd.description,
                                  style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                ),
                              ],
                            ),
                          ),
                          if (cmd.autoSend)
                            const Icon(Icons.keyboard_return, color: AppColors.textMuted, size: 14),
                        ],
                      ),
                    ),
                  )).toList(),
                ),
              ),
            // Input area
            Container(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              decoration: const BoxDecoration(
                color: AppColors.surface,
                border: Border(top: BorderSide(color: AppColors.border)),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      focusNode: _focusNode,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                      maxLines: null,
                      onSubmitted: (_) => _send(),
                      decoration: InputDecoration(
                        hintText: 'Ask Pip anything... (type / for commands)',
                        hintStyle: const TextStyle(color: AppColors.textMuted),
                        filled: true,
                        fillColor: AppColors.card,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.border),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.border),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.amber, width: 1.5),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  GestureDetector(
                    onTap: _sending ? null : _send,
                    child: Container(
                      width: 44, height: 44,
                      decoration: BoxDecoration(
                        gradient: _sending ? null
                            : const LinearGradient(colors: [AppColors.orange, Color(0xFFEA580C)]),
                        color: _sending ? AppColors.card : null,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Icon(
                        Icons.send_rounded,
                        color: _sending ? AppColors.textMuted : Colors.white,
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildWelcome() {
    final suggestions = [
      'What emails need attention today?',
      'How many items are pending?',
      "Summarise today's inbox",
      '/status',
    ];
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 40),
        const Center(child: Text('\u{1f9e0}', style: TextStyle(fontSize: 48))),
        const SizedBox(height: 16),
        const Center(
          child: Text(
            'BackPocket Twin',
            style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
        ),
        const SizedBox(height: 8),
        const Center(
          child: Text(
            'Ask me anything about your inbox',
            style: TextStyle(color: AppColors.textDim, fontSize: 14),
          ),
        ),
        const SizedBox(height: 12),
        const Center(
          child: Text(
            'Type / for slash commands',
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
        ),
        const SizedBox(height: 32),
        ...suggestions.map(
          (s) => GestureDetector(
            onTap: () {
              _ctrl.text = s;
              _send();
            },
            child: Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  if (s.startsWith('/'))
                    const Padding(
                      padding: EdgeInsets.only(right: 8),
                      child: Icon(Icons.terminal, color: AppColors.amber, size: 14),
                    ),
                  Expanded(
                    child: Text(s, style: const TextStyle(color: AppColors.textDim, fontSize: 13)),
                  ),
                  const Icon(Icons.arrow_forward_ios, color: AppColors.textMuted, size: 12),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ConvTile extends StatelessWidget {
  final String title;
  final String time;
  final bool active;
  final VoidCallback onTap;

  const _ConvTile({required this.title, required this.time, required this.active, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        color: active ? AppColors.amber.withAlpha(20) : Colors.transparent,
        child: Row(
          children: [
            Expanded(
              child: Text(
                title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: active ? AppColors.amber : AppColors.textDim,
                  fontSize: 13,
                  fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(time, style: const TextStyle(color: AppColors.textMuted, fontSize: 10)),
          ],
        ),
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final Map<String, String> msg;

  const _ChatBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isUser = msg['role'] == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 28, height: 28,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [AppColors.amber, AppColors.orange]),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Center(
                child: Text('BP', style: TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 9)),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser ? AppColors.orange.withAlpha(51) : AppColors.card,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isUser ? 14 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 14),
                ),
                border: Border.all(
                  color: isUser ? AppColors.orange.withAlpha(76) : AppColors.border,
                ),
              ),
              child: _buildContent(msg['content'] ?? ''),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildContent(String text) {
    // Render bold (**text**) and italic (*text*)
    final spans = <InlineSpan>[];
    final boldRe = RegExp(r'\*\*(.*?)\*\*');
    int lastEnd = 0;
    for (final m in boldRe.allMatches(text)) {
      if (m.start > lastEnd) {
        spans.add(TextSpan(text: text.substring(lastEnd, m.start)));
      }
      spans.add(TextSpan(
        text: m.group(1),
        style: const TextStyle(fontWeight: FontWeight.bold),
      ));
      lastEnd = m.end;
    }
    if (lastEnd < text.length) {
      spans.add(TextSpan(text: text.substring(lastEnd)));
    }

    final isUser = msg['role'] == 'user';
    return RichText(
      text: TextSpan(
        style: TextStyle(
          color: isUser ? Colors.white : AppColors.textDim,
          fontSize: 13,
          height: 1.5,
        ),
        children: spans.isEmpty ? [TextSpan(text: text)] : spans,
      ),
    );
  }
}
