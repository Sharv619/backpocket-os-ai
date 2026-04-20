import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../theme.dart';

const Color kBg = Color(0xFF0D0A07);

class InstructionsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const InstructionsScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<InstructionsScreen> createState() => _InstructionsScreenState();
}

class _InstructionsScreenState extends State<InstructionsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 4, vsync: this);
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
          colors: [kBg, Color(0xFF1A1008)],
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
              labelStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
              tabs: const [
                Tab(text: 'General'),
                Tab(text: 'Email Triage'),
                Tab(text: 'Senders'),
                Tab(text: 'Categories'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabCtrl,
              children: [
                _GeneralInstructionsTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
                _EmailTriageTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
                _SenderRulesTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
                _CategoryRulesTab(serverUrl: widget.serverUrl, apiKey: widget.apiKey),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Tab 1: General Instructions (original content) ─────────────────────────
class _GeneralInstructionsTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  const _GeneralInstructionsTab({required this.serverUrl, required this.apiKey});
  @override
  State<_GeneralInstructionsTab> createState() => _GeneralInstructionsTabState();
}

class _GeneralInstructionsTabState extends State<_GeneralInstructionsTab> {
  List<dynamic> _instructions = [];
  bool _loading = true;
  final _newInstructionController = TextEditingController();
  String _selectedCategory = 'tone';

  @override
  void initState() {
    super.initState();
    _loadInstructions();
  }

  Future<void> _loadInstructions() async {
    setState(() => _loading = true);
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/instructions'),
        headers: headers,
      );
      final body = jsonDecode(res.body);
      if (body is Map && body['general_instructions'] is List) {
        _instructions = body['general_instructions'] as List;
      } else if (body is List) {
        _instructions = body;
      } else {
        _instructions = [];
      }
    } catch (e) {
      debugPrint('Load instructions error: $e');
    }
    setState(() => _loading = false);
  }

  Future<void> _addInstruction() async {
    if (_newInstructionController.text.isEmpty) return;
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      await http.post(
        Uri.parse('${widget.serverUrl}/api/instructions'),
        headers: headers,
        body: jsonEncode({
          'instruction_text': _newInstructionController.text,
          'category': _selectedCategory,
          'is_active': 1,
        }),
      );
      _newInstructionController.clear();
      _loadInstructions();
    } catch (e) {
      debugPrint('Add instruction error: $e');
    }
  }

  Future<void> _deleteInstruction(int id) async {
    final headers = {
      'Content-Type': 'application/json',
      if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
    };
    try {
      await http.delete(
        Uri.parse('${widget.serverUrl}/api/instructions/$id'),
        headers: headers,
      );
      _loadInstructions();
    } catch (e) {
      debugPrint('Delete error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
        : ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Text('ADD INSTRUCTION', style: TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.border)),
                child: Column(
                  children: [
                    TextField(
                      controller: _newInstructionController,
                      maxLines: 3,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        hintText: 'Enter instruction...',
                        hintStyle: const TextStyle(color: AppColors.textMuted),
                        filled: true,
                        fillColor: AppColors.surface,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: AppColors.border)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButton<String>(
                            value: _selectedCategory,
                            dropdownColor: AppColors.card,
                            style: const TextStyle(color: Colors.white),
                            items: const [
                              DropdownMenuItem(value: 'tone', child: Text('Tone')),
                              DropdownMenuItem(value: 'priority', child: Text('Priority')),
                              DropdownMenuItem(value: 'workflow', child: Text('Workflow')),
                              DropdownMenuItem(value: 'safety', child: Text('Safety')),
                            ],
                            onChanged: (v) => setState(() => _selectedCategory = v!),
                          ),
                        ),
                        const SizedBox(width: 12),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.amber, foregroundColor: Colors.black),
                          onPressed: _addInstruction,
                          child: const Text('Add', style: TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              const Text('YOUR INSTRUCTIONS', style: TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
              const SizedBox(height: 12),
              if (_instructions.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.border)),
                  child: const Center(child: Text('No instructions yet', style: TextStyle(color: AppColors.textMuted))),
                )
              else
                ...(_instructions).map((inst) => _InstructionCard(
                      instruction: inst,
                      onDelete: () => _deleteInstruction(inst['id']),
                    )),
            ],
          );
  }
}

