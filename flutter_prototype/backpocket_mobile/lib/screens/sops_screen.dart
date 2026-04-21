import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../services/api_service.dart';
import '../theme.dart';

class SopsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const SopsScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _SopsScreenState createState() => _SopsScreenState();
}

class _SopsScreenState extends State<SopsScreen> {
  late ApiService _apiService;
  List<dynamic> _sops = [];
  List<dynamic> _filteredSops = [];
  bool _loading = true;
  String _selectedCategory = 'All';

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _fetchSops();
  }

  Future<void> _fetchSops() async {
    try {
      final data = await _apiService.getSops();
      setState(() {
        _sops = data['sops'] ?? [];
        _filterSops();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
      });
      // Handle error
    }
  }

  void _filterSops() {
    if (_selectedCategory == 'All') {
      _filteredSops = _sops;
    } else {
      _filteredSops = _sops.where((sop) => sop['category'] == _selectedCategory).toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    final categories = ['All', 'System', 'Chat', 'Email', 'Instructions', 'Debug'];
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Wrap(
              spacing: 8.0,
              children: categories.map((category) {
                return ChoiceChip(
                  label: Text(category),
                  selected: _selectedCategory == category,
                  onSelected: (selected) {
                    setState(() {
                      _selectedCategory = category;
                      _filterSops();
                    });
                  },
                  backgroundColor: AppColors.card,
                  selectedColor: AppColors.amber,
                  labelStyle: TextStyle(color: _selectedCategory == category ? Colors.black : Colors.white),
                );
              }).toList(),
            ),
          ),
          Expanded(
            child: _loading
                ? Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _filteredSops.length,
                    itemBuilder: (context, index) {
                      final sop = _filteredSops[index];
                      return SopCard(sop: sop);
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class SopCard extends StatefulWidget {
  final dynamic sop;

  const SopCard({super.key, required this.sop});

  @override
  _SopCardState createState() => _SopCardState();
}

class _SopCardState extends State<SopCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    List<dynamic> steps = [];
    try {
      steps = jsonDecode(widget.sop['steps'] ?? '[]');
    } catch (e) {
      // ignore
    }

    return Card(
      color: AppColors.card,
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: ExpansionTile(
        title: Text(widget.sop['title'] ?? 'No Title', style: TextStyle(color: Colors.white)),
        subtitle: Text(widget.sop['description'] ?? '', style: TextStyle(color: AppColors.textDim)),
        children: steps.map<Widget>((step) => ListTile(
          leading: Icon(Icons.check_circle_outline, color: AppColors.amber),
          title: Text(step.toString(), style: TextStyle(color: AppColors.textMuted)),
        )).toList(),
        onExpansionChanged: (isExpanded) {
          setState(() {
            _isExpanded = isExpanded;
          });
        },
        initiallyExpanded: _isExpanded,
      ),
    );
  }
}
