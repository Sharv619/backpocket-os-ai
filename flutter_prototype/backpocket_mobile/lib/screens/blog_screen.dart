import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class BlogScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const BlogScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<BlogScreen> createState() => _BlogScreenState();
}

class _BlogScreenState extends State<BlogScreen> with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF1A1008)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          Container(
            color: AppColors.surface,
            child: TabBar(
              controller: _tabCtrl,
              indicatorColor: AppColors.amber,
              labelColor: AppColors.amber,
              unselectedLabelColor: AppColors.textMuted,
              labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
              tabs: const [
                Tab(text: 'Generate Post'),
                Tab(text: 'Startup Story'),
                Tab(text: 'Library'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabCtrl,
              children: [
                _BlogGenerateTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
                _StartupStoryTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
                const _LibraryTab(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BlogGenerateTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const _BlogGenerateTab({required this.serverUrl, required this.apiKey});

  @override
  State<_BlogGenerateTab> createState() => _BlogGenerateTabState();
}

class _BlogGenerateTabState extends State<_BlogGenerateTab> {
  final _titleCtrl = TextEditingController();
  String _theme = 'entrepreneurship';
  bool _generating = false;
  Map<String, dynamic>? _result;
  String? _error;

  final _themes = ['entrepreneurship', 'innovation', 'leadership', 'growth'];

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _generate() async {
    final title = _titleCtrl.text.trim();
    if (title.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter a title')));
      return;
    }
    setState(() { _generating = true; _error = null; _result = null; });
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/blog/generate?title=${Uri.encodeComponent(title)}&theme=$_theme'),
        headers: _headers,
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (data.containsKey('error')) {
        setState(() { _error = data['error'] as String; _generating = false; });
      } else {
        setState(() { _result = data; _generating = false; });
      }
    } catch (e) {
      setState(() { _error = e.toString(); _generating = false; });
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('Generate Blog Post', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        TextField(
          controller: _titleCtrl,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: InputDecoration(
            labelText: 'Post Title',
            labelStyle: const TextStyle(color: AppColors.textMuted),
            hintText: 'e.g., The Art of Building',
            hintStyle: const TextStyle(color: AppColors.textMuted),
            filled: true,
            fillColor: AppColors.card,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.amber)),
          ),
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          value: _theme,
          dropdownColor: AppColors.card,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: InputDecoration(
            labelText: 'Theme',
            labelStyle: const TextStyle(color: AppColors.textMuted),
            filled: true,
            fillColor: AppColors.card,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
          ),
          items: _themes.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
          onChanged: (v) => setState(() => _theme = v ?? 'entrepreneurship'),
        ),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: _generating ? null : _generate,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: _generating
              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : const Text('Generate Post', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.red.withAlpha(30), borderRadius: BorderRadius.circular(8)),
            child: Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
          ),
        ],
        if (_result != null) ...[
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_result!['title'] as String? ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 8),
                Text(_result!['content'] as String? ?? '', style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.6)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _StartupStoryTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const _StartupStoryTab({required this.serverUrl, required this.apiKey});

  @override
  State<_StartupStoryTab> createState() => _StartupStoryTabState();
}

class _StartupStoryTabState extends State<_StartupStoryTab> {
  final _companyCtrl = TextEditingController();
  bool _generating = false;
  Map<String, dynamic>? _result;
  String? _error;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _generate() async {
    final name = _companyCtrl.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter a company name')));
      return;
    }
    setState(() { _generating = true; _error = null; _result = null; });
    try {
      final res = await http.post(
        Uri.parse('${widget.serverUrl}/api/blog/startup-story'),
        headers: _headers,
        body: jsonEncode({'company_name': name, 'theme': 'entrepreneurship'}),
      ).timeout(const Duration(seconds: 45));
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (data.containsKey('error')) {
        setState(() { _error = data['error'] as String; _generating = false; });
      } else {
        setState(() { _result = data; _generating = false; });
      }
    } catch (e) {
      setState(() { _error = e.toString(); _generating = false; });
    }
  }

  @override
  void dispose() {
    _companyCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const Text('Startup Stories', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        TextField(
          controller: _companyCtrl,
          style: const TextStyle(color: Colors.white, fontSize: 14),
          decoration: InputDecoration(
            labelText: 'Company Name',
            labelStyle: const TextStyle(color: AppColors.textMuted),
            hintText: 'Your Company Name',
            hintStyle: const TextStyle(color: AppColors.textMuted),
            filled: true,
            fillColor: AppColors.card,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.amber)),
          ),
        ),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: _generating ? null : _generate,
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 14),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          ),
          child: _generating
              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
              : const Text('Generate Story', style: TextStyle(fontWeight: FontWeight.bold)),
        ),
        if (_error != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppColors.red.withAlpha(30), borderRadius: BorderRadius.circular(8)),
            child: Text(_error!, style: const TextStyle(color: AppColors.red, fontSize: 13)),
          ),
        ],
        if (_result != null) ...[
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_result!['title'] as String? ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 4),
                if (_result!['company'] != null)
                  Text('Company: ${_result!['company']}', style: const TextStyle(color: AppColors.amber, fontSize: 11)),
                const SizedBox(height: 12),
                Text(_result!['content'] as String? ?? '', style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.6)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _LibraryTab extends StatelessWidget {
  const _LibraryTab();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_stories_outlined, color: AppColors.textMuted, size: 48),
          SizedBox(height: 16),
          Text('Blog Library', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text('Coming soon...', style: TextStyle(color: AppColors.textDim, fontSize: 13)),
        ],
      ),
    );
  }
}