class _InstructionCard extends StatelessWidget {
  final Map<String, dynamic> instruction;
  final VoidCallback onDelete;
  const _InstructionCard({required this.instruction, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final category = instruction['category'] ?? 'tone';
    final isActive = instruction['is_active'] == 1 || instruction['is_active'] == true;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isActive ? AppColors.amber.withAlpha(77) : AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(color: _getCategoryColor(category).withAlpha(26), borderRadius: BorderRadius.circular(6)),
            child: Text(category.toUpperCase(), style: TextStyle(color: _getCategoryColor(category), fontSize: 10, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(instruction['instruction_text'] ?? instruction['instruction'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
          ),
          IconButton(icon: const Icon(Icons.delete_outline, color: AppColors.red, size: 20), onPressed: onDelete),
        ],
      ),
    );
  }

  Color _getCategoryColor(String cat) {
    switch (cat) {
      case 'tone': return AppColors.amber;
      case 'priority': return AppColors.orange;
      case 'workflow': return AppColors.green;
      case 'safety': return AppColors.red;
      default: return AppColors.textDim;
    }
  }
}

// ─── Tab 2: Email Triage Rules ─────────────────────────────────────────────────
class _EmailTriageTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  const _EmailTriageTab({required this.serverUrl, required this.apiKey});
  @override
  State<_EmailTriageTab> createState() => _EmailTriageTabState();
}

