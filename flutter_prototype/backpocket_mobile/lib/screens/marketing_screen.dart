import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

const Color kBg = Color(0xFF0D0A07);
const Color kSurface = Color(0xFF1A1208);
const Color kCard = Color(0xFF211708);
const Color kBorder = Color(0x22FFFFFF);
const Color kAmber = Color(0xFFFBBF24);
const Color kOrange = Color(0xFFF97316);
const Color kGreen = Color(0xFF22C55E);
const Color kRed = Color(0xFFEF4444);
const Color kTextDim = Color(0x99FFFFFF);
const Color kTextMuted = Color(0x44FFFFFF);

class MarketingScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const MarketingScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<MarketingScreen> createState() => _MarketingScreenState();
}

class _MarketingScreenState extends State<MarketingScreen> {
  Map<String, dynamic>? _insights;
  List<dynamic> _activity = [];
  final _jobDescController = TextEditingController();
  final _suburbController = TextEditingController();
  bool _loading = false;
  bool _generating = false;

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
      final insightsRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/marketing/insights'),
        headers: headers,
      );
      _insights = jsonDecode(insightsRes.body);

      final activityRes = await http.get(
        Uri.parse('${widget.serverUrl}/api/marketing/activity'),
        headers: headers,
      );
      _activity = jsonDecode(activityRes.body)['activity'] ?? [];
    } catch (e) {
      debugPrint('Marketing load error: $e');
    }
    setState(() => _loading = false);
  }

  Future<void> _generateGbpPost() async {
    if (_jobDescController.text.isEmpty || _suburbController.text.isEmpty) {
      _showSnack('Please enter job description and suburb', isError: true);
      return;
    }

    setState(() => _generating = true);
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };

    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/marketing/gbp-post'),
        headers: headers,
        body: jsonEncode({
          'job_description': _jobDescController.text,
          'suburb': _suburbController.text,
        }),
      );
      final data = jsonDecode(res.body);
      setState(() => _generating = false);

      if (data['status'] == 'success') {
        _showSnack('GBP Post generated!', isError: false);
        _jobDescController.clear();
        _suburbController.clear();
        _loadData();
      } else {
        _showSnack('Error: ${data['message']}', isError: true);
      }
    } catch (e) {
      setState(() => _generating = false);
      _showSnack('Error: $e', isError: true);
    }
  }

  void _showSnack(String msg, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: isError ? kRed : kGreen,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [kBg, Color(0xFF1A1008)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: kAmber))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // GBP Post Generator
                const Text(
                  'GBP POST GENERATOR',
                  style: TextStyle(
                    color: kAmber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: kCard,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: kBorder),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Draft a Google Business Profile post from a job',
                        style: TextStyle(color: kTextDim, fontSize: 12),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _jobDescController,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText:
                              'Job description (e.g., Completed rewiring in Campbelltown)',
                          hintStyle: const TextStyle(color: kTextMuted),
                          filled: true,
                          fillColor: kSurface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: const BorderSide(color: kBorder),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _suburbController,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText: 'Suburb (e.g., Campbelltown)',
                          hintStyle: const TextStyle(color: kTextMuted),
                          filled: true,
                          fillColor: kSurface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: const BorderSide(color: kBorder),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: kAmber,
                            foregroundColor: Colors.black,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                          onPressed: _generating ? null : _generateGbpPost,
                          child: _generating
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text(
                                  'Generate GBP Post',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Growth Stats
                const Text(
                  'LOCAL SEO INSIGHTS',
                  style: TextStyle(
                    color: kAmber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                _buildInsights(),
                const SizedBox(height: 24),

                // Recent Activity
                const Text(
                  'RECENT ACTIVITY',
                  style: TextStyle(
                    color: kAmber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                _buildActivity(),
              ],
            ),
    );
  }

  Widget _buildInsights() {
    final insights = _insights?['insights'] ?? {};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: kBorder),
      ),
      child: Column(
        children: [
          _InsightRow(
            icon: Icons.search,
            label: insights['local_search_impressions']?['label'] ?? 'Search',
            value: insights['local_search_impressions']?['value'] ?? '+22%',
          ),
          const Divider(color: kBorder),
          _InsightRow(
            icon: Icons.location_on,
            label: insights['maps_visibility']?['label'] ?? 'Maps',
            value: insights['maps_visibility']?['value'] ?? 'High',
            subtitle: insights['maps_visibility']?['area'],
          ),
          const Divider(color: kBorder),
          _InsightRow(
            icon: Icons.star,
            label: insights['pending_review_requests']?['label'] ?? 'Reviews',
            value: '${insights['pending_review_requests']?['value'] ?? 3}',
          ),
        ],
      ),
    );
  }

  Widget _buildActivity() {
    if (_activity.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: kBorder),
        ),
        child: const Center(
          child: Text(
            'No marketing activity yet',
            style: TextStyle(color: kTextMuted),
          ),
        ),
      );
    }

    return Column(
      children: _activity
          .map(
            (item) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: kCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: kBorder),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: kAmber.withAlpha(26),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.campaign, color: kAmber, size: 16),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['generated_post'] ?? 'GBP Post',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                          ),
                        ),
                        Text(
                          item['created_at']?.toString().split('.').first ?? '',
                          style: const TextStyle(
                            color: kTextMuted,
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: kGreen.withAlpha(26),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      item['status'] ?? 'draft',
                      style: const TextStyle(color: kGreen, fontSize: 10),
                    ),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}

class _InsightRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String? subtitle;

  const _InsightRow({
    required this.icon,
    required this.label,
    required this.value,
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
              color: kAmber.withAlpha(26),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(icon, color: kAmber, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(color: kTextDim, fontSize: 12),
                ),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: const TextStyle(color: kTextMuted, fontSize: 10),
                  ),
              ],
            ),
          ),
          Text(
            value,
            style: const TextStyle(color: kAmber, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
