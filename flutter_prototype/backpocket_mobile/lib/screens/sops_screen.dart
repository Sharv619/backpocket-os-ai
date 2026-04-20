import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

class SopsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const SopsScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<SopsScreen> createState() => _SopsScreenState();
}

class _SopsScreenState extends State<SopsScreen> {
  List<dynamic> _sops = [];
  bool _loading = true;
  String? _error;
  String _filter = 'All';
  final Set<String> _expanded = {};

  static const _filters = ['All', 'System', 'Chat', 'Email', 'Instructions', 'Debug'];

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/sops'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        _sops = data['sops'] as List? ?? [];
      } else {
        _error = 'Server error ${res.statusCode}';
      }
    } catch (e) {
      _error = 'Cannot reach server. Check Settings → Server URL.\n$e';
    }
    if (mounted) setState(() => _loading = false);
  }

  List<dynamic> get _filtered {
    if (_filter == 'All') return _sops;
    return _sops.where((s) {
      final cat = (s['category'] as String? ?? '').toLowerCase();
      return cat == _filter.toLowerCase();
    }).toList();
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
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
          : _error != null
              ? _buildError()
              : Column(
                  children: [
                    _buildFilters(),
                    Expanded(child: _buildList()),
                  ],
                ),
    );
  }

  Widget _buildFilters() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: _filters.map((f) {
            final selected = _filter == f;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: GestureDetector(
                onTap: () => setState(() => _filter = f),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                  decoration: BoxDecoration(
                    color: selected ? AppColors.amber : AppColors.card,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: selected ? AppColors.amber : AppColors.border,
                    ),
                  ),
                  child: Text(
                    f,
                    style: TextStyle(
                      color: selected ? AppColors.brown : AppColors.textDim,
                      fontSize: 12,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.normal,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildList() {
    final items = _filtered;
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.list_alt_outlined, color: AppColors.textMuted, size: 48),
            const SizedBox(height: 16),
            Text('No $_filter SOPs', style: const TextStyle(color: AppColors.textDim)),
            const SizedBox(height: 16),
            TextButton.icon(
              onPressed: () => setState(() => _filter = 'All'),
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Show all'),
              style: TextButton.styleFrom(foregroundColor: AppColors.amber),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      color: AppColors.amber,
      backgroundColor: AppColors.card,
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        itemCount: items.length,
        itemBuilder: (ctx, i) => _SopCard(
          sop: items[i],
          isExpanded: _expanded.contains(items[i]['id']?.toString()),
          onToggle: () {
            final key = items[i]['id']?.toString() ?? '';
            setState(() {
              if (_expanded.contains(key)) {
                _expanded.remove(key);
              } else {
                _expanded.add(key);
              }
            });
          },
        ),
      ),
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
            Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textDim, height: 1.5)),
            const SizedBox(height: 20),
            TextButton.icon(
              onPressed: _load,
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Retry'),
              style: TextButton.styleFrom(foregroundColor: AppColors.orange),
            ),
          ],
        ),
      ),
    );
  }
}

class _SopCard extends StatefulWidget {
  final dynamic sop;
  final bool isExpanded;
  final VoidCallback onToggle;

  const _SopCard({required this.sop, required this.isExpanded, required this.onToggle});

  @override
  State<_SopCard> createState() => _SopCardState();
}

class _SopCardState extends State<_SopCard> {
  List<dynamic>? _steps;

  @override
  void initState() {
    super.initState();
    _parseSteps();
  }

  void _parseSteps() {
    final raw = widget.sop['steps'];
    if (raw == null) {
      _steps = null;
      return;
    }
    try {
      if (raw is String) {
        _steps = List<dynamic>.from(jsonDecode(raw) as List);
      } else if (raw is List) {
        _steps = List<dynamic>.from(raw);
      }
    } catch (_) {
      _steps = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final category = widget.sop['category'] as String? ?? 'System';
    final color = _getCategoryColor(category);

    return GestureDetector(
      onTap: widget.onToggle,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: color.withAlpha(26),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      category.toUpperCase(),
                      style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                  const Spacer(),
                  Icon(
                    widget.isExpanded ? Icons.expand_less : Icons.expand_more,
                    color: AppColors.textMuted,
                    size: 20,
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 8),
              child: Text(
                widget.sop['title'] as String? ?? 'Untitled',
                style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w600),
              ),
            ),
            if (widget.sop['description'] != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                child: Text(
                  widget.sop['description'] as String,
                  style: const TextStyle(color: AppColors.textDim, fontSize: 13),
                  maxLines: widget.isExpanded ? null : 2,
                  overflow: widget.isExpanded ? null : TextOverflow.ellipsis,
                ),
              ),
            if (widget.isExpanded && _steps != null && _steps!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: _steps!.asMap().entries.map((e) {
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 22, height: 22,
                              decoration: BoxDecoration(
                                color: AppColors.amber.withAlpha(26),
                                shape: BoxShape.circle,
                              ),
                              child: Center(
                                child: Text(
                                  '${e.key + 1}',
                                  style: const TextStyle(color: AppColors.amber, fontSize: 11, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                e.value.toString(),
                                style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
                              ),
                            ),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Color _getCategoryColor(String cat) {
    switch (cat.toLowerCase()) {
      case 'system': return AppColors.red;
      case 'chat': return AppColors.amber;
      case 'email': return AppColors.green;
      case 'instructions': return AppColors.orange;
      case 'debug': return const Color(0xFF6B7280);
      default: return AppColors.textDim;
    }
  }
}