class _EmailTriageTabState extends State<_EmailTriageTab> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/email-rules'),
        headers: {'Content-Type': 'application/json', if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey},
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        _data = jsonDecode(res.body) as Map<String, dynamic>;
      } else {
        _error = 'Server error ${res.statusCode}';
      }
    } catch (e) {
      _error = 'Cannot reach server. $e';
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
        : _error != null
            ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.textDim)))
            : RefreshIndicator(
                color: AppColors.amber,
                backgroundColor: AppColors.card,
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    const Text('Email Triage Rules', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 20),
                    // Tier cards
                    _tierCard(1, 'REPLY NEEDED', AppColors.red, 'Important client emails requiring immediate response'),
                    const SizedBox(height: 8),
                    _tierCard(2, 'REVIEW NEEDED', AppColors.orange, 'Non-urgent acknowledgments that need review'),
                    const SizedBox(height: 8),
                    _tierCard(3, 'FYI ONLY', AppColors.amber, 'Informational emails for reference'),
                    const SizedBox(height: 8),
                    _tierCard(4, 'ARCHIVE', const Color(0xFF6B7280), 'Portal updates and routine notifications'),
                    const SizedBox(height: 8),
                    _tierCard(5, 'LOW PRIORITY', const Color(0xFF374151), 'Newsletters, spam, promotional content'),
                    const SizedBox(height: 20),
                    // Golden senders
                    if (_data != null && (_data!['golden_senders'] as List?)?.isNotEmpty == true) ...[
                      const Text('Golden Senders', style: TextStyle(color: AppColors.amber, fontSize: 14, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      const Text('Always treated as Tier 1 (Urgent)', style: TextStyle(color: AppColors.textDim, fontSize: 12)),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.border)),
                        child: Column(
                          children: (_data!['golden_senders'] as List).map((sender) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Row(
                              children: [
                                const Icon(Icons.star, color: AppColors.amber, size: 16),
                                const SizedBox(width: 8),
                                Expanded(child: Text(sender.toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                              ],
                            ),
                          )).toList(),
                        ),
                      ),
                    ],
                    const SizedBox(height: 20),
                    // Processing layers
                    if (_data != null && (_data!['processing_layers'] as List?)?.isNotEmpty == true) ...[
                      const Text('Processing Layers', style: TextStyle(color: AppColors.amber, fontSize: 14, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      ...(_data!['processing_layers'] as List).asMap().entries.map((e) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)),
                        child: Row(
                          children: [
                            Container(
                              width: 24, height: 24,
                              decoration: BoxDecoration(color: AppColors.amber.withAlpha(26), shape: BoxShape.circle),
                              child: Center(child: Text('${e.key + 1}', style: const TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.bold))),
                            ),
                            const SizedBox(width: 12),
                            Expanded(child: Text(e.value.toString(), style: const TextStyle(color: Colors.white, fontSize: 13))),
                          ],
                        ),
                      )),
                    ],
                  ],
                ),
              );
  }

  Widget _tierCard(int tier, String label, Color color, String desc) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: color.withAlpha(15),
        borderRadius: BorderRadius.circular(12),
        border: Border(left: BorderSide(color: color, width: 3)),
      ),
      child: Row(
        children: [
          Container(
            width: 28, height: 28,
            decoration: BoxDecoration(color: color.withAlpha(38), shape: BoxShape.circle),
            child: Center(child: Text('$tier', style: TextStyle(color: color, fontWeight: FontWeight.bold))),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
                const SizedBox(height: 2),
                Text(desc, style: const TextStyle(color: AppColors.textDim, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Tab 3: Sender Rules ───────────────────────────────────────────────────────
class _SenderRulesTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  const _SenderRulesTab({required this.serverUrl, required this.apiKey});
  @override
  State<_SenderRulesTab> createState() => _SenderRulesTabState();
}

class _SenderRulesTabState extends State<_SenderRulesTab> {
  List<dynamic> _rules = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/sender-instructions'),
        headers: _headers,
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        _rules = data['instructions'] as List? ?? [];
      } else {
        _error = 'Server error ${res.statusCode}';
      }
    } catch (e) {
      _error = 'Cannot reach server. $e';
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _addRule(String email, String instructions, String category) async {
    try {
      await http.post(
        Uri.parse('${widget.serverUrl}/api/sender-instructions'),
        headers: _headers,
        body: jsonEncode({'sender_email': email, 'instructions': instructions, 'category': category}),
      );
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red));
    }
  }

  Future<void> _deleteRule(String email) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
        title: const Text('Delete Rule?', style: TextStyle(color: Colors.white)),
        content: Text('Remove rules for $email?', style: const TextStyle(color: AppColors.textDim)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.red),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await http.delete(
        Uri.parse('${widget.serverUrl}/api/sender-instructions/${Uri.encodeComponent(email)}'),
        headers: _headers,
      );
      _load();
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red));
    }
  }

  void _showAddDialog() {
    final emailCtrl = TextEditingController();
    final instrCtrl = TextEditingController();
    String category = 'general';
    showDialog(
      context: context,
      builder: (_) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          backgroundColor: AppColors.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
          title: const Text('Add Sender Rule', style: TextStyle(color: Colors.white)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: emailCtrl, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Sender Email', labelStyle: TextStyle(color: AppColors.textMuted), filled: true, fillColor: AppColors.card)),
              const SizedBox(height: 12),
              TextField(controller: instrCtrl, maxLines: 3, style: const TextStyle(color: Colors.white), decoration: const InputDecoration(labelText: 'Instructions', labelStyle: TextStyle(color: AppColors.textMuted), filled: true, fillColor: AppColors.card)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: category,
                dropdownColor: AppColors.card,
                style: const TextStyle(color: Colors.white),
                decoration: const InputDecoration(labelText: 'Category', labelStyle: TextStyle(color: AppColors.textMuted), filled: true, fillColor: AppColors.card),
                items: const [
                  DropdownMenuItem(value: 'general', child: Text('General')),
                  DropdownMenuItem(value: 'urgent', child: Text('Urgent')),
                  DropdownMenuItem(value: 'followup', child: Text('Follow-up')),
                  DropdownMenuItem(value: 'info', child: Text('Info')),
                ],
                onChanged: (v) => setDialogState(() => category = v ?? 'general'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel', style: TextStyle(color: AppColors.textMuted))),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.amber, foregroundColor: Colors.black),
              onPressed: () {
                if (emailCtrl.text.isNotEmpty && instrCtrl.text.isNotEmpty) {
                  _addRule(emailCtrl.text, instrCtrl.text, category);
                  Navigator.pop(ctx);
                }
              },
              child: const Text('Add', style: TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
        : _error != null
            ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.textDim)))
            : Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const Expanded(child: Text('Sender Rules', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold))),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.add, size: 18),
                          label: const Text('Add Rule'),
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.amber, foregroundColor: Colors.black),
                          onPressed: _showAddDialog,
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: _rules.isEmpty
                        ? const Center(child: Text('No sender rules yet', style: TextStyle(color: AppColors.textMuted)))
                        : RefreshIndicator(
                            color: AppColors.amber,
                            backgroundColor: AppColors.card,
                            onRefresh: _load,
                            child: ListView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                              itemCount: _rules.length,
                              itemBuilder: (ctx, i) {
                                final rule = _rules[i] as Map<String, dynamic>;
                                final email = rule['sender_email'] ?? '';
                                final instr = rule['instructions'] ?? '';
                                final cat = rule['category'] ?? 'general';
                                return Container(
                                  margin: const EdgeInsets.only(bottom: 10),
                                  padding: const EdgeInsets.all(14),
                                  decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.border)),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                            decoration: BoxDecoration(color: AppColors.orange.withAlpha(26), borderRadius: BorderRadius.circular(6)),
                                            child: Text(cat.toUpperCase(), style: const TextStyle(color: AppColors.orange, fontSize: 10, fontWeight: FontWeight.bold)),
                                          ),
                                          const Spacer(),
                                          IconButton(
                                            icon: const Icon(Icons.delete_outline, color: AppColors.red, size: 18),
                                            onPressed: () => _deleteRule(email.toString()),
                                            tooltip: 'Delete',
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 6),
                                      Text(email.toString(), style: const TextStyle(color: AppColors.amber, fontSize: 13, fontWeight: FontWeight.w600)),
                                      const SizedBox(height: 4),
                                      Text(instr.toString(), style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4)),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ),
                  ),
                ],
              );
  }
}

