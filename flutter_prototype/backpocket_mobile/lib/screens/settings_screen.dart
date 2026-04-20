import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../theme.dart';

const Color kBg = Color(0xFF0D0A07);

class SettingsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  final Function(String url, String key)? onSettingsChanged;

  const SettingsScreen({
    super.key,
    this.serverUrl = 'http://127.0.0.1:8000',
    this.apiKey = '',
    this.onSettingsChanged,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _serverUrlController;
  late TextEditingController _apiKeyController;
  final _ownerNameController = TextEditingController();
  bool _saving = false;
  String? _pingResult;
  bool _pinging = false;

  // BYOK — Sovereign Engine
  final _orKeyController = TextEditingController();
  final _geminiKeyController = TextEditingController();
  final _elKeyController = TextEditingController();
  Map<String, dynamic> _byokStatus = {};
  bool _byokLoading = false;

  Future<void> _testConnection() async {
    final url = _serverUrlController.text.trim();
    setState(() { _pinging = true; _pingResult = null; });
    try {
      final response = await http.get(
        Uri.parse('$url/api/status'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 5));
      setState(() {
        _pingResult = response.statusCode == 200 ? 'Connected' : 'HTTP ${response.statusCode}';
        _pinging = false;
      });
    } on TimeoutException {
      setState(() { _pingResult = 'Timeout — server not reachable'; _pinging = false; });
    } catch (e) {
      setState(() { _pingResult = 'Error: $e'; _pinging = false; });
    }
  }

  @override
  void initState() {
    super.initState();
    _serverUrlController = TextEditingController(text: widget.serverUrl);
    _apiKeyController = TextEditingController(text: widget.apiKey);
    _loadPrefs();
  }

  @override
  void dispose() {
    _serverUrlController.dispose();
    _apiKeyController.dispose();
    _ownerNameController.dispose();
    _orKeyController.dispose();
    _geminiKeyController.dispose();
    _elKeyController.dispose();
    super.dispose();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _serverUrlController.text =
          prefs.getString('server_url') ?? widget.serverUrl;
      _apiKeyController.text = prefs.getString('api_key') ?? widget.apiKey;
      _ownerNameController.text = prefs.getString('owner_name') ?? '';
    });
    _loadBYOKStatus();
  }

  Future<void> _loadBYOKStatus() async {
    setState(() => _byokLoading = true);
    try {
      final url = _serverUrlController.text.trim();
      final res = await http.get(
        Uri.parse('$url/api/settings/byok-status'),
        headers: {
          'Content-Type': 'application/json',
          if (_apiKeyController.text.isNotEmpty)
            'X-API-Key': _apiKeyController.text,
        },
      ).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        setState(() => _byokStatus = data['providers'] ?? {});
      }
    } catch (_) {}
    setState(() => _byokLoading = false);
  }

  Future<void> _saveBYOKKey(String provider, String key) async {
    if (key.isEmpty) return;
    try {
      final url = _serverUrlController.text.trim();
      final res = await http.post(
        Uri.parse('$url/api/settings/byok'),
        headers: {
          'Content-Type': 'application/json',
          if (_apiKeyController.text.isNotEmpty)
            'X-API-Key': _apiKeyController.text,
        },
        body: jsonEncode({'provider': provider, 'api_key': key}),
      ).timeout(const Duration(seconds: 8));
      if (res.statusCode == 200 && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('$provider key saved — you are now sovereign.'),
          backgroundColor: AppColors.green,
          behavior: SnackBarBehavior.floating,
        ));
        _loadBYOKStatus();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: AppColors.red,
          behavior: SnackBarBehavior.floating,
        ));
      }
    }
  }

  Future<void> _clearBYOKKey(String provider) async {
    try {
      final url = _serverUrlController.text.trim();
      await http.delete(
        Uri.parse('$url/api/settings/byok/$provider'),
        headers: {
          'Content-Type': 'application/json',
          if (_apiKeyController.text.isNotEmpty)
            'X-API-Key': _apiKeyController.text,
        },
      ).timeout(const Duration(seconds: 5));
      _loadBYOKStatus();
    } catch (_) {}
  }

  Future<void> _saveSettings() async {
    setState(() => _saving = true);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _serverUrlController.text.trim());
    await prefs.setString('api_key', _apiKeyController.text.trim());
    await prefs.setString('owner_name', _ownerNameController.text.trim());
    setState(() => _saving = false);

    widget.onSettingsChanged?.call(
      _serverUrlController.text.trim(),
      _apiKeyController.text.trim(),
    );

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Settings saved!'),
        backgroundColor: AppColors.green,
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
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text(
            'SETTINGS',
            style: TextStyle(
              color: AppColors.amber,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 16),

          // Identity
          _SettingsSection(
            title: 'Your Profile',
            children: [
              _SettingsField(
                controller: _ownerNameController,
                label: 'Your Name',
                hint: 'e.g. Steve',
                icon: Icons.person_outline,
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Server Configuration
          _SettingsSection(
            title: 'Server Configuration',
            children: [
              _SettingsField(
                controller: _serverUrlController,
                label: 'Server URL',
                hint: 'http://192.168.x.x:8000',
                icon: Icons.dns_outlined,
              ),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: _pinging
                        ? const SizedBox(width: 14, height: 14, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.wifi_find_outlined, size: 16),
                    label: Text(_pinging ? 'Testing…' : 'Test Connection'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.amber,
                      side: const BorderSide(color: AppColors.amber),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    onPressed: _pinging ? null : _testConnection,
                  ),
                ),
              ]),
              if (_pingResult != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Row(children: [
                    Icon(
                      _pingResult == 'Connected' ? Icons.check_circle_outline : Icons.error_outline,
                      size: 14,
                      color: _pingResult == 'Connected' ? AppColors.green : AppColors.red,
                    ),
                    const SizedBox(width: 6),
                    Expanded(child: Text(
                      _pingResult!,
                      style: TextStyle(
                        color: _pingResult == 'Connected' ? AppColors.green : AppColors.red,
                        fontSize: 12,
                      ),
                    )),
                  ]),
                ),
              const SizedBox(height: 12),
              _SettingsField(
                controller: _apiKeyController,
                label: 'API Key (optional)',
                hint: 'BP_API_KEY from .env',
                icon: Icons.key_outlined,
                isPassword: true,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Save Button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.amber,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              onPressed: _saving ? null : _saveSettings,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text(
                      'Save Settings',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 32),

          // ── SOVEREIGN ENGINE — BYOK ─────────────────────────────────────────
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Text(
                    'SOVEREIGN ENGINE',
                    style: TextStyle(
                      color: AppColors.textDim,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.amber.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'BYOK',
                      style: TextStyle(color: AppColors.amber, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              const Text(
                'Use your own API keys. Your data, your keys, no cloud lock-in.',
                style: TextStyle(color: AppColors.textMuted, fontSize: 11),
              ),
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: _byokLoading
                    ? const Center(child: CircularProgressIndicator(color: AppColors.amber))
                    : Column(
                        children: [
                          _BYOKRow(
                            provider: 'openrouter',
                            label: 'OpenRouter',
                            controller: _orKeyController,
                            isConfigured: _byokStatus['openrouter']?['configured'] == true,
                            onSave: () => _saveBYOKKey('openrouter', _orKeyController.text.trim()),
                            onClear: () => _clearBYOKKey('openrouter'),
                          ),
                          const Divider(color: AppColors.border, height: 24),
                          _BYOKRow(
                            provider: 'gemini',
                            label: 'Gemini',
                            controller: _geminiKeyController,
                            isConfigured: _byokStatus['gemini']?['configured'] == true,
                            onSave: () => _saveBYOKKey('gemini', _geminiKeyController.text.trim()),
                            onClear: () => _clearBYOKKey('gemini'),
                          ),
                          const Divider(color: AppColors.border, height: 24),
                          _BYOKRow(
                            provider: 'elevenlabs',
                            label: 'ElevenLabs',
                            controller: _elKeyController,
                            isConfigured: _byokStatus['elevenlabs']?['configured'] == true,
                            onSave: () => _saveBYOKKey('elevenlabs', _elKeyController.text.trim()),
                            onClear: () => _clearBYOKKey('elevenlabs'),
                          ),
                        ],
                      ),
              ),
            ],
          ),
          const SizedBox(height: 32),

          // About
          _SettingsSection(
            title: 'About',
            children: [
              _InfoRow(label: 'App', value: 'BackPocket OS'),
              _InfoRow(label: 'Version', value: '2.3'),
              _InfoRow(label: 'Platform', value: 'Business OS'),
              _InfoRow(label: 'Theme', value: '5am Warehouse'),
            ],
          ),
          const SizedBox(height: 24),

          // API Endpoints Info
          _SettingsSection(
            title: 'Available Endpoints',
            children: const [
              _InfoRow(label: 'Status', value: '/api/status'),
              _InfoRow(label: 'Inbox', value: '/api/mobile/pending'),
              _InfoRow(label: 'Documents', value: '/api/documents'),
              _InfoRow(label: 'Workflow', value: '/api/workflow/stages'),
              _InfoRow(label: 'Marketing', value: '/api/marketing/insights'),
              _InfoRow(label: 'Chat', value: '/api/mobile/chat'),
            ],
          ),
        ],
      ),
    );
  }
}

