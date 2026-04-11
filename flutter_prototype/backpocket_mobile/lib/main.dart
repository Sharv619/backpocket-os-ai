import 'dart:convert';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'screens/vision_chat_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/documents_screen.dart';
import 'screens/marketing_screen.dart';
import 'screens/instructions_screen.dart';
import 'screens/settings_screen.dart';

// ─── TwinController for chat state ───────────────────────────────────────────────
class TwinController extends ChangeNotifier {
  final List<Map<String, String>> _messages = [];
  String _currentStage = 'Inbox';
  bool _isLoading = false;

  List<Map<String, String>> get messages => _messages;
  String get currentStage => _currentStage;
  bool get isLoading => _isLoading;

  void setStage(String stage) {
    _currentStage = stage;
    notifyListeners();
  }

  void addMessage(Map<String, String> msg) {
    _messages.add(msg);
    notifyListeners();
  }

  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void clearHistory() {
    _messages.clear();
    notifyListeners();
  }
}

// ─── Colours (5am warehouse aesthetic) ───────────────────────────────────────
const Color kBg = Color(0xFF0D0A07);
const Color kSurface = Color(0xFF1A1208);
const Color kCard = Color(0xFF211708);
const Color kBorder = Color(0x22FFFFFF);
const Color kAmber = Color(0xFFFBBF24);
const Color kOrange = Color(0xFFF97316);
const Color kRed = Color(0xFFEF4444);
const Color kGreen = Color(0xFF22C55E);
const Color kTextDim = Color(0x99FFFFFF);
const Color kTextMuted = Color(0x44FFFFFF);

// ─── Tier config ─────────────────────────────────────────────────────────────
const _tierLabels = {1: 'URGENT', 2: 'HIGH', 3: 'MEDIUM', 4: 'LOW', 5: 'SPAM'};
const _tierColors = {
  1: kRed,
  2: kOrange,
  3: kAmber,
  4: Color(0xFF6B7280),
  5: Color(0xFF374151),
};

// ─── Entry point ─────────────────────────────────────────────────────────────
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const BackPocketApp());
}

class BackPocketApp extends StatelessWidget {
  const BackPocketApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => TwinController(),
      child: MaterialApp(
        title: 'BackPocket OS',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        home: const AppShell(),
      ),
    );
  }
}

