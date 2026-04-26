import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AgenticRagScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const AgenticRagScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _AgenticRagScreenState createState() => _AgenticRagScreenState();
}

class _AgenticRagScreenState extends State<AgenticRagScreen> {
  late ApiService _apiService;
  List<dynamic> _logs = [];
  bool _loading = true;
  bool _fetching = false;
  String? _error;
  Timer? _refreshTimer;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _fetchLogs();
    _refreshTimer = Timer.periodic(const Duration(seconds: 4), (_) => _fetchLogs());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchLogs() async {
    if (_fetching) return;
    _fetching = true;
    try {
      final data = await _apiService.getAgenticRagLogs();
      if (mounted) {
        setState(() {
          _logs = data['logs'] ?? [];
          _loading = false;
          _error = null;
        });
        if (_scrollController.hasClients) {
          _scrollController.jumpTo(0);
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString();
        });
      }
    } finally {
      _fetching = false;
    }
  }

  Color _lineColor(Map log) {
    final type = log['type'] as String? ?? 'info';
    final level = log['level'] as String? ?? 'INFO';
    if (level == 'ERROR' || level == 'CRITICAL') return const Color(0xFFFF6B6B);
    if (level == 'WARNING') return const Color(0xFFFFB347);
    switch (type) {
      case 'routing':     return const Color(0xFF00E5FF);
      case 'learned':     return const Color(0xFF69FF47);
      case 'model_call':  return const Color(0xFFB388FF);
      case 'triage':      return const Color(0xFFFFD54F);
      case 'error':       return const Color(0xFFFF6B6B);
      default:            return Colors.white54;
    }
  }

  String _prefix(Map log) {
    final type = log['type'] as String? ?? 'info';
    final level = log['level'] as String? ?? 'INFO';
    if (level == 'ERROR') return '[ERR]';
    if (level == 'WARNING') return '[WRN]';
    switch (type) {
      case 'routing':    return '[ROUTE]';
      case 'learned':    return '[LEARN]';
      case 'model_call': return '[MODEL]';
      case 'triage':     return '[TRIAGE]';
      default:           return '[INFO]';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          Expanded(child: _buildTerminal()),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      color: const Color(0xFF111111),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          const _Dot(color: Color(0xFFFF5F57)),
          const SizedBox(width: 6),
          const _Dot(color: Color(0xFFFFBD2E)),
          const SizedBox(width: 6),
          const _Dot(color: Color(0xFF28C840)),
          const SizedBox(width: 14),
          const Text(
            'backpocket-ai — pipeline logs',
            style: TextStyle(color: Colors.white38, fontSize: 12, fontFamily: 'monospace'),
          ),
          const Spacer(),
          if (_error != null && _logs.isNotEmpty)
            const Padding(
              padding: EdgeInsets.only(right: 8),
              child: _Dot(color: Color(0xFFFF6B6B)),
            ),
          if (_loading)
            const SizedBox(
              width: 10, height: 10,
              child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF69FF47)),
            )
          else
            GestureDetector(
              onTap: () { setState(() => _loading = true); _fetchLogs(); },
              child: const Icon(Icons.refresh, color: Colors.white24, size: 16),
            ),
          const SizedBox(width: 8),
          Text('${_logs.length} lines', style: const TextStyle(color: Colors.white24, fontSize: 10)),
        ],
      ),
    );
  }

  Widget _buildTerminal() {
    if (_error != null && _logs.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('connection refused', style: TextStyle(color: Color(0xFFFF6B6B), fontFamily: 'monospace', fontSize: 13)),
            const SizedBox(height: 6),
            Text(widget.serverUrl, style: const TextStyle(color: Colors.white24, fontFamily: 'monospace', fontSize: 11)),
          ],
        ),
      );
    }

    if (!_loading && _logs.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('\$ waiting for AI activity...', style: TextStyle(color: Colors.white24, fontFamily: 'monospace', fontSize: 13)),
            SizedBox(height: 6),
            Text('process an email or chat to see logs', style: TextStyle(color: Colors.white24, fontFamily: 'monospace', fontSize: 11)),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 20),
      itemCount: _logs.length,
      itemBuilder: (ctx, i) {
        final log = _logs[i] as Map;
        final ts = log['timestamp'] as String? ?? '';
        final msg = log['action'] as String? ?? '';
        final loggerName = (log['logger'] as String? ?? '').split('.').last;
        final color = _lineColor(log);
        final prefix = _prefix(log);

        return Padding(
          padding: const EdgeInsets.only(bottom: 3),
          child: RichText(
            text: TextSpan(
              style: const TextStyle(fontFamily: 'monospace', fontSize: 11, height: 1.5),
              children: [
                TextSpan(text: '$ts ', style: const TextStyle(color: Colors.white24)),
                TextSpan(text: '$prefix ', style: TextStyle(color: color, fontWeight: FontWeight.bold)),
                if (loggerName.isNotEmpty)
                  TextSpan(text: '[$loggerName] ', style: const TextStyle(color: Colors.white38)),
                TextSpan(text: msg, style: TextStyle(color: color == Colors.white54 ? Colors.white70 : color)),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Dot extends StatelessWidget {
  final Color color;
  const _Dot({required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 11, height: 11,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}
