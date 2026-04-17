import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'theme.dart';
import 'screens/inbox_screen.dart';
import 'screens/twin_chat_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/documents_screen.dart';
import 'screens/marketing_screen.dart';
import 'screens/instructions_screen.dart';
import 'screens/construction_screen.dart';
import 'screens/settings_screen.dart';
import 'services/voice_command_service.dart';
import 'widgets/voice_fab.dart';
import 'widgets/voice_recording_overlay.dart';
import 'widgets/voice_confirmation_card.dart';
import 'models/voice_command_response.dart';

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

class BackPocketApp extends StatefulWidget {
  const BackPocketApp({super.key});

  @override
  State<BackPocketApp> createState() => _BackPocketAppState();
}

class _BackPocketAppState extends State<BackPocketApp> {
  late final GoRouter _router;

  @override
  void initState() {
    super.initState();
    _router = GoRouter(
      initialLocation: '/',
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => AppShell(initialTab: 0),
        ),
        GoRoute(
          path: '/inbox',
          builder: (context, state) => AppShell(initialTab: 1),
        ),
        GoRoute(
          path: '/chat',
          builder: (context, state) => AppShell(initialTab: 2),
        ),
        GoRoute(
          path: '/docs',
          builder: (context, state) => AppShell(initialTab: 3),
        ),
        GoRoute(
          path: '/marketing',
          builder: (context, state) => AppShell(initialTab: 4),
        ),
        GoRoute(
          path: '/instructions',
          builder: (context, state) => AppShell(initialTab: 5),
        ),
        GoRoute(
          path: '/construction',
          builder: (context, state) => AppShell(initialTab: 6),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => AppShell(initialTab: 7),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => TwinController(),
      child: MaterialApp.router(
        title: 'BackPocket OS',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        builder: (context, child) =>
            AppBackground(child: child ?? const SizedBox()),
        routerConfig: _router,
      ),
    );
  }
}

// ─── App Shell (bottom nav + settings) ───────────────────────────────────────
class AppShell extends StatefulWidget {
  final int initialTab;

  const AppShell({super.key, this.initialTab = 0});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  late int _tab;
  String _serverUrl = 'http://192.168.1.147:8000';
  String _apiKey = '';
  bool _magnifierMode = false;
  VoiceCommandService? _voiceService;
  bool _showVoiceOverlay = false;
  VoiceCommandResponse? _voiceResponse;

  @override
  void initState() {
    super.initState();
    _tab = widget.initialTab;
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _serverUrl = prefs.getString('server_url') ?? 'http://192.168.1.147:8000';
      _apiKey = prefs.getString('api_key') ?? '';
      _voiceService = VoiceCommandService(baseUrl: _serverUrl, apiKey: _apiKey);
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
            _settingsField(urlCtrl, 'Server URL', 'http://192.168.1.147:8000'),
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
      {'icon': Icons.psychology_outlined, 'label': 'Pip Chat', 'tab': 2},
      {'icon': Icons.description_outlined, 'label': 'Documents', 'tab': 3},
      {'icon': Icons.campaign_outlined, 'label': 'Marketing', 'tab': 4},
      {'icon': Icons.rule_outlined, 'label': 'Instructions', 'tab': 5},
      {'icon': Icons.build_outlined, 'label': 'Construction', 'tab': 6},
      {'icon': Icons.settings_outlined, 'label': 'Settings', 'tab': 7},
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

  static const _screenNames = ['dashboard', 'inbox', 'chat', 'documents', 'marketing', 'instructions', 'construction', 'settings'];

  void _onVoiceFabTap() {
    _voiceService?.setScreenContext(_screenNames[_tab], tabIndex: _tab);
    setState(() => _showVoiceOverlay = true);
  }

  Future<void> _handleVoiceText(String text) async {
    if (_voiceService == null) return;
    _voiceService!.setScreenContext(_screenNames[_tab], tabIndex: _tab);
    final response = await _voiceService!.sendTranscript(text);
    if (response != null) {
      setState(() => _voiceResponse = response);
      _handleVoiceUiAction(response);
      if (!response.needsConfirmation && !response.needsMoreInput) {
        setState(() => _showVoiceOverlay = false);
      }
    }
  }

  Future<void> _handleVoiceConfirm(String answer) async {
    if (_voiceService == null) return;
    final response = await _voiceService!.sendConfirmation(answer);
    if (response != null) {
      setState(() => _voiceResponse = response);
      _handleVoiceUiAction(response);
      if (!response.needsConfirmation && !response.needsMoreInput) {
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) setState(() => _voiceResponse = null);
        });
      }
    } else {
      setState(() => _voiceResponse = null);
    }
  }

  void _handleVoiceUiAction(VoiceCommandResponse response) {
    final ui = response.uiAction;
    if (ui.navigateTo != null) {
      final idx = _screenNames.indexOf(ui.navigateTo!);
      if (idx >= 0) setState(() => _tab = idx);
    }
    if (ui.tabIndex != null && ui.navigateTo == null) {
      setState(() => _tab = ui.tabIndex!);
    }
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
      ConstructionScreen(serverUrl: _serverUrl, apiKey: _apiKey),
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
      body: Stack(
        children: [
          Transform.scale(
            scale: _magnifierMode ? 1.1 : 1.0,
            child: pages[_tab],
          ),
          if (_voiceResponse != null && (_voiceResponse!.needsConfirmation || _voiceResponse!.needsMoreInput))
            Positioned(
              bottom: 80,
              left: 0,
              right: 0,
              child: VoiceConfirmationCard(
                response: _voiceResponse!,
                onConfirm: () => _handleVoiceConfirm('yes'),
                onCancel: () => _handleVoiceConfirm('cancel'),
                onDismiss: () => setState(() => _voiceResponse = null),
              ),
            ),
          if (_showVoiceOverlay && _voiceService != null)
            VoiceRecordingOverlay(
              voiceService: _voiceService!,
              transcript: _voiceService!.lastTranscript,
              speechResponse: _voiceResponse?.speechResponse,
              followUpPrompt: _voiceResponse?.followUpPrompt,
              onClose: () => setState(() => _showVoiceOverlay = false),
              onTextSubmit: _handleVoiceText,
            ),
        ],
      ),
      floatingActionButton: _voiceService != null
          ? VoiceFab(
              voiceService: _voiceService!,
              onTap: _onVoiceFabTap,
              onLongPress: () => setState(() => _showVoiceOverlay = true),
            )
          : null,
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
