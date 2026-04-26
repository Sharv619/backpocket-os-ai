import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../theme.dart';

class CoachScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const CoachScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<CoachScreen> createState() => _CoachScreenState();
}

class _CoachScreenState extends State<CoachScreen> {
  late ApiService _api;
  final _textCtrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String _error = '';

  static const _examples = [
    'I just wanted to check if maybe you could possibly review this when you get a chance?',
    'Hi, I think we should probably consider looking at the proposal again.',
    'Sorry to bother you but I was wondering if you might be available for a quick chat?',
  ];

  @override
  void initState() {
    super.initState();
    _api = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    super.dispose();
  }

  Future<void> _analyze() async {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() { _loading = true; _error = ''; _result = null; });
    try {
      final res = await _api.analyzeCoach(text);
      setState(() => _result = res);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  void _loadExample(String text) {
    _textCtrl.text = text;
    setState(() { _result = null; _error = ''; });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF071014), Color(0xFF0A1A10)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              color: Colors.transparent,
              padding: const EdgeInsets.only(bottom: 16),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('🎤 Communication Coach', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
                  SizedBox(height: 4),
                  Text('Paste your message — get a confidence score + power version.', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                ],
              ),
            ),

            // Input area
            Container(
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.04),
                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                borderRadius: BorderRadius.circular(12),
              ),
              child: TextField(
                controller: _textCtrl,
                maxLines: 6,
                style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.5),
                decoration: const InputDecoration(
                  hintText: 'Paste a message, email draft, or anything you\'d say to a client…',
                  hintStyle: TextStyle(color: AppColors.textMuted, fontSize: 13),
                  contentPadding: EdgeInsets.all(14),
                  border: InputBorder.none,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Example chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  const Text('Try: ', style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
                  const SizedBox(width: 6),
                  ..._examples.map((ex) => Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => _loadExample(ex),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: AppColors.amber.withValues(alpha: 0.1),
                          border: Border.all(color: AppColors.amber.withValues(alpha: 0.3)),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(ex.length > 30 ? '${ex.substring(0, 30)}…' : ex,
                            style: const TextStyle(color: AppColors.amber, fontSize: 10)),
                      ),
                    ),
                  )),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Analyze button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: _loading
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                    : const Icon(Icons.psychology),
                label: Text(_loading ? 'Analysing…' : 'Analyse Message', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: _loading ? null : _analyze,
              ),
            ),

            // Error
            if (_error.isNotEmpty) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: AppColors.red.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(8)),
                child: Text('⚠️ $_error', style: const TextStyle(color: AppColors.red, fontSize: 13)),
              ),
            ],

            // Results
            if (_result != null) ...[
              const SizedBox(height: 20),
              _ScoreBar(score: (_result!['score'] ?? _result!['confidence_score'] ?? 0) as num),
              const SizedBox(height: 16),
              if (_result!['authority_issues'] != null)
                _IssueSection(title: '⚡ Authority Issues', items: _result!['authority_issues'], color: AppColors.red),
              if (_result!['clarity_issues'] != null)
                _IssueSection(title: '🎯 Clarity Issues', items: _result!['clarity_issues'], color: AppColors.amber),
              if (_result!['empathy_score'] != null)
                _ScoreCard(label: 'Empathy Score', value: '${_result!['empathy_score']}/100', color: AppColors.green),
              if (_result!['power_version'] != null || _result!['improved_version'] != null) ...[
                const SizedBox(height: 8),
                _PowerVersionCard(text: _result!['power_version'] ?? _result!['improved_version'] ?? ''),
              ],
              if (_result!['feedback'] != null) ...[
                const SizedBox(height: 8),
                _FeedbackCard(text: _result!['feedback'].toString()),
              ],
            ],
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

class _ScoreBar extends StatelessWidget {
  final num score;
  const _ScoreBar({required this.score});

  Color get _color {
    if (score >= 80) return AppColors.green;
    if (score >= 60) return AppColors.amber;
    return AppColors.red;
  }

  String get _label {
    if (score >= 80) return 'Strong 💪';
    if (score >= 60) return 'Good — room to improve';
    return 'Needs work';
  }

  @override
  Widget build(BuildContext context) {
    final pct = (score / 100).clamp(0.0, 1.0);
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _color.withValues(alpha: 0.1),
        border: Border.all(color: _color.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            const Text('Confidence Score', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
            Text('${score.toInt()}/100', style: TextStyle(color: _color, fontWeight: FontWeight.w900, fontSize: 22)),
          ]),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct,
              backgroundColor: Colors.white.withValues(alpha: 0.1),
              valueColor: AlwaysStoppedAnimation<Color>(_color),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 8),
          Text(_label, style: TextStyle(color: _color, fontSize: 12)),
        ],
      ),
    );
  }
}

class _IssueSection extends StatelessWidget {
  final String title;
  final dynamic items;
  final Color color;
  const _IssueSection({required this.title, required this.items, required this.color});

  @override
  Widget build(BuildContext context) {
    final list = items is List ? items as List : [items.toString()];
    if (list.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 13)),
          const SizedBox(height: 6),
          ...list.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('• ', style: TextStyle(color: color)),
              Expanded(child: Text(item.toString(), style: const TextStyle(color: AppColors.textMuted, fontSize: 13))),
            ]),
          )),
        ],
      ),
    );
  }
}

class _ScoreCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _ScoreCard({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.08),
      border: Border.all(color: color.withValues(alpha: 0.2)),
      borderRadius: BorderRadius.circular(8),
    ),
    child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label, style: const TextStyle(color: Colors.white, fontSize: 13)),
      Text(value, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14)),
    ]),
  );
}

class _PowerVersionCard extends StatelessWidget {
  final String text;
  const _PowerVersionCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.green.withValues(alpha: 0.08),
        border: Border.all(color: AppColors.green.withValues(alpha: 0.3)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(children: [
            Icon(Icons.bolt, color: AppColors.green, size: 16),
            SizedBox(width: 6),
            Text('Power Version', style: TextStyle(color: AppColors.green, fontWeight: FontWeight.bold, fontSize: 13)),
          ]),
          const SizedBox(height: 10),
          Text(text, style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.6)),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              icon: const Icon(Icons.copy, size: 14),
              label: const Text('Copy', style: TextStyle(fontSize: 12)),
              style: TextButton.styleFrom(foregroundColor: AppColors.green, minimumSize: Size.zero, tapTargetSize: MaterialTapTargetSize.shrinkWrap),
              onPressed: () {
                Clipboard.setData(ClipboardData(text: text));
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Power version copied!'), backgroundColor: AppColors.green));
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _FeedbackCard extends StatelessWidget {
  final String text;
  const _FeedbackCard({required this.text});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha: 0.04),
      border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('📝 Coach Feedback', style: TextStyle(color: AppColors.textMuted, fontWeight: FontWeight.bold, fontSize: 12, letterSpacing: 0.5)),
        const SizedBox(height: 8),
        Text(text, style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.6)),
      ],
    ),
  );
}
