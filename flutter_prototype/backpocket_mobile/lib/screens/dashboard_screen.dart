import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class DashboardScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const DashboardScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _status;
  List<dynamic> _workflowStages = [];
  Map<String, dynamic>? _currentStage;
  Map<String, dynamic>? _marketingInsights;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    try {
      // Load status
      final statusRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/status'),
        headers: headers,
      );
      _status = jsonDecode(statusRes.body);

      // Load workflow stages
      final stagesRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/workflow/stages'),
        headers: headers,
      );
      _workflowStages = jsonDecode(stagesRes.body)['stages'] ?? [];

      // Load current stage
      final currentRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/workflow/current'),
        headers: headers,
      );
      _currentStage = jsonDecode(currentRes.body);

      // Load marketing insights
      final insightsRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/marketing/insights'),
        headers: headers,
      );
      _marketingInsights = jsonDecode(insightsRes.body);
    } catch (e) {
      debugPrint('Dashboard load error: $e');
    }
    setState(() => _loading = false);
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  @override
  Widget build(BuildContext context) {
    final pendingCount = _status?['pending_count'] ?? 0;

    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF1A1008), Color(0xFF2D1A00)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(
              child: CircularProgressIndicator(color: AppColors.amber),
            )
          : RefreshIndicator(
              color: AppColors.amber,
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Greeting
                  Text(
                    '${_getGreeting()}, Steve.',
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Pip has prepared $pendingCount items for your review.',
                    style: const TextStyle(
                      color: AppColors.textDim,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Stats Row
                  _buildStatsRow(),
                  const SizedBox(height: 20),

                  // Job Pipeline
                  const Text(
                    'JOB PIPELINE',
                    style: TextStyle(
                      color: AppColors.amber,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildJobPipeline(),
                  const SizedBox(height: 20),

                  // Growth Stats (Marketing)
                  const Text(
                    'GROWTH STATS',
                    style: TextStyle(
                      color: AppColors.amber,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildGrowthStats(),
                ],
              ),
            ),
    );
  }

  Widget _buildStatsRow() {
    final pendingCount = _status?['pending_count'] ?? 0;

    return Row(
      children: [
        _StatPill(
          icon: Icons.email_outlined,
          label: 'Emails',
          count: pendingCount,
          color: AppColors.amber,
        ),
        const SizedBox(width: 8),
        _StatPill(
          icon: Icons.description_outlined,
          label: 'Docs',
          count: 0,
          color: AppColors.orange,
        ),
        const SizedBox(width: 8),
        _StatPill(
          icon: Icons.campaign_outlined,
          label: 'Posts',
          count: 0,
          color: AppColors.green,
        ),
        const SizedBox(width: 8),
        _StatPill(
          icon: Icons.check_circle_outline,
          label: 'Tasks',
          count: 0,
          color: Colors.purple,
        ),
      ],
    );
  }

  Widget _buildJobPipeline() {
    final currentStageNum = _currentStage?['current_stage'] ?? '1';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          // Stage indicators
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: _workflowStages.map((stage) {
                final stageNum = stage['stage_number'].toString();
                final isActive = stageNum == currentStageNum;
                final isPast =
                    _workflowStages.indexOf(stage) <
                    _workflowStages.indexWhere(
                      (s) => s['stage_number'].toString() == currentStageNum,
                    );

                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Column(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isActive
                              ? AppColors.amber
                              : (isPast
                                    ? AppColors.green.withAlpha(128)
                                    : AppColors.surface),
                          border: Border.all(
                            color: isActive
                                ? AppColors.amber
                                : (isPast ? AppColors.green : AppColors.border),
                            width: 2,
                          ),
                        ),
                        child: Center(
                          child: isPast
                              ? const Icon(
                                  Icons.check,
                                  color: AppColors.green,
                                  size: 20,
                                )
                              : Text(
                                  stageNum,
                                  style: TextStyle(
                                    color: isActive
                                        ? Colors.black
                                        : AppColors.textDim,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                        ),
                      ),
                      const SizedBox(height: 4),
                      SizedBox(
                        width: 60,
                        child: Text(
                          (stage['title'] as String).split(' ').first,
                          style: TextStyle(
                            fontSize: 10,
                            color: isActive
                                ? AppColors.amber
                                : AppColors.textMuted,
                          ),
                          textAlign: TextAlign.center,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 12),
          // Current stage title
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.amber.withAlpha(26),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.amber.withAlpha(77)),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.play_circle_outline,
                  color: AppColors.amber,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _currentStage?['stage_title'] ??
                        'Client Inquiry / Call for Quote',
                    style: const TextStyle(
                      color: AppColors.amber,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGrowthStats() {
    final insights = _marketingInsights?['insights'] ?? {};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          _GrowthItem(
            icon: Icons.search,
            label:
                insights['local_search_impressions']?['label'] ??
                'Local Search',
            value: insights['local_search_impressions']?['value'] ?? '+22%',
            trend: 'up',
          ),
          const Divider(color: AppColors.border),
          _GrowthItem(
            icon: Icons.location_on,
            label: insights['maps_visibility']?['label'] ?? 'Maps Visibility',
            value: insights['maps_visibility']?['value'] ?? 'High',
            subtitle:
                insights['maps_visibility']?['area'] ??
                'Campbelltown/Macarthur',
          ),
          const Divider(color: AppColors.border),
          _GrowthItem(
            icon: Icons.star,
            label:
                insights['pending_review_requests']?['label'] ??
                'Pending Reviews',
            value: '${insights['pending_review_requests']?['value'] ?? 3}',
          ),
        ],
      ),
    );
  }
}

class _StatPill extends StatelessWidget {
  final IconData icon;
  final String label;
  final int count;
  final Color color;

  const _StatPill({
    required this.icon,
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 4),
            Text(
              '$count',
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 18,
              ),
            ),
            Text(
              label,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }
}

class _GrowthItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String? trend;
  final String? subtitle;

  const _GrowthItem({
    required this.icon,
    required this.label,
    required this.value,
    this.trend,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.amber.withAlpha(26),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: AppColors.amber, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.textDim,
                    fontSize: 12,
                  ),
                ),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 10,
                    ),
                  ),
              ],
            ),
          ),
          Row(
            children: [
              Text(
                value,
                style: const TextStyle(
                  color: AppColors.amber,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (trend == 'up') const SizedBox(width: 4),
              if (trend == 'up')
                const Icon(Icons.trending_up, color: AppColors.green, size: 16),
            ],
          ),
        ],
      ),
    );
  }
}
