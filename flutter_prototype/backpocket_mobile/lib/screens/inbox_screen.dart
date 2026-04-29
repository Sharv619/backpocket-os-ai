import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

const _tierLabels = {1: 'URGENT', 2: 'HIGH', 3: 'MEDIUM', 4: 'LOW', 5: 'SPAM'};
const _tierColors = {
  1: AppColors.red,
  2: AppColors.orange,
  3: AppColors.amber,
  4: Color(0xFF6B7280),
  5: Color(0xFF374151),
};

class InboxScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const InboxScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchPending();
  }

  @override
  void didUpdateWidget(InboxScreen old) {
    super.didUpdateWidget(old);
    if (old.serverUrl != widget.serverUrl || old.apiKey != widget.apiKey) {
      _fetchPending();
    }
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _fetchPending() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await http
          .get(
            Uri.parse('${widget.serverUrl}/api/mobile/pending'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        setState(() {
          _items = List<Map<String, dynamic>>.from(
            (data['items'] as List? ?? []).map(
              (e) => Map<String, dynamic>.from(e as Map),
            ),
          );
          _loading = false;
        });
      } else {
        setState(() {
          _error = 'Server error ${res.statusCode}';
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Cannot reach server.\nCheck Settings → Server URL.\n\n$e';
        _loading = false;
      });
    }
  }

  Future<void> _manualSync() async {
    setState(() => _loading = true);
    try {
      // Trigger background poll on server
      await http.get(Uri.parse('${widget.serverUrl}/run-poll'), headers: _headers);
      
      // Wait a moment for processing, then fetch updated list
      await Future.delayed(const Duration(seconds: 2));
      await _fetchPending();
      
      _showSnack('Syncing complete', success: true);
    } catch (e) {
      _showSnack('Sync error: $e', success: false);
      setState(() => _loading = false);
    }
  }

  Future<void> _approve(String refId, String sender, String subject) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => _ApproveDialog(sender: sender, subject: subject),
    );
    if (confirmed != true) return;

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/approve'),
            headers: _headers,
            body: jsonEncode({'ref_id': refId, 'note': 'approved via mobile'}),
          )
          .timeout(const Duration(seconds: 15));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;

      final status = data['status'] as String? ?? '';
      if (status == 'approved' || status == 'demo') {
        _showSnack(
          status == 'demo'
              ? 'DEMO: Would send to $sender'
              : 'Email sent to $sender',
          success: true,
        );
        setState(() => _items.removeWhere((i) => i['ref_id'] == refId));
      } else {
        _showSnack(
          data['message'] as String? ?? 'Approval failed',
          success: false,
        );
      }
    } catch (e) {
      if (mounted) _showSnack('Error: $e', success: false);
    }
  }

  void _showSnack(String msg, {required bool success}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: success ? AppColors.green : AppColors.red,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void _openDetail(Map<String, dynamic> item) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ApprovalDetailScreen(
          item: item,
          serverUrl: widget.serverUrl,
          apiKey: widget.apiKey,
          onApproved: () {
            setState(
              () => _items.removeWhere((i) => i['ref_id'] == item['ref_id']),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF1A1008), Color(0xFF2D1A00)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : _error != null
          ? _buildError()
          : _items.isEmpty
          ? _buildEmpty()
          : _buildList(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_outlined, color: AppColors.textMuted, size: 48),
            const SizedBox(height: 16),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textDim, height: 1.5),
            ),
            const SizedBox(height: 20),
            _textBtn('Retry', AppColors.orange, _fetchPending),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('All clear', style: TextStyle(fontSize: 32, color: AppColors.amber)),
          const SizedBox(height: 12),
          const Text(
            'No pending approvals.',
            style: TextStyle(color: AppColors.textDim),
          ),
          const SizedBox(height: 20),
          _textBtn('Refresh', AppColors.surface, _fetchPending),
        ],
      ),
    );
  }

  Widget _buildList() {
    return RefreshIndicator(
      color: AppColors.amber,
      backgroundColor: AppColors.card,
      onRefresh: _fetchPending,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${_items.length} pending approval${_items.length == 1 ? "" : "s"}',
                  style: const TextStyle(color: AppColors.textDim, fontSize: 13),
                ),
              ),
              GestureDetector(
                onTap: _manualSync,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.amber.withAlpha(30),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.amber.withAlpha(100)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.sync, color: AppColors.amber, size: 14),
                      SizedBox(width: 4),
                      Text('Sync Now', style: TextStyle(color: AppColors.amber, fontSize: 11, fontWeight: FontWeight.bold)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ..._items.map(
            (item) => _InboxCard(
              item: item,
              onApprove: () => _approve(
                item['ref_id'] as String? ?? '',
                item['sender'] as String? ?? '',
                item['subject'] as String? ?? '',
              ),
              onTap: () => _openDetail(item),
            ),
          ),
        ],
      ),
    );
  }

  Widget _textBtn(String label, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Text(
          label,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}

class _InboxCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback onApprove;
  final VoidCallback onTap;

  const _InboxCard({required this.item, required this.onApprove, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final tier = item['tier'] as int? ?? 3;
    final demoItem = item['is_demo_item'] == true;
    final tierLabel = demoItem ? 'DEMO' : (_tierLabels[tier] ?? 'MEDIUM');
    final tierColor = _tierColors[tier] ?? AppColors.amber;
    final ageHours = (item['age_hours'] as num?)?.toDouble() ?? 0.0;
    final preview = item['preview'] as String? ?? '';

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 0),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: tierColor.withAlpha(38),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: tierColor.withAlpha(102)),
                    ),
                    child: Text(
                      tierLabel,
                      style: TextStyle(
                        color: tierColor,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatAge(ageHours),
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 0),
              child: Text(
                item['sender'] as String? ?? 'Unknown',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 2, 14, 0),
              child: Text(
                item['subject'] as String? ?? '',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: AppColors.amber, fontSize: 13),
              ),
            ),
            if (preview.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
                child: Text(
                  preview,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppColors.textDim, fontSize: 12, height: 1.4),
                ),
              ),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
              child: Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: demoItem ? onTap : onApprove,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        decoration: BoxDecoration(
                          gradient: demoItem
                              ? const LinearGradient(
                                  colors: [AppColors.surface, Color(0xFF3B2A18)],
                                )
                              : const LinearGradient(
                                  colors: [AppColors.orange, Color(0xFFEA580C)],
                                ),
                          borderRadius: BorderRadius.circular(10),
                          border: demoItem ? Border.all(color: AppColors.border) : null,
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              demoItem ? Icons.visibility_outlined : Icons.check_circle_outline,
                              color: Colors.white,
                              size: 16,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              demoItem ? 'Read Email' : 'Verify & Send',
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: onTap,
                    child: Container(
                      padding: const EdgeInsets.all(11),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: const Icon(Icons.open_in_new, color: AppColors.textDim, size: 16),
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

  String _formatAge(double hours) {
    if (hours < 1) return '${(hours * 60).round()}m ago';
    if (hours < 24) return '${hours.round()}h ago';
    return '${(hours / 24).round()}d ago';
  }
}

class ApprovalDetailScreen extends StatefulWidget {
  final Map<String, dynamic> item;
  final String serverUrl;
  final String apiKey;
  final VoidCallback onApproved;

  const ApprovalDetailScreen({
    super.key,
    required this.item,
    required this.serverUrl,
    required this.apiKey,
    required this.onApproved,
  });

  @override
  State<ApprovalDetailScreen> createState() => _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends State<ApprovalDetailScreen> {
  bool _approving = false;
  bool _archiving = false;
  bool _saving = false;
  bool _loadingDraft = true;
  late TextEditingController _draftCtrl;
  String _sender = '';
  String _subject = '';
  String _emailBody = '';

  bool get _isDemoItem => widget.item['is_demo_item'] == true;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  @override
  void initState() {
    super.initState();
    _sender = widget.item['sender'] as String? ?? '';
    _subject = widget.item['subject'] as String? ?? '';
    _emailBody = widget.item['email_body'] as String? ?? '';
    final existing = widget.item['draft_body'] as String? ??
        widget.item['preview'] as String? ?? '';
    _draftCtrl = TextEditingController(text: existing);
    if (_isDemoItem) {
      _loadingDraft = false;
    } else {
      _fetchDraft();
    }
  }

  @override
  void dispose() {
    _draftCtrl.dispose();
    super.dispose();
  }

  Future<void> _fetchDraft() async {
    final refId = widget.item['ref_id'] as String? ?? '';
    if (refId.isEmpty) {
      setState(() => _loadingDraft = false);
      return;
    }
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/draft/$refId'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      if (!mounted) return;
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      final draft = data['draft'] as Map<String, dynamic>?;
      if (draft != null) {
        final body = draft['draft_body'] as String? ?? '';
        if (body.isNotEmpty) _draftCtrl.text = body;
        _sender = draft['sender'] as String? ?? _sender;
        _subject = draft['subject'] as String? ?? _subject;
        _emailBody = draft['email_body'] as String? ?? _emailBody;
      }
    } catch (_) {}
    if (mounted) setState(() => _loadingDraft = false);
  }

  void _snack(String msg, {bool success = true}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: success ? AppColors.green : AppColors.red,
      behavior: SnackBarBehavior.floating,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ));
  }

  Future<void> _saveDraft() async {
    final text = _draftCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() => _saving = true);
    try {
      await http.post(
        Uri.parse('${widget.serverUrl}/api/revise'),
        headers: _headers,
        body: jsonEncode({
          'ref_id': widget.item['ref_id'],
          'new_draft': text,
          'feedback': 'Edited in app',
        }),
      ).timeout(const Duration(seconds: 10));
      _snack('Draft saved!');
    } catch (e) {
      _snack('Error saving draft: $e', success: false);
    }
    if (mounted) setState(() => _saving = false);
  }

  Future<void> _archive() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.border),
        ),
        title: const Text('Archive?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'This email will be archived and removed from pending.',
          style: TextStyle(color: AppColors.textDim),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF6B7280),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Archive'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _archiving = true);
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/archive'),
        headers: _headers,
        body: jsonEncode({'ref_id': widget.item['ref_id']}),
      ).timeout(const Duration(seconds: 10));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;
      if (data['status'] == 'success') {
        _snack('Email archived');
        widget.onApproved();
        Navigator.pop(context);
      } else {
        _snack(data['message'] as String? ?? 'Archive failed', success: false);
      }
    } catch (e) {
      _snack('Error: $e', success: false);
    }
    if (mounted) setState(() => _archiving = false);
  }

  Future<void> _doApprove() async {
    final text = _draftCtrl.text.trim();
    if (text.isEmpty) {
      _snack('Draft is empty', success: false);
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => _ApproveDialog(
        sender: _sender,
        subject: _subject,
      ),
    );
    if (confirmed != true) return;

    setState(() => _approving = true);
    try {
      // Save latest draft first
      await http.post(
        Uri.parse('${widget.serverUrl}/api/revise'),
        headers: _headers,
        body: jsonEncode({
          'ref_id': widget.item['ref_id'],
          'new_draft': text,
          'feedback': 'Final edit before send',
        }),
      ).timeout(const Duration(seconds: 10));

      // Then approve
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/approve'),
        headers: _headers,
        body: jsonEncode({'ref_id': widget.item['ref_id']}),
      ).timeout(const Duration(seconds: 15));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;

      final status = data['status'] as String? ?? '';
      if (status == 'success' || status == 'approved' || status == 'demo') {
        _snack(status == 'demo'
            ? 'DEMO: Would send to $_sender'
            : 'Email sent to $_sender');
        widget.onApproved();
        Navigator.pop(context);
      } else {
        _snack(data['message'] as String? ?? 'Send failed', success: false);
      }
    } catch (e) {
      _snack('Error: $e', success: false);
    }
    if (mounted) setState(() => _approving = false);
  }

  Widget _buildSuggestedActions(dynamic actionsData) {
    List<dynamic> actions = [];
    try {
      if (actionsData is String) {
        actions = jsonDecode(actionsData);
      } else if (actionsData is List) {
        actions = actionsData;
      }
    } catch (_) {}

    if (actions.isEmpty) return const SizedBox();

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: actions.map((a) {
        final label = a['label'] ?? a['action'] ?? 'Action';
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.green.withAlpha(128)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.auto_awesome, color: AppColors.green, size: 12),
              const SizedBox(width: 6),
              Text(
                label,
                style: const TextStyle(color: AppColors.green, fontSize: 11, fontWeight: FontWeight.w600),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tier = widget.item['tier'] as int? ?? 3;
    final tierLabel = _tierLabels[tier] ?? 'MEDIUM';
    final tierColor = _tierColors[tier] ?? AppColors.amber;
    final refId = widget.item['ref_id'] as String? ?? '';

    return Scaffold(
      backgroundColor: AppColors.bgDark,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: AppColors.amber, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Review Email',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        actions: [
          if (!_archiving && !_isDemoItem)
            IconButton(
              icon: const Icon(Icons.archive_outlined, color: AppColors.textMuted, size: 20),
              onPressed: _archive,
              tooltip: 'Archive',
            )
          else
            const Padding(
              padding: EdgeInsets.all(12),
              child: SizedBox(
                width: 20, height: 20,
                child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
              ),
            ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.border),
        ),
      ),
      body: _loadingDraft
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: tierColor.withAlpha(38),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: tierColor.withAlpha(102)),
                        ),
                        child: Text(
                          tierLabel,
                          style: TextStyle(
                            color: tierColor, fontSize: 11,
                            fontWeight: FontWeight.bold, letterSpacing: 0.5,
                          ),
                        ),
                      ),
                      const Spacer(),
                      if (refId.isNotEmpty)
                        Text(
                          'REF: $refId',
                          style: const TextStyle(color: AppColors.textMuted, fontSize: 10, fontFamily: 'monospace'),
                        ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _subject,
                    style: const TextStyle(
                      color: Colors.white, fontSize: 18,
                      fontWeight: FontWeight.bold, height: 1.3,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(
                        Icons.person_outline,
                        color: AppColors.textMuted,
                        size: 14,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          _sender,
                          style: const TextStyle(
                            color: AppColors.textDim,
                            fontSize: 13,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'AI Reasoning',
                    style: TextStyle(
                      color: AppColors.amber, fontSize: 12,
                      fontWeight: FontWeight.w600, letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Text(
                      widget.item['ai_reasoning']?.toString().isNotEmpty == true
                          ? widget.item['ai_reasoning']
                          : 'No reasoning provided.',
                      style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.5),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Original Email',
                    style: TextStyle(
                      color: AppColors.amber, fontSize: 12,
                      fontWeight: FontWeight.w600, letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: SelectableText(
                      _emailBody.trim().isNotEmpty
                          ? _emailBody.trim()
                          : 'Full email text is not available for this item yet.',
                      style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.5),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'AI Draft Reply (editable)',
                    style: TextStyle(
                      color: AppColors.amber, fontSize: 12,
                      fontWeight: FontWeight.w600, letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _draftCtrl,
                    maxLines: null,
                    minLines: 8,
                    readOnly: _isDemoItem,
                    style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.6),
                    decoration: InputDecoration(
                      filled: true,
                      fillColor: AppColors.card,
                      hintText: _isDemoItem
                          ? 'No AI draft stored for this live demo email.'
                          : 'No draft yet. Type a response...',
                      hintStyle: const TextStyle(color: AppColors.textMuted),
                      contentPadding: const EdgeInsets.all(16),
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
                  if (widget.item['suggested_actions']?.toString().isNotEmpty == true) ...[
                    const SizedBox(height: 20),
                    const Text(
                      'Suggested Next Steps',
                      style: TextStyle(
                        color: AppColors.amber, fontSize: 12,
                        fontWeight: FontWeight.w600, letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 10),
                    _buildSuggestedActions(widget.item['suggested_actions']),
                  ],
                  if (!_isDemoItem) ...[
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      child: GestureDetector(
                        onTap: _approving ? null : _doApprove,
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          decoration: BoxDecoration(
                            gradient: _approving ? null
                                : const LinearGradient(colors: [AppColors.orange, Color(0xFFEA580C)]),
                            color: _approving ? AppColors.surface : null,
                            borderRadius: BorderRadius.circular(14),
                            border: _approving ? Border.all(color: AppColors.border) : null,
                          ),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              if (_approving)
                                const SizedBox(width: 18, height: 18,
                                  child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2))
                              else
                                const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                              const SizedBox(width: 10),
                              Text(
                                _approving ? 'Sending...' : 'Verify & Send',
                                style: TextStyle(
                                  color: _approving ? AppColors.textDim : Colors.white,
                                  fontWeight: FontWeight.bold, fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Row(
                      children: [
                        Expanded(
                          child: GestureDetector(
                            onTap: _saving ? null : _saveDraft,
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: AppColors.amber.withAlpha(76),
                                ),
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  if (_saving)
                                    const SizedBox(
                                      width: 14,
                                      height: 14,
                                      child: CircularProgressIndicator(
                                        color: AppColors.amber,
                                        strokeWidth: 2,
                                      ),
                                    )
                                  else
                                    const Icon(
                                      Icons.save_outlined,
                                      color: AppColors.amber,
                                      size: 16,
                                    ),
                                  const SizedBox(width: 8),
                                  Text(
                                    _saving ? 'Saving...' : 'Save Draft',
                                    style: const TextStyle(
                                      color: AppColors.amber,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: GestureDetector(
                            onTap: _archive,
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 14),
                              decoration: BoxDecoration(
                                color: AppColors.surface,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(color: AppColors.border),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.archive_outlined,
                                    color: AppColors.textDim,
                                    size: 16,
                                  ),
                                  SizedBox(width: 8),
                                  Text(
                                    'Archive',
                                    style: TextStyle(
                                      color: AppColors.textDim,
                                      fontWeight: FontWeight.w600,
                                      fontSize: 13,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                  const SizedBox(height: 32),
                  const SizedBox(height: 16),
                ],
              ),
            ),
    );
  }
}

class _ApproveDialog extends StatelessWidget {
  final String sender;
  final String subject;

  const _ApproveDialog({required this.sender, required this.subject});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AppColors.border),
      ),
      title: const Text(
        'Verify & Send?',
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'This will send the AI draft to:',
            style: TextStyle(color: AppColors.textDim),
          ),
          const SizedBox(height: 8),
          Text(
            sender,
            style: const TextStyle(color: AppColors.amber, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            'Re: $subject',
            style: const TextStyle(color: AppColors.textDim, fontSize: 12),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          onPressed: () => Navigator.pop(context, true),
          child: const Text('Send It', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
      ],
    );
  }
}