// ─── App Shell (bottom nav + settings) ───────────────────────────────────────
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _tab = 0;
  String _serverUrl = 'http://127.0.0.1:8000';
  String _apiKey = '';
  bool _magnifierMode = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _serverUrl = prefs.getString('server_url') ?? 'http://127.0.0.1:8000';
      _apiKey = prefs.getString('api_key') ?? '';
    });
  }

  Future<void> _savePrefs(String url, String key) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', url);
    await prefs.setString('api_key', key);
    setState(() {
      _serverUrl = url;
      _apiKey = key;
    });
  }

  void _showSettings() {
    final urlCtrl = TextEditingController(text: _serverUrl);
    final keyCtrl = TextEditingController(text: _apiKey);
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: kSurface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          left: 24,
          right: 24,
          top: 24,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Settings',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: kAmber,
              ),
            ),
            const SizedBox(height: 20),
            _settingsField(urlCtrl, 'Server URL', 'http://127.0.0.1:8000'),
            const SizedBox(height: 12),
            _settingsField(keyCtrl, 'API Key (optional)', 'BP_API_KEY value'),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: kOrange,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () {
                  _savePrefs(urlCtrl.text.trim(), keyCtrl.text.trim());
                  Navigator.pop(context);
                },
                child: const Text(
                  'Save',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _settingsField(TextEditingController ctrl, String label, String hint) {
    return TextField(
      controller: ctrl,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        labelStyle: const TextStyle(color: kTextDim),
        hintStyle: const TextStyle(color: kTextMuted),
        filled: true,
        fillColor: kCard,
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

  // ─── Animated Sidebar ─────────────────────────────────────────────────────────
  Widget _buildSidebar() {
    final twinController = context.read<TwinController>();
    final navItems = [
      {'icon': Icons.dashboard_outlined, 'label': 'Home', 'tab': 0},
      {'icon': Icons.inbox_outlined, 'label': 'Inbox', 'tab': 1},
      {'icon': Icons.psychology_outlined, 'label': 'Twin Chat', 'tab': 2},
      {'icon': Icons.description_outlined, 'label': 'Documents', 'tab': 3},
      {'icon': Icons.campaign_outlined, 'label': 'Marketing', 'tab': 4},
      {'icon': Icons.rule_outlined, 'label': 'Instructions', 'tab': 5},
    ];
    final chatHistory = twinController.messages
        .where((m) => m['role'] == 'user')
        .take(5)
        .toList();

    return Drawer(
      backgroundColor: AppColors.surface,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.amber, AppColors.orange],
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Center(
                      child: Text(
                        'BP',
                        style: TextStyle(
                          color: AppColors.brown,
                          fontWeight: FontWeight.w900,
                          fontSize: 14,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'BackPocket',
                    style: TextStyle(
                      color: AppColors.cream,
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(color: kBorder, height: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  ...navItems.map(
                    (item) => _SidebarItem(
                      icon: item['icon'] as IconData,
                      label: item['label'] as String,
                      isSelected: _tab == item['tab'],
                      onTap: () {
                        setState(() => _tab = item['tab'] as int);
                        Navigator.pop(context);
                      },
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Text(
                      'CHAT HISTORY',
                      style: TextStyle(
                        color: kTextMuted,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1,
                      ),
                    ),
                  ),
                  if (chatHistory.isEmpty)
                    const Padding(
                      padding: EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      child: Text(
                        'No recent chats',
                        style: TextStyle(color: kTextMuted, fontSize: 12),
                      ),
                    )
                  else
                    ...chatHistory.asMap().entries.map(
                      (e) => _ChatHistoryItem(
                        text: e.value['content'] ?? '',
                        index: e.key,
                        onTap: () {
                          setState(() => _tab = 2);
                          Navigator.pop(context);
                        },
                      ),
                    ),
                ],
              ),
            ),
            const Divider(color: kBorder, height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: _SidebarItem(
                icon: Icons.settings_outlined,
                label: 'Settings',
                isSelected: false,
                onTap: () {
                  setState(() => _tab = 6);
                  Navigator.pop(context);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      InboxScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      TwinChatScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      DocumentsScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      MarketingScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      InstructionsScreen(serverUrl: _serverUrl, apiKey: _apiKey),
      SettingsScreen(
        serverUrl: _serverUrl,
        apiKey: _apiKey,
        onSettingsChanged: (url, key) {
          setState(() {
            _serverUrl = url;
            _apiKey = key;
          });
        },
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        backgroundColor: kSurface,
        elevation: 0,
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(Icons.menu, color: kAmber),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
        title: const Text(
          'BackPocket OS',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: Icon(
              _magnifierMode ? Icons.zoom_in : Icons.zoom_in_outlined,
              color: _magnifierMode ? AppColors.amber : kTextDim,
            ),
            onPressed: () => setState(() => _magnifierMode = !_magnifierMode),
            tooltip: 'Magnifier Mode',
          ),
          IconButton(
            icon: const Icon(Icons.dashboard_outlined, color: kTextDim),
            onPressed: () => setState(() => _tab = 0),
          ),
        ],
      ),
      drawer: _buildSidebar(),
      body: Transform.scale(
        scale: _magnifierMode ? 1.1 : 1.0,
        child: pages[_tab],
      ),
      floatingActionButton: _tab == 1
          ? FloatingActionButton(
              onPressed: () => Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) =>
                      VisionChatScreen(serverUrl: _serverUrl, apiKey: _apiKey),
                ),
              ),
              backgroundColor: kOrange,
              child: const Icon(Icons.camera_alt_rounded),
            )
          : null,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: kSurface,
          border: Border(top: BorderSide(color: kBorder)),
        ),
        child: BottomNavigationBar(
          currentIndex: _tab,
          onTap: (i) => setState(() => _tab = i),
          backgroundColor: Colors.transparent,
          selectedItemColor: kAmber,
          unselectedItemColor: kTextMuted,
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_outlined),
              activeIcon: Icon(Icons.dashboard),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.inbox_outlined),
              activeIcon: Icon(Icons.inbox),
              label: 'Inbox',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.psychology_outlined),
              activeIcon: Icon(Icons.psychology),
              label: 'Twin',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.description_outlined),
              activeIcon: Icon(Icons.description),
              label: 'Docs',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.campaign_outlined),
              activeIcon: Icon(Icons.campaign),
              label: 'Marketing',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.rule_outlined),
              activeIcon: Icon(Icons.rule),
              label: 'Rules',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.settings_outlined),
              activeIcon: Icon(Icons.settings),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Sidebar Item Widget ────────────────────────────────────────────────────────