// ─── Tab 4: Category Rules (Document, Marketing, Client) ──────────────────────
class _CategoryRulesTab extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  const _CategoryRulesTab({required this.serverUrl, required this.apiKey});
  @override
  State<_CategoryRulesTab> createState() => _CategoryRulesTabState();
}

class _CategoryRulesTabState extends State<_CategoryRulesTab> {
  List<dynamic> _allRules = [];
  bool _loading = true;
  String? _error;
  String _categoryFilter = 'Document';

  final _categoryFilters = ['Document', 'Marketing', 'Client'];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final res = await http.get(
        Uri.parse('${widget.serverUrl}/api/instructions'),
        headers: {'Content-Type': 'application/json', if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey},
      ).timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final body = jsonDecode(res.body);
        if (body is Map && body['general_instructions'] is List) {
          _allRules = body['general_instructions'] as List;
        } else if (body is List) {
          _allRules = body;
        } else {
          _allRules = [];
        }
      } else {
        _error = 'Server error ${res.statusCode}';
      }
    } catch (e) {
      _error = 'Cannot reach server. $e';
    }
    if (mounted) setState(() => _loading = false);
  }

  List<dynamic> get _filtered {
    return _allRules.where((r) {
      final cat = (r['category'] as String? ?? '').toLowerCase();
      final filter = _categoryFilter.toLowerCase();
      if (filter == 'client') return cat.contains('client') || cat.contains('email - sender');
      return cat.contains(filter);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return _loading
        ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
        : _error != null
            ? Center(child: Text(_error!, style: const TextStyle(color: AppColors.textDim)))
            : Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: _categoryFilters.map((f) {
                          final selected = _categoryFilter == f;
                          return Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: GestureDetector(
                              onTap: () => setState(() => _categoryFilter = f),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                                decoration: BoxDecoration(
                                  color: selected ? AppColors.amber : AppColors.card,
                                  borderRadius: BorderRadius.circular(20),
                                  border: Border.all(color: selected ? AppColors.amber : AppColors.border),
                                ),
                                child: Text(f, style: TextStyle(color: selected ? AppColors.brown : AppColors.textDim, fontSize: 12, fontWeight: selected ? FontWeight.w700 : FontWeight.normal)),
                              ),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                  ),
                  Expanded(
                    child: _filtered.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(_getCategoryIcon(_categoryFilter), color: AppColors.textMuted, size: 40),
                                const SizedBox(height: 12),
                                Text('No $_categoryFilter rules yet', style: const TextStyle(color: AppColors.textMuted)),
                                const SizedBox(height: 4),
                                const Text('Add via Twin Instructions', style: TextStyle(color: AppColors.textDim, fontSize: 12)),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            color: AppColors.amber,
                            backgroundColor: AppColors.card,
                            onRefresh: _load,
                            child: ListView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                              itemCount: _filtered.length,
                              itemBuilder: (ctx, i) {
                                final rule = _filtered[i] as Map<String, dynamic>;
                                final text = rule['instruction_text'] ?? rule['instruction'] ?? '';
                                final cat = rule['category'] ?? '';
                                final isCritical = rule['is_critical'] == 1 || rule['is_critical'] == true;
                                return Container(
                                  margin: const EdgeInsets.only(bottom: 10),
                                  padding: const EdgeInsets.all(14),
                                  decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.border)),
                                  child: Row(
                                    children: [
                                      Icon(_getCategoryIcon(_categoryFilter), color: AppColors.orange, size: 18),
                                      const SizedBox(width: 12),
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: [
                                            Row(
                                              children: [
                                                Container(
                                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                  decoration: BoxDecoration(color: AppColors.orange.withAlpha(26), borderRadius: BorderRadius.circular(4)),
                                                  child: Text(cat.toUpperCase(), style: const TextStyle(color: AppColors.orange, fontSize: 9, fontWeight: FontWeight.bold)),
                                                ),
                                                if (isCritical) ...[
                                                  const SizedBox(width: 6),
                                                  Container(
                                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                    decoration: BoxDecoration(color: AppColors.red.withAlpha(26), borderRadius: BorderRadius.circular(4)),
                                                    child: const Text('CRITICAL', style: TextStyle(color: AppColors.red, fontSize: 9, fontWeight: FontWeight.bold)),
                                                  ),
                                                ],
                                              ],
                                            ),
                                            const SizedBox(height: 6),
                                            Text(text.toString(), style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4)),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                          ),
                  ),
                ],
              );
  }

  IconData _getCategoryIcon(String cat) {
    switch (cat) {
      case 'Document': return Icons.description_outlined;
      case 'Marketing': return Icons.campaign_outlined;
      case 'Client': return Icons.person_outline;
      default: return Icons.rule_outlined;
    }
  }
}