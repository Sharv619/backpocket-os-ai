import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';

class ClientCrmScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const ClientCrmScreen({super.key, required this.serverUrl, required this.apiKey});

  @override
  _ClientCrmScreenState createState() => _ClientCrmScreenState();
}

class _ClientCrmScreenState extends State<ClientCrmScreen> {
  late ApiService _apiService;
  List<dynamic> _clients = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _fetchClients();
  }

  Future<void> _fetchClients() async {
    try {
      final data = await _apiService.getClientMaster();
      setState(() {
        _clients = data['clients'] ?? [];
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
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _clients.isEmpty
              ? const Center(child: Text('No clients in BPS_Client_Master yet.', style: TextStyle(color: AppColors.textDim)))
              : ListView.builder(
                  itemCount: _clients.length,
                  itemBuilder: (context, index) {
                    final client = _clients[index];
                    return Card(
                      color: AppColors.card,
                      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
                      child: ListTile(
                        title: Text('${client['first_name']} ${client['last_name']}', style: const TextStyle(color: Colors.white)),
                        subtitle: Text(client['primary_email'] ?? '', style: const TextStyle(color: AppColors.textDim)),
                        trailing: Text(client['client_status'] ?? '', style: const TextStyle(color: AppColors.amber)),
                      ),
                    );
                  },
                ),
    );
  }
}