class _SettingsSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const _SettingsSection({required this.title, required this.children});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AppColors.textDim,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(children: children),
        ),
      ],
    );
  }
}

class _SettingsField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  final String hint;
  final IconData icon;
  final bool isPassword;

  const _SettingsField({
    required this.controller,
    required this.label,
    required this.hint,
    required this.icon,
    this.isPassword = false,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: isPassword,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: AppColors.textDim),
        hintText: hint,
        hintStyle: const TextStyle(color: AppColors.textMuted),
        prefixIcon: Icon(icon, color: AppColors.amber, size: 20),
        filled: true,
        fillColor: AppColors.surface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.border),
        ),
      ),
    );
  }
}

class _BYOKRow extends StatelessWidget {
  final String provider;
  final String label;
  final TextEditingController controller;
  final bool isConfigured;
  final VoidCallback onSave;
  final VoidCallback onClear;

  const _BYOKRow({
    required this.provider,
    required this.label,
    required this.controller,
    required this.isConfigured,
    required this.onSave,
    required this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(
              isConfigured ? Icons.verified : Icons.key_off_outlined,
              color: isConfigured ? AppColors.green : AppColors.textMuted,
              size: 16,
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: isConfigured ? AppColors.green : AppColors.textDim,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(width: 8),
            if (isConfigured)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                decoration: BoxDecoration(
                  color: AppColors.green.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text('SOVEREIGN', style: TextStyle(color: AppColors.green, fontSize: 9)),
              ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                obscureText: true,
                style: const TextStyle(color: Colors.white, fontSize: 12),
                decoration: InputDecoration(
                  hintText: isConfigured ? '••••••• (replace to update)' : 'sk-or-v1-...',
                  hintStyle: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                  filled: true,
                  fillColor: AppColors.surface,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: const BorderSide(color: AppColors.border),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: const BorderSide(color: AppColors.border),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            GestureDetector(
              onTap: onSave,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.amber,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text('Save', style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 12)),
              ),
            ),
            if (isConfigured) ...[
              const SizedBox(width: 6),
              GestureDetector(
                onTap: onClear,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppColors.red.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.red.withValues(alpha: 0.3)),
                  ),
                  child: const Icon(Icons.delete_outline, color: AppColors.red, size: 16),
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textDim, fontSize: 13)),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.amber,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
