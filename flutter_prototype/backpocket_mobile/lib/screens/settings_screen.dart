import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

const Color kBg = Color(0xFF0D0A07);
const Color kSurface = Color(0xFF1A1208);
const Color kCard = Color(0xFF211708);
const Color kBorder = Color(0x22FFFFFF);
const Color kAmber = Color(0xFFFBBF24);
const Color kOrange = Color(0xFFF97316);
const Color kTextDim = Color(0x99FFFFFF);
const Color kTextMuted = Color(0x44FFFFFF);
const Color kGreen = Color(0xFF22C55E);
const Color kRed = Color(0xFFEF4444);

class SettingsScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;
  final Function(String url, String key)? onSettingsChanged;

  const SettingsScreen({
    super.key,
    this.serverUrl = 'http://192.168.1.147:8000',
    this.apiKey = '',
    this.onSettingsChanged,
  });

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _serverUrlController;
  late TextEditingController _apiKeyController;
  bool _saving = false;

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
    super.dispose();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _serverUrlController.text =
          prefs.getString('server_url') ?? widget.serverUrl;
      _apiKeyController.text = prefs.getString('api_key') ?? widget.apiKey;
    });
  }

  Future<void> _saveSettings() async {
    setState(() => _saving = true);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _serverUrlController.text.trim());
    await prefs.setString('api_key', _apiKeyController.text.trim());
    setState(() => _saving = false);

    widget.onSettingsChanged?.call(
      _serverUrlController.text.trim(),
      _apiKeyController.text.trim(),
    );

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Settings saved!'),
        backgroundColor: kGreen,
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
              color: kAmber,
              fontSize: 12,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 16),

          // Server Configuration
          _SettingsSection(
            title: 'Server Configuration',
            children: [
              _SettingsField(
                controller: _serverUrlController,
                label: 'Server URL',
                hint: 'http://192.168.1.147:8000',
                icon: Icons.dns_outlined,
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
                backgroundColor: kAmber,
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

          // About
          _SettingsSection(
            title: 'About',
            children: [
              _InfoRow(label: 'App', value: 'BackPocket OS'),
              _InfoRow(label: 'Version', value: '2.3'),
              _InfoRow(label: 'User', value: 'Steve (Tradie)'),
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
            color: kTextDim,
            fontSize: 12,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: kCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: kBorder),
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
        labelStyle: const TextStyle(color: kTextDim),
        hintText: hint,
        hintStyle: const TextStyle(color: kTextMuted),
        prefixIcon: Icon(icon, color: kAmber, size: 20),
        filled: true,
        fillColor: kSurface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: kBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: kBorder),
        ),
      ),
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
          Text(label, style: const TextStyle(color: kTextDim, fontSize: 13)),
          Text(
            value,
            style: const TextStyle(
              color: kAmber,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
