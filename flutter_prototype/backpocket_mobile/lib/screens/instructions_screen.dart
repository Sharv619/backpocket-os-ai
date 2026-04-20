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

class _InstructionsScreenState extends State<InstructionsScreen> {
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
                // Add new instruction
                const Text(
                  'ADD INSTRUCTION',
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
                    children: [
                      TextField(
                        controller: _newInstructionController,
                        maxLines: 3,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText:
                              'Enter instruction (e.g., Always be concise and professional...)',
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
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButton<String>(
                              value: _selectedCategory,
                              dropdownColor: AppColors.card,
                              style: const TextStyle(color: Colors.white),
                              items: const [
                                DropdownMenuItem(
                                  value: 'tone',
                                  child: Text('Tone'),
                                ),
                                DropdownMenuItem(
                                  value: 'priority',
                                  child: Text('Priority'),
                                ),
                                DropdownMenuItem(
                                  value: 'workflow',
                                  child: Text('Workflow'),
                                ),
                                DropdownMenuItem(
                                  value: 'safety',
                                  child: Text('Safety'),
                                ),
                              ],
                              onChanged: (v) =>
                                  setState(() => _selectedCategory = v!),
                            ),
                          ),
                          const SizedBox(width: 12),
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: AppColors.amber,
                              foregroundColor: Colors.black,
                            ),
                            onPressed: _addInstruction,
                            child: const Text(
                              'Add',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Instructions list
                const Text(
                  'YOUR INSTRUCTIONS',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 12),
                if (_instructions.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: AppColors.card,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Center(
                      child: Text(
                        'No instructions yet',
                        style: TextStyle(color: AppColors.textMuted),
                      ),
                    ),
                  )
                else
                  ..._instructions.map(
                    (inst) => _InstructionCard(
                      instruction: inst,
                      onDelete: () => _deleteInstruction(inst['id']),
                    ),
                  ),
              ],
            ),
    );
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
            decoration: BoxDecoration(
              color: _getCategoryColor(category).withAlpha(26),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              category.toUpperCase(),
              style: TextStyle(
                color: _getCategoryColor(category),
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              instruction['instruction_text'] ?? instruction['instruction'] ?? '',
              style: const TextStyle(color: Colors.white, fontSize: 13),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: AppColors.red, size: 20),
            onPressed: onDelete,
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String cat) {
    switch (cat) {
      case 'tone':
        return AppColors.amber;
      case 'priority':
        return AppColors.orange;
      case 'workflow':
        return AppColors.green;
      case 'safety':
        return AppColors.red;
      default:
        return AppColors.textDim;
    }
  }
}
