import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

const Color kBg = Color(0xFF0D0A07);

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
  final _companyNameController = TextEditingController();
  bool _loading = false;
  bool _generating = false;
  bool _generatingSocial = false;
  bool _generatingStory = false;

  // Generated content results
  String? _gbpPost;
  String? _facebookPost;
  String? _instagramCaption;
  String? _instagramHashtags;
  String? _storyTitle;
  String? _storyContent;
  String _selectedTheme = 'entrepreneurship';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _jobDescController.dispose();
    _suburbController.dispose();
    _companyNameController.dispose();
    super.dispose();
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

    setState(() { _generating = true; _gbpPost = null; });
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
        setState(() => _gbpPost = data['post'] as String?);
        _loadData();
      } else {
        _showSnack('Error: ${data['message']}', isError: true);
      }
    } catch (e) {
      setState(() => _generating = false);
      _showSnack('Error: $e', isError: true);
    }
  }

  Future<void> _generateFacebook() async {
    if (_jobDescController.text.isEmpty || _suburbController.text.isEmpty) {
      _showSnack('Enter job description and suburb first', isError: true);
      return;
    }
    setState(() { _generatingSocial = true; _facebookPost = null; });
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/marketing/facebook-post'),
        headers: headers,
        body: jsonEncode({
          'job_description': _jobDescController.text,
          'suburb': _suburbController.text,
        }),
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body);
      if (data['status'] == 'success') {
        setState(() => _facebookPost = data['post'] as String?);
        _loadData();
      } else {
        _showSnack('Error: ${data['message']}', isError: true);
      }
    } catch (e) {
      _showSnack('Facebook error: $e', isError: true);
    } finally {
      setState(() => _generatingSocial = false);
    }
  }

  Future<void> _generateInstagram() async {
    if (_jobDescController.text.isEmpty || _suburbController.text.isEmpty) {
      _showSnack('Enter job description and suburb first', isError: true);
      return;
    }
    setState(() { _generatingSocial = true; _instagramCaption = null; _instagramHashtags = null; });
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/marketing/instagram-caption'),
        headers: headers,
        body: jsonEncode({
          'job_description': _jobDescController.text,
          'suburb': _suburbController.text,
        }),
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body);
      if (data['status'] == 'success') {
        setState(() {
          _instagramCaption = data['caption'] as String?;
          _instagramHashtags = data['hashtags'] as String?;
        });
        _loadData();
      } else {
        _showSnack('Error: ${data['message']}', isError: true);
      }
    } catch (e) {
      _showSnack('Instagram error: $e', isError: true);
    } finally {
      setState(() => _generatingSocial = false);
    }
  }

  Future<void> _generateStory() async {
    setState(() { _generatingStory = true; _storyContent = null; _storyTitle = null; });
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/blog/startup-story'),
        headers: headers,
        body: jsonEncode({
          'company_name': _companyNameController.text.isNotEmpty
              ? _companyNameController.text
              : 'BackPocket',
          'theme': _selectedTheme,
        }),
      ).timeout(const Duration(seconds: 90));
      final data = jsonDecode(res.body);
      if (data['error'] != null) {
        _showSnack('Error: ${data['error']}', isError: true);
      } else {
        setState(() {
          _storyTitle = data['title'] as String?;
          _storyContent = data['content'] as String?;
        });
      }
    } catch (e) {
      _showSnack('Story error: $e', isError: true);
    } finally {
      setState(() => _generatingStory = false);
    }
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    _showSnack('Copied to clipboard');
  }

  void _showSnack(String msg, {bool isError = false}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: isError ? AppColors.red : AppColors.green,
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
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // GBP Post Generator
                const Text(
                  'GBP POST GENERATOR',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Draft a Google Business Profile post from a job',
                        style: TextStyle(color: AppColors.textDim, fontSize: 12),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _jobDescController,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText:
                              'Job description (e.g., Completed rewiring in Campbelltown)',
                          hintStyle: const TextStyle(color: AppColors.textMuted),
                          filled: true,
                          fillColor: AppColors.surface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: const BorderSide(color: AppColors.border),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _suburbController,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText: 'Suburb (e.g., Campbelltown)',
                          hintStyle: const TextStyle(color: AppColors.textMuted),
                          filled: true,
                          fillColor: AppColors.surface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: const BorderSide(color: AppColors.border),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.amber,
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
                      if (_gbpPost != null) ...[
                        const SizedBox(height: 16),
                        _buildResultCard(
                          icon: Icons.business,
                          color: AppColors.amber,
                          label: 'Google Business Post',
                          content: _gbpPost!,
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Growth Stats
                const Text(
                  'LOCAL SEO INSIGHTS',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                _buildInsights(),
                const SizedBox(height: 24),

                // Social Media Generator
                const Text(
                  'SOCIAL MEDIA',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                _buildSocialSection(),
                const SizedBox(height: 24),

                // Success Story / Blog Generator
                const Text(
                  'SUCCESS STORY',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                _buildStorySection(),
                const SizedBox(height: 24),

                // Recent Activity
                const Text(
                  'RECENT ACTIVITY',
                  style: TextStyle(
                    color: AppColors.amber,
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

  Widget _buildSocialSection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Reuse job description + suburb from GBP section above',
            style: TextStyle(color: AppColors.textMuted, fontSize: 11),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.facebook, size: 16),
                  label: _generatingSocial
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Facebook'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1877F2),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _generatingSocial ? null : _generateFacebook,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.camera_alt, size: 16),
                  label: _generatingSocial
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('Instagram'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFE1306C),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _generatingSocial ? null : _generateInstagram,
                ),
              ),
            ],
          ),
          if (_facebookPost != null) ...[
            const SizedBox(height: 16),
            _buildResultCard(
              icon: Icons.facebook,
              color: const Color(0xFF1877F2),
              label: 'Facebook Post',
              content: _facebookPost!,
            ),
          ],
          if (_instagramCaption != null) ...[
            const SizedBox(height: 12),
            _buildResultCard(
              icon: Icons.camera_alt,
              color: const Color(0xFFE1306C),
              label: 'Instagram Caption',
              content: '${_instagramCaption!}\n\n${_instagramHashtags ?? ''}',
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStorySection() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'AI-crafted success story ready for your website or newsletter',
            style: TextStyle(color: AppColors.textDim, fontSize: 12),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _companyNameController,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              hintText: 'Business name (optional)',
              hintStyle: const TextStyle(color: AppColors.textMuted),
              filled: true,
              fillColor: AppColors.surface,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: AppColors.border),
              ),
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _selectedTheme,
            dropdownColor: AppColors.surface,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              filled: true,
              fillColor: AppColors.surface,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: const BorderSide(color: AppColors.border),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            ),
            items: const [
              DropdownMenuItem(value: 'entrepreneurship', child: Text('Entrepreneurship')),
              DropdownMenuItem(value: 'community', child: Text('Community Impact')),
              DropdownMenuItem(value: 'quality', child: Text('Quality Craftsmanship')),
              DropdownMenuItem(value: 'technology', child: Text('Tech & Tradies')),
            ],
            onChanged: (v) => setState(() => _selectedTheme = v ?? 'entrepreneurship'),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: _generatingStory
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                  : const Icon(Icons.auto_stories, size: 18),
              label: Text(_generatingStory ? 'Generating...' : 'Generate Success Story'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.amber,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: _generatingStory ? null : _generateStory,
            ),
          ),
          if (_storyContent != null) ...[
            const SizedBox(height: 16),
            _buildResultCard(
              icon: Icons.article,
              color: AppColors.amber,
              label: _storyTitle ?? 'Success Story',
              content: _storyContent!,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildResultCard({
    required IconData icon,
    required Color color,
    required String label,
    required String content,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withAlpha(13),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(51)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 14),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
              GestureDetector(
                onTap: () => _copyToClipboard(content),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: color.withAlpha(26),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.copy, color: color, size: 12),
                      const SizedBox(width: 4),
                      Text('Copy', style: TextStyle(color: color, fontSize: 11)),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            content,
            style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.5),
          ),
        ],
      ),
    );
  }

  Widget _buildInsights() {
    final insights = _insights?['insights'] ?? {};

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          _InsightRow(
            icon: Icons.search,
            label: insights['local_search_impressions']?['label'] ?? 'Search',
            value: insights['local_search_impressions']?['value'] ?? '+22%',
          ),
          const Divider(color: AppColors.border),
          _InsightRow(
            icon: Icons.location_on,
            label: insights['maps_visibility']?['label'] ?? 'Maps',
            value: insights['maps_visibility']?['value'] ?? 'High',
            subtitle: insights['maps_visibility']?['area'],
          ),
          const Divider(color: AppColors.border),
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
          color: AppColors.card,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: const Center(
          child: Text(
            'No marketing activity yet',
            style: TextStyle(color: AppColors.textMuted),
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
                color: AppColors.card,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.amber.withAlpha(26),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.campaign, color: AppColors.amber, size: 16),
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
                            color: AppColors.textMuted,
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
                      color: AppColors.green.withAlpha(26),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      item['status'] ?? 'draft',
                      style: const TextStyle(color: AppColors.green, fontSize: 10),
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
                  style: const TextStyle(color: AppColors.textDim, fontSize: 12),
                ),
                if (subtitle != null)
                  Text(
                    subtitle!,
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 10),
                  ),
              ],
            ),
          ),
          Text(
            value,
            style: const TextStyle(color: AppColors.amber, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
