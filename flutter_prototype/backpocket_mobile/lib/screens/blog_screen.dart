import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../theme.dart';

class BlogScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const BlogScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<BlogScreen> createState() => _BlogScreenState();
}

class _BlogScreenState extends State<BlogScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  late final ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: AppColors.amber,
          labelColor: Colors.white,
          unselectedLabelColor: AppColors.textDim,
          tabs: const [
            Tab(text: 'Generate Blog Post'),
            Tab(text: 'Startup Stories'),
            Tab(text: 'Blog Library'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          GenerateBlogTab(apiService: _apiService),
          StartupStoryTab(apiService: _apiService),
          BlogLibraryTab(apiService: _apiService),
        ],
      ),
    );
  }
}

class GenerateBlogTab extends StatefulWidget {
  final ApiService apiService;

  const GenerateBlogTab({super.key, required this.apiService});

  @override
  State<GenerateBlogTab> createState() => _GenerateBlogTabState();
}

class _GenerateBlogTabState extends State<GenerateBlogTab> {
  final _titleController = TextEditingController();
  String _selectedTheme = 'entrepreneurship';
  Map<String, dynamic>? _generatedPost;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _generatePost() async {
    if (_titleController.text.trim().isEmpty) {
      setState(() => _error = 'Enter a title first.');
      return;
    }

    setState(() {
      _isLoading = true;
      _generatedPost = null;
      _error = null;
    });

    try {
      final post = await widget.apiService.generateBlogPost(
        _titleController.text.trim(),
        _selectedTheme,
      );
      setState(() {
        _generatedPost = post;
        _error = post['error']?.toString();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Blog generation failed: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(labelText: 'Title'),
            style: const TextStyle(color: Colors.white),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _selectedTheme,
            dropdownColor: AppColors.card,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(labelText: 'Theme'),
            onChanged: (newValue) {
              if (newValue == null) return;
              setState(() => _selectedTheme = newValue);
            },
            items: const [
              'entrepreneurship',
              'innovation',
              'leadership',
              'growth',
            ].map((value) {
              return DropdownMenuItem<String>(
                value: value,
                child: Text(value),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _generatePost,
              child: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Generate Post'),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.red)),
          ],
          if (_generatedPost != null && _error == null) ...[
            const SizedBox(height: 16),
            _BlogPreviewCard(item: _generatedPost!),
          ],
        ],
      ),
    );
  }
}

class StartupStoryTab extends StatefulWidget {
  final ApiService apiService;

  const StartupStoryTab({super.key, required this.apiService});

  @override
  State<StartupStoryTab> createState() => _StartupStoryTabState();
}

class _StartupStoryTabState extends State<StartupStoryTab> {
  final _companyNameController = TextEditingController();
  Map<String, dynamic>? _generatedStory;
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _companyNameController.dispose();
    super.dispose();
  }

  Future<void> _generateStory() async {
    if (_companyNameController.text.trim().isEmpty) {
      setState(() => _error = 'Enter a company name first.');
      return;
    }

    setState(() {
      _isLoading = true;
      _generatedStory = null;
      _error = null;
    });

    try {
      final story = await widget.apiService.generateStartupStory(
        _companyNameController.text.trim(),
      );
      setState(() {
        _generatedStory = story;
        _error = story['error']?.toString();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Startup story failed: $e';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _companyNameController,
            decoration: const InputDecoration(labelText: 'Company Name'),
            style: const TextStyle(color: Colors.white),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _generateStory,
              child: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Generate Startup Story'),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: AppColors.red)),
          ],
          if (_generatedStory != null && _error == null) ...[
            const SizedBox(height: 16),
            _BlogPreviewCard(item: _generatedStory!),
          ],
        ],
      ),
    );
  }
}

class BlogLibraryTab extends StatefulWidget {
  final ApiService apiService;

  const BlogLibraryTab({super.key, required this.apiService});

  @override
  State<BlogLibraryTab> createState() => _BlogLibraryTabState();
}

class _BlogLibraryTabState extends State<BlogLibraryTab> {
  List<dynamic> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadLibrary();
  }

  Future<void> _loadLibrary() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await widget.apiService.getBlogLibrary();
      setState(() {
        _items = (data['items'] as List?) ?? const [];
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Library load failed: $e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.amber),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(_error!, style: const TextStyle(color: AppColors.red)),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _loadLibrary,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    if (_items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'No blog posts yet.',
                style: TextStyle(color: AppColors.textDim),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: _loadLibrary,
                child: const Text('Refresh'),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.amber,
      onRefresh: _loadLibrary,
      child: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          return _BlogPreviewCard(item: _items[index] as Map<String, dynamic>);
        },
      ),
    );
  }
}

class _BlogPreviewCard extends StatelessWidget {
  final Map<String, dynamic> item;

  const _BlogPreviewCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final title = item['title']?.toString() ?? 'Untitled';
    final content = item['content']?.toString() ?? '';
    final theme = item['theme']?.toString();
    final createdAt = item['created_at']?.toString() ?? '';

    return Card(
      color: AppColors.card,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (theme != null && theme.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                theme,
                style: const TextStyle(
                  color: AppColors.amber,
                  fontSize: 12,
                ),
              ),
            ],
            if (createdAt.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                createdAt,
                style: const TextStyle(color: AppColors.textMuted),
              ),
            ],
            const Divider(color: AppColors.border),
            Text(
              content,
              style: const TextStyle(color: Colors.white, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
}
