import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

class BlogScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const BlogScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _BlogScreenState createState() => _BlogScreenState();
}

class _BlogScreenState extends State<BlogScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: TabBar(
        controller: _tabController,
        tabs: const [
          Tab(text: 'Generate Blog Post'),
          Tab(text: 'Startup Stories'),
          Tab(text: 'Blog Library'),
        ],
        indicatorColor: AppColors.amber,
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          GenerateBlogTab(apiService: _apiService),
          StartupStoryTab(apiService: _apiService),
          const Center(child: Text('Blog library coming soon...', style: TextStyle(color: AppColors.textDim))),
        ],
      ),
    );
  }
}

class GenerateBlogTab extends StatefulWidget {
  final ApiService apiService;

  const GenerateBlogTab({super.key, required this.apiService});

  @override
  _GenerateBlogTabState createState() => _GenerateBlogTabState();
}

class _GenerateBlogTabState extends State<GenerateBlogTab> {
  final _titleController = TextEditingController();
  String _selectedTheme = 'entrepreneurship';
  Map<String, dynamic>? _generatedPost;
  bool _isLoading = false;

  void _generatePost() async {
    setState(() {
      _isLoading = true;
      _generatedPost = null;
    });
    try {
      final post = await widget.apiService.generateBlogPost(_titleController.text, _selectedTheme);
      setState(() {
        _generatedPost = post;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            controller: _titleController,
            decoration: const InputDecoration(labelText: 'Title'),
            style: const TextStyle(color: Colors.white),
          ),
          DropdownButton<String>(
            value: _selectedTheme,
            onChanged: (String? newValue) {
              setState(() {
                _selectedTheme = newValue!;
              });
            },
            items: <String>['entrepreneurship', 'innovation', 'leadership', 'growth']
                .map<DropdownMenuItem<String>>((String value) {
              return DropdownMenuItem<String>(
                value: value,
                child: Text(value),
              );
            }).toList(),
          ),
          ElevatedButton(
            onPressed: _isLoading ? null : _generatePost,
            child: _isLoading ? const CircularProgressIndicator() : const Text('Generate Post'),
          ),
          if (_generatedPost != null)
            Card(
              color: AppColors.card,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_generatedPost!['title'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    Text(_generatedPost!['created_at'], style: const TextStyle(color: AppColors.textMuted)),
                    const Divider(color: AppColors.border),
                    Text(_generatedPost!['content'], style: const TextStyle(color: Colors.white)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class StartupStoryTab extends StatefulWidget {
  final ApiService apiService;

  const StartupStoryTab({super.key, required this.apiService});

  @override
  _StartupStoryTabState createState() => _StartupStoryTabState();
}

class _StartupStoryTabState extends State<StartupStoryTab> {
  final _companyNameController = TextEditingController();
  Map<String, dynamic>? _generatedStory;
  bool _isLoading = false;

  void _generateStory() async {
    setState(() {
      _isLoading = true;
      _generatedStory = null;
    });
    try {
      final story = await widget.apiService.generateStartupStory(_companyNameController.text);
      setState(() {
        _generatedStory = story;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            controller: _companyNameController,
            decoration: const InputDecoration(labelText: 'Company Name'),
            style: const TextStyle(color: Colors.white),
          ),
          ElevatedButton(
            onPressed: _isLoading ? null : _generateStory,
            child: _isLoading ? const CircularProgressIndicator() : const Text('Generate Startup Story'),
          ),
          if (_generatedStory != null)
            Card(
              color: AppColors.card,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_generatedStory!['title'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    Text(_generatedStory!['created_at'], style: const TextStyle(color: AppColors.textMuted)),
                    const Divider(color: AppColors.border),
                    Text(_generatedStory!['content'], style: const TextStyle(color: Colors.white)),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
