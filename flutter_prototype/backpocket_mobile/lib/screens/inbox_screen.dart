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
                onTap: _fetchPending,
                child: const Icon(Icons.refresh, color: AppColors.textMuted, size: 18),
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
    final tierLabel = _tierLabels[tier] ?? 'MEDIUM';
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
                      onTap: onApprove,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [AppColors.orange, Color(0xFFEA580C)],
                          ),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.check_circle_outline, color: Colors.white, size: 16),
                            SizedBox(width: 6),
                            Text(
                              'Approve & Send',
                              style: TextStyle(
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

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _doApprove() async {
    setState(() => _approving = true);
    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/approve'),
            headers: _headers,
            body: jsonEncode({
              'ref_id': widget.item['ref_id'],
              'note': 'approved via mobile detail view',
            }),
          )
          .timeout(const Duration(seconds: 15));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;

      final status = data['status'] as String? ?? '';
      if (status == 'approved' || status == 'demo') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              status == 'demo'
                  ? 'DEMO: Would have sent email'
                  : 'Email sent successfully',
            ),
            backgroundColor: AppColors.green,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
        widget.onApproved();
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(data['message'] as String? ?? 'Approval failed'),
            backgroundColor: AppColors.red,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppColors.red,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _approving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = widget.item['tier'] as int? ?? 3;
    final tierLabel = _tierLabels[tier] ?? 'MEDIUM';
    final tierColor = _tierColors[tier] ?? AppColors.amber;
    final preview = widget.item['preview'] as String? ?? '';

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
          'Review Draft',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.border),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
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
                  color: tierColor,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              widget.item['subject'] as String? ?? '',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.person_outline, color: AppColors.textMuted, size: 14),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    widget.item['sender'] as String? ?? '',
                    style: const TextStyle(color: AppColors.textDim, fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            const Text(
              'AI Draft Reply',
              style: TextStyle(
                color: AppColors.amber,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Text(
                preview.isNotEmpty ? preview : 'No preview available.',
                style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.6),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Full draft available in desktop dashboard',
              style: TextStyle(color: AppColors.textMuted, fontSize: 11),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: _approving ? null : _doApprove,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    gradient: _approving
                        ? null
                        : const LinearGradient(colors: [AppColors.orange, Color(0xFFEA580C)]),
                    color: _approving ? AppColors.surface : null,
                    borderRadius: BorderRadius.circular(14),
                    border: _approving ? Border.all(color: AppColors.border) : null,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_approving)
                        const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(color: AppColors.amber, strokeWidth: 2),
                        )
                      else
                        const Icon(Icons.check_circle, color: Colors.white, size: 20),
                      const SizedBox(width: 10),
                      Text(
                        _approving ? 'Sending...' : 'Approve & Send Email',
                        style: TextStyle(
                          color: _approving ? AppColors.textDim : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Center(
                    child: Text(
                      'Back to Inbox',
                      style: TextStyle(
                        color: AppColors.textDim,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ),
            ),
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
        'Approve & Send?',
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
