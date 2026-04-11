import 'dart:convert';
import 'package:flutter/material.dart';
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
      _instructions = jsonDecode(res.body) ?? [];
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
        Uri.parse('${widget.serverUrl}/api/instruction'),
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
          ? const Center(child: CircularProgressIndicator(color: kAmber))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Add new instruction
                const Text(
                  'ADD INSTRUCTION',
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
                    children: [
                      TextField(
                        controller: _newInstructionController,
                        maxLines: 3,
                        style: const TextStyle(color: Colors.white),
                        decoration: InputDecoration(
                          hintText:
                              'Enter instruction (e.g., Always respond in Steve\'s voice...)',
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
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButton<String>(
                              value: _selectedCategory,
                              dropdownColor: kCard,
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
                              backgroundColor: kAmber,
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
                    color: kAmber,
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
                      color: kCard,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: kBorder),
                    ),
                    child: const Center(
                      child: Text(
                        'No instructions yet',
                        style: TextStyle(color: kTextMuted),
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
        Uri.parse('${widget.serverUrl}/api/instruction/$id'),
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
    final isActive = instruction['is_active'] == 1;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isActive ? kAmber.withAlpha(77) : kBorder),
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
              instruction['instruction_text'] ?? '',
              style: const TextStyle(color: Colors.white, fontSize: 13),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, color: kRed, size: 20),
            onPressed: onDelete,
          ),
        ],
      ),
    );
  }

  Color _getCategoryColor(String cat) {
    switch (cat) {
      case 'tone':
        return kAmber;
      case 'priority':
        return kOrange;
      case 'workflow':
        return kGreen;
      case 'safety':
        return kRed;
      default:
        return kTextDim;
    }
  }
}
