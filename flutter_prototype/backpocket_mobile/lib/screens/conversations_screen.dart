import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

class ConversationsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const ConversationsScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<ConversationsScreen> createState() => _ConversationsScreenState();
}

class _ConversationsScreenState extends State<ConversationsScreen> {
  late ApiService _api;
  List<dynamic> _conversations = [];
  bool _loading = false;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = ''; });
    try {
      final list = await _api.getConversations();
      setState(() => _conversations = list);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _delete(String id) async {
    try {
      await _api.deleteConversation(id);
      setState(() => _conversations.removeWhere((c) => c['id'].toString() == id));
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Conversation deleted'), backgroundColor: AppColors.green));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF0D0A14), Color(0xFF130A1F)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          Container(
            color: Colors.black45,
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('💬 Conversations', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
                    SizedBox(height: 4),
                    Text('Full chat history with Pip', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                  ],
                ),
                IconButton(
                  icon: const Icon(Icons.refresh, color: AppColors.amber),
                  onPressed: _load,
                  tooltip: 'Refresh',
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
                : _error.isNotEmpty
                    ? _ErrorView(error: _error, onRetry: _load)
                    : _conversations.isEmpty
                        ? const Center(child: Text('No conversations yet.\nStart chatting with Pip!', textAlign: TextAlign.center, style: TextStyle(color: AppColors.textMuted, fontSize: 14)))
                        : RefreshIndicator(
                            onRefresh: _load,
                            color: AppColors.amber,
                            child: ListView.builder(
                              padding: const EdgeInsets.all(12),
                              itemCount: _conversations.length,
                              itemBuilder: (context, i) {
                                final conv = _conversations[i];
                                return _ConversationCard(
                                  conv: conv,
                                  onTap: () => Navigator.push(context, MaterialPageRoute(
                                    builder: (_) => _ConversationDetailScreen(
                                      convId: conv['id'].toString(),
                                      title: conv['title'] ?? 'Conversation ${i + 1}',
                                      api: _api,
                                    ),
                                  )),
                                  onDelete: () => _confirmDelete(context, conv['id'].toString()),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, String id) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Delete conversation?', style: TextStyle(color: Colors.white)),
        content: const Text('This cannot be undone.', style: TextStyle(color: AppColors.textMuted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
          TextButton(
            onPressed: () { Navigator.pop(ctx); _delete(id); },
            child: const Text('Delete', style: TextStyle(color: AppColors.red)),
          ),
        ],
      ),
    );
  }
}

class _ConversationCard extends StatelessWidget {
  final dynamic conv;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _ConversationCard({required this.conv, required this.onTap, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final messageCount = conv['message_count'] ?? 0;
    final source = conv['source'] ?? 'chat';
    final updated = conv['updated_at'] ?? conv['created_at'] ?? '';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.04),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        onTap: onTap,
        leading: Container(
          width: 40, height: 40,
          decoration: BoxDecoration(
            color: AppColors.amber.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: const Center(child: Text('💬', style: TextStyle(fontSize: 18))),
        ),
        title: Text(
          conv['title'] ?? 'Untitled conversation',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14),
          maxLines: 1, overflow: TextOverflow.ellipsis,
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Row(children: [
            _Tag(label: source, color: AppColors.amber),
            const SizedBox(width: 8),
            Text('$messageCount msgs', style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
            if (updated.isNotEmpty) ...[
              const SizedBox(width: 8),
              Expanded(child: Text(_formatDate(updated), style: const TextStyle(color: AppColors.textMuted, fontSize: 11), overflow: TextOverflow.ellipsis)),
            ],
          ]),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.textMuted),
          onPressed: onDelete,
          tooltip: 'Delete',
        ),
      ),
    );
  }

  String _formatDate(String raw) {
    try {
      final dt = DateTime.parse(raw.replaceAll(' ', 'T'));
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inDays == 0) return 'Today';
      if (diff.inDays == 1) return 'Yesterday';
      if (diff.inDays < 7) return '${diff.inDays}d ago';
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return raw;
    }
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final Color color;
  const _Tag({required this.label, required this.color});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(color: color.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(4)),
    child: Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
  );
}

class _ConversationDetailScreen extends StatefulWidget {
  final String convId;
  final String title;
  final ApiService api;

  const _ConversationDetailScreen({required this.convId, required this.title, required this.api});

  @override
  State<_ConversationDetailScreen> createState() => _ConversationDetailScreenState();
}

class _ConversationDetailScreenState extends State<_ConversationDetailScreen> {
  List<dynamic> _messages = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await widget.api.getConversation(widget.convId);
      setState(() => _messages = data['messages'] ?? []);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red));
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgDark,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        title: Text(widget.title, style: const TextStyle(color: Colors.white, fontSize: 15), overflow: TextOverflow.ellipsis),
        iconTheme: const IconThemeData(color: AppColors.amber),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : _messages.isEmpty
              ? const Center(child: Text('No messages in this conversation.', style: TextStyle(color: AppColors.textMuted)))
              : ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: _messages.length,
                  itemBuilder: (context, i) {
                    final msg = _messages[i];
                    final isUser = (msg['role'] ?? '') == 'user';
                    return _MessageBubble(content: msg['content'] ?? '', isUser: isUser, timestamp: msg['created_at'] ?? '');
                  },
                ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final String content;
  final bool isUser;
  final String timestamp;

  const _MessageBubble({required this.content, required this.isUser, required this.timestamp});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isUser ? AppColors.amber.withValues(alpha: 0.25) : Colors.white.withValues(alpha: 0.06),
          border: Border.all(color: isUser ? AppColors.amber.withValues(alpha: 0.4) : Colors.white.withValues(alpha: 0.08)),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(12),
            topRight: const Radius.circular(12),
            bottomLeft: Radius.circular(isUser ? 12 : 2),
            bottomRight: Radius.circular(isUser ? 2 : 12),
          ),
        ),
        child: Column(
          crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            Text(content, style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5)),
            if (timestamp.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(_formatTime(timestamp), style: const TextStyle(color: AppColors.textMuted, fontSize: 10)),
            ],
          ],
        ),
      ),
    );
  }

  String _formatTime(String raw) {
    try {
      final dt = DateTime.parse(raw.replaceAll(' ', 'T'));
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return '';
    }
  }
}

class _ErrorView extends StatelessWidget {
  final String error;
  final VoidCallback onRetry;
  const _ErrorView({required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) => Center(
    child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      const Text('⚠️ Error', style: TextStyle(color: Colors.red, fontSize: 18, fontWeight: FontWeight.bold)),
      const SizedBox(height: 12),
      Text(error, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, fontSize: 13)),
      const SizedBox(height: 20),
      ElevatedButton.icon(icon: const Icon(Icons.refresh), label: const Text('Retry'), onPressed: onRetry, style: ElevatedButton.styleFrom(backgroundColor: AppColors.amber)),
    ]),
  );
}