class _SidebarItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _SidebarItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(
        icon,
        color: isSelected ? AppColors.amber : kTextMuted,
        size: 22,
      ),
      title: Text(
        label,
        style: TextStyle(
          color: isSelected ? AppColors.cream : kTextDim,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          fontSize: 14,
        ),
      ),
      selected: isSelected,
      selectedTileColor: AppColors.amber.withAlpha(26),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      onTap: onTap,
    );
  }
}

// ─── Chat History Item Widget ───────────────────────────────────────────────────
class _ChatHistoryItem extends StatelessWidget {
  final String text;
  final int index;
  final VoidCallback onTap;

  const _ChatHistoryItem({
    required this.text,
    required this.index,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
      leading: const Icon(
        Icons.chat_bubble_outline,
        color: kTextMuted,
        size: 16,
      ),
      title: Text(
        text.length > 30 ? '${text.substring(0, 30)}...' : text,
        style: const TextStyle(color: kTextMuted, fontSize: 12),
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      onTap: onTap,
    );
  }
}

// ─── Inbox Screen ─────────────────────────────────────────────────────────────
class InboxScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const InboxScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchPending();
  }

  @override
  void didUpdateWidget(InboxScreen old) {
    super.didUpdateWidget(old);
    if (old.serverUrl != widget.serverUrl || old.apiKey != widget.apiKey) {
      _fetchPending();
    }
  }

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _fetchPending() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final res = await http
          .get(
            Uri.parse('${widget.serverUrl}/api/mobile/pending'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as Map<String, dynamic>;
        setState(() {
          _items = List<Map<String, dynamic>>.from(
            (data['items'] as List? ?? []).map(
              (e) => Map<String, dynamic>.from(e as Map),
            ),
          );
          _loading = false;
        });
      } else {
        setState(() {
          _error = 'Server error ${res.statusCode}';
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Cannot reach server.\nCheck Settings → Server URL.\n\n$e';
        _loading = false;
      });
    }
  }

  Future<void> _approve(String refId, String sender, String subject) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => _ApproveDialog(sender: sender, subject: subject),
    );
    if (confirmed != true) return;

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/approve'),
            headers: _headers,
            body: jsonEncode({'ref_id': refId, 'note': 'approved via mobile'}),
          )
          .timeout(const Duration(seconds: 15));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;

      final status = data['status'] as String? ?? '';
      if (status == 'approved' || status == 'demo') {
        _showSnack(
          status == 'demo'
              ? 'DEMO: Would send to $sender'
              : 'Email sent to $sender',
          success: true,
        );
        setState(() => _items.removeWhere((i) => i['ref_id'] == refId));
      } else {
        _showSnack(
          data['message'] as String? ?? 'Approval failed',
          success: false,
        );
      }
    } catch (e) {
      if (mounted) _showSnack('Error: $e', success: false);
    }
  }

  void _showSnack(String msg, {required bool success}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: success ? kGreen : kRed,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  void _openDetail(Map<String, dynamic> item) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => ApprovalDetailScreen(
          item: item,
          serverUrl: widget.serverUrl,
          apiKey: widget.apiKey,
          onApproved: () {
            setState(
              () => _items.removeWhere((i) => i['ref_id'] == item['ref_id']),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [kBg, Color(0xFF1A1008), Color(0xFF2D1A00)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: _loading
          ? const Center(child: CircularProgressIndicator(color: kAmber))
          : _error != null
          ? _buildError()
          : _items.isEmpty
          ? _buildEmpty()
          : _buildList(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_outlined, color: kTextMuted, size: 48),
            const SizedBox(height: 16),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(color: kTextDim, height: 1.5),
            ),
            const SizedBox(height: 20),
            _textBtn('Retry', kOrange, _fetchPending),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('✅', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 12),
          const Text(
            'All clear!',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.bold,
              color: kAmber,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'No pending approvals.',
            style: TextStyle(color: kTextDim),
          ),
          const SizedBox(height: 20),
          _textBtn('Refresh', kSurface, _fetchPending),
        ],
      ),
    );
  }

  Widget _buildList() {
    return RefreshIndicator(
      color: kAmber,
      backgroundColor: kCard,
      onRefresh: _fetchPending,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${_items.length} pending approval${_items.length == 1 ? "" : "s"}',
                  style: const TextStyle(color: kTextDim, fontSize: 13),
                ),
              ),
              GestureDetector(
                onTap: _fetchPending,
                child: const Icon(Icons.refresh, color: kTextMuted, size: 18),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ..._items.map(
            (item) => _InboxCard(
              item: item,
              onApprove: () => _approve(
                item['ref_id'] as String? ?? '',
                item['sender'] as String? ?? '',
                item['subject'] as String? ?? '',
              ),
              onTap: () => _openDetail(item),
            ),
          ),
        ],
      ),
    );
  }

  Widget _textBtn(String label, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: kBorder),
        ),
        child: Text(
          label,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

// ─── Inbox Card ───────────────────────────────────────────────────────────────
class _InboxCard extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback onApprove;
  final VoidCallback onTap;

  const _InboxCard({
    required this.item,
    required this.onApprove,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final tier = item['tier'] as int? ?? 3;
    final tierLabel = _tierLabels[tier] ?? 'MEDIUM';
    final tierColor = _tierColors[tier] ?? kAmber;
    final ageHours = (item['age_hours'] as num?)?.toDouble() ?? 0.0;
    final preview = item['preview'] as String? ?? '';

    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: kCard,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: kBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Tier badge + age
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 0),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: tierColor.withAlpha(38),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: tierColor.withAlpha(102)),
                    ),
                    child: Text(
                      tierLabel,
                      style: TextStyle(
                        color: tierColor,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatAge(ageHours),
                    style: const TextStyle(color: kTextMuted, fontSize: 11),
                  ),
                ],
              ),
            ),
            // Sender
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 8, 14, 0),
              child: Text(
                item['sender'] as String? ?? 'Unknown',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ),
            // Subject
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 2, 14, 0),
              child: Text(
                item['subject'] as String? ?? '',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(color: kAmber, fontSize: 13),
              ),
            ),
            // Preview
            if (preview.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(14, 4, 14, 0),
                child: Text(
                  preview,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: kTextDim,
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ),
            // Approve button
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
              child: Row(
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: onApprove,
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 11),
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [kOrange, Color(0xFFEA580C)],
                          ),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.check_circle_outline,
                              color: Colors.white,
                              size: 16,
                            ),
                            SizedBox(width: 6),
                            Text(
                              'Approve & Send',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: onTap,
                    child: Container(
                      padding: const EdgeInsets.all(11),
                      decoration: BoxDecoration(
                        color: kSurface,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: kBorder),
                      ),
                      child: const Icon(
                        Icons.open_in_new,
                        color: kTextDim,
                        size: 16,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatAge(double hours) {
    if (hours < 1) return '${(hours * 60).round()}m ago';
    if (hours < 24) return '${hours.round()}h ago';
    return '${(hours / 24).round()}d ago';
  }
}

// ─── Approval Detail Screen ───────────────────────────────────────────────────
class ApprovalDetailScreen extends StatefulWidget {
  final Map<String, dynamic> item;
  final String serverUrl;
  final String apiKey;
  final VoidCallback onApproved;

  const ApprovalDetailScreen({
    super.key,
    required this.item,
    required this.serverUrl,
    required this.apiKey,
    required this.onApproved,
  });

  @override
  State<ApprovalDetailScreen> createState() => _ApprovalDetailScreenState();
}

class _ApprovalDetailScreenState extends State<ApprovalDetailScreen> {
  bool _approving = false;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _doApprove() async {
    setState(() => _approving = true);
    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/approve'),
            headers: _headers,
            body: jsonEncode({
              'ref_id': widget.item['ref_id'],
              'note': 'approved via mobile detail view',
            }),
          )
          .timeout(const Duration(seconds: 15));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (!mounted) return;

      final status = data['status'] as String? ?? '';
      if (status == 'approved' || status == 'demo') {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              status == 'demo'
                  ? 'DEMO: Would have sent email'
                  : 'Email sent successfully',
            ),
            backgroundColor: kGreen,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
        widget.onApproved();
        Navigator.pop(context);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(data['message'] as String? ?? 'Approval failed'),
            backgroundColor: kRed,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: kRed,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _approving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tier = widget.item['tier'] as int? ?? 3;
    final tierLabel = _tierLabels[tier] ?? 'MEDIUM';
    final tierColor = _tierColors[tier] ?? kAmber;
    final preview = widget.item['preview'] as String? ?? '';

    return Scaffold(
      backgroundColor: kBg,
      appBar: AppBar(
        backgroundColor: kSurface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: kAmber, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Review Draft',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: kBorder),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Tier badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: tierColor.withAlpha(38),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: tierColor.withAlpha(102)),
              ),
              child: Text(
                tierLabel,
                style: TextStyle(
                  color: tierColor,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Subject
            Text(
              widget.item['subject'] as String? ?? '',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 8),

            // From
            Row(
              children: [
                const Icon(Icons.person_outline, color: kTextMuted, size: 14),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    widget.item['sender'] as String? ?? '',
                    style: const TextStyle(color: kTextDim, fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            // Draft preview
            const Text(
              'AI Draft Reply',
              style: TextStyle(
                color: kAmber,
                fontSize: 12,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: kCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: kBorder),
              ),
              child: Text(
                preview.isNotEmpty ? preview : 'No preview available.',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  height: 1.6,
                ),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Full draft available in desktop dashboard',
              style: TextStyle(color: kTextMuted, fontSize: 11),
            ),
            const SizedBox(height: 32),

            // Approve button
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: _approving ? null : _doApprove,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  decoration: BoxDecoration(
                    gradient: _approving
                        ? null
                        : const LinearGradient(
                            colors: [kOrange, Color(0xFFEA580C)],
                          ),
                    color: _approving ? kSurface : null,
                    borderRadius: BorderRadius.circular(14),
                    border: _approving ? Border.all(color: kBorder) : null,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_approving)
                        const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            color: kAmber,
                            strokeWidth: 2,
                          ),
                        )
                      else
                        const Icon(
                          Icons.check_circle,
                          color: Colors.white,
                          size: 20,
                        ),
                      const SizedBox(width: 10),
                      Text(
                        _approving ? 'Sending...' : 'Approve & Send Email',
                        style: TextStyle(
                          color: _approving ? kTextDim : Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Back button
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  decoration: BoxDecoration(
                    color: kSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: kBorder),
                  ),
                  child: const Center(
                    child: Text(
                      'Back to Inbox',
                      style: TextStyle(
                        color: kTextDim,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Approve Confirm Dialog ────────────────────────────────────────────────────
class _ApproveDialog extends StatelessWidget {
  final String sender;
  final String subject;

  const _ApproveDialog({required this.sender, required this.subject});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: kSurface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: kBorder),
      ),
      title: const Text(
        'Approve & Send?',
        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'This will send the AI draft to:',
            style: TextStyle(color: kTextDim),
          ),
          const SizedBox(height: 8),
          Text(
            sender,
            style: const TextStyle(color: kAmber, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            'Re: $subject',
            style: const TextStyle(color: kTextDim, fontSize: 12),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context, false),
          child: const Text('Cancel', style: TextStyle(color: kTextMuted)),
        ),
        ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: kOrange,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
            ),
          ),
          onPressed: () => Navigator.pop(context, true),
          child: const Text(
            'Send It',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
      ],
    );
  }
}

// ─── Twin Chat Screen ─────────────────────────────────────────────────────────
class TwinChatScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const TwinChatScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<TwinChatScreen> createState() => _TwinChatScreenState();
}

class _TwinChatScreenState extends State<TwinChatScreen> {
  final List<Map<String, String>> _messages = [];
  final TextEditingController _ctrl = TextEditingController();
  final ScrollController _scroll = ScrollController();
  bool _sending = false;

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    if (widget.apiKey.isNotEmpty) 'X-API-Key': widget.apiKey,
  };

  Future<void> _send() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    _ctrl.clear();
    setState(() {
      _messages.add({'role': 'user', 'content': text});
      _sending = true;
    });
    _scrollToBottom();

    try {
      final res = await http
          .post(
            Uri.parse('${widget.serverUrl}/api/mobile/chat'),
            headers: _headers,
            body: jsonEncode({'message': text}),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (mounted) {
        setState(() {
          _messages.add({
            'role': 'assistant',
            'content': data['response'] as String? ?? 'No response.',
          });
          _sending = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add({'role': 'assistant', 'content': 'Error: $e'});
          _sending = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
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
          Expanded(
            child: _messages.isEmpty
                ? _buildWelcome()
                : ListView.builder(
                    controller: _scroll,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (_, i) => _ChatBubble(msg: _messages[i]),
                  ),
          ),
          if (_sending)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 20, vertical: 4),
              child: Row(
                children: [
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(
                      color: kAmber,
                      strokeWidth: 2,
                    ),
                  ),
                  SizedBox(width: 8),
                  Text(
                    'Twin is thinking...',
                    style: TextStyle(color: kTextDim, fontSize: 12),
                  ),
                ],
              ),
            ),
          Container(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            decoration: const BoxDecoration(
              color: kSurface,
              border: Border(top: BorderSide(color: kBorder)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ctrl,
                    style: const TextStyle(color: Colors.white, fontSize: 14),
                    maxLines: null,
                    onSubmitted: (_) => _send(),
                    decoration: InputDecoration(
                      hintText: 'Ask your twin anything...',
                      hintStyle: const TextStyle(color: kTextMuted),
                      filled: true,
                      fillColor: kCard,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: kBorder),
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: kBorder),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                        borderSide: const BorderSide(color: kAmber, width: 1.5),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                GestureDetector(
                  onTap: _sending ? null : _send,
                  child: Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      gradient: _sending
                          ? null
                          : const LinearGradient(
                              colors: [kOrange, Color(0xFFEA580C)],
                            ),
                      color: _sending ? kCard : null,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      Icons.send_rounded,
                      color: _sending ? kTextMuted : Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcome() {
    final suggestions = [
      'What emails need attention today?',
      'How many items are pending?',
      "Summarise today's inbox",
    ];
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 40),
        const Center(child: Text('🧠', style: TextStyle(fontSize: 48))),
        const SizedBox(height: 16),
        const Center(
          child: Text(
            'BackPocket Twin',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        const SizedBox(height: 8),
        const Center(
          child: Text(
            'Ask me anything about your inbox',
            style: TextStyle(color: kTextDim, fontSize: 14),
          ),
        ),
        const SizedBox(height: 32),
        ...suggestions.map(
          (s) => GestureDetector(
            onTap: () {
              _ctrl.text = s;
              _send();
            },
            child: Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: kCard,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: kBorder),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      s,
                      style: const TextStyle(color: kTextDim, fontSize: 13),
                    ),
                  ),
                  const Icon(
                    Icons.arrow_forward_ios,
                    color: kTextMuted,
                    size: 12,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final Map<String, String> msg;

  const _ChatBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isUser = msg['role'] == 'user';
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [kAmber, kOrange]),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Center(
                child: Text(
                  'BP',
                  style: TextStyle(
                    color: Colors.black,
                    fontWeight: FontWeight.w900,
                    fontSize: 9,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser ? kOrange.withAlpha(51) : kCard,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isUser ? 14 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 14),
                ),
                border: Border.all(
                  color: isUser ? kOrange.withAlpha(76) : kBorder,
                ),
              ),
              child: Text(
                msg['content'] ?? '',
                style: TextStyle(
                  color: isUser ? Colors.white : kTextDim,
                  fontSize: 13,
                  height: 1.5,
                ),
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }
}
