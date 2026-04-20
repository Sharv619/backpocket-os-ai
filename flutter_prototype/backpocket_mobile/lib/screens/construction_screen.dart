import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme.dart';
import 'voice_input_screen.dart';

class ConstructionScreen extends StatefulWidget {
  final String serverUrl;
  final String apiKey;

  const ConstructionScreen({
    super.key,
    required this.serverUrl,
    required this.apiKey,
  });

  @override
  State<ConstructionScreen> createState() => _ConstructionScreenState();
}

class _ConstructionScreenState extends State<ConstructionScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  late ApiService _apiService;

  List<dynamic> _leads = [];
  List<dynamic> _quotes = [];
  List<dynamic> _payments = [];
  Map<String, dynamic>? _pipeline;

  bool _loading = false;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _apiService = ApiService(baseUrl: widget.serverUrl, apiKey: widget.apiKey);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _error = '';
    });

    try {
      final leads = await _apiService.getConstructionLeads();
      final quotes = await _apiService.getConstructionQuotes();
      final payments = await _apiService.getConstructionPayments();
      final pipeline = await _apiService.getConstructionPipeline();

      setState(() {
        _leads = leads;
        _quotes = quotes;
        _payments = payments;
        _pipeline = pipeline;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
      debugPrint('Construction load error: $e');
    }

    setState(() => _loading = false);
  }

  Color _getStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'accepted':
      case 'paid':
        return AppColors.green;
      case 'sent':
      case 'pending':
        return AppColors.amber;
      case 'draft':
        return Colors.grey;
      default:
        return Colors.red;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.bgDark, Color(0xFF1A1008), Color(0xFF2D1A00)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Column(
        children: [
          // Header
          Container(
            color: Colors.black45,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '🏗️ Construction',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Leads • Quotes • Payments',
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[400],
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.amber.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        '${_pipeline?['total_quotes'] ?? 0} Quotes',
                        style: const TextStyle(
                          color: AppColors.amber,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                // Pipeline Summary — field names match backend get_pipeline_summary()
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _PipelineCounter(
                      label: 'Total',
                      count: _pipeline?['total_quotes'] ?? 0,
                      color: Colors.grey,
                    ),
                    _PipelineCounter(
                      label: 'Sent',
                      count: _pipeline?['pending_quotes'] ?? 0,
                      color: AppColors.amber,
                    ),
                    _PipelineCounter(
                      label: 'Accepted',
                      count: _pipeline?['accepted_quotes'] ?? 0,
                      color: AppColors.green,
                    ),
                    Column(
                      children: [
                        Text(
                          '\$${(_pipeline?['revenue_pipeline'] ?? 0).toStringAsFixed(0)}',
                          style: const TextStyle(
                            color: AppColors.green,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Text(
                          'Revenue',
                          style: TextStyle(
                            color: Colors.grey,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Tabs
          Container(
            color: Colors.black26,
            child: TabBar(
              controller: _tabController,
              tabs: const [
                Tab(text: '📋 Leads', icon: SizedBox.shrink()),
                Tab(text: '💰 Quotes', icon: SizedBox.shrink()),
                Tab(text: '💳 Payments', icon: SizedBox.shrink()),
              ],
              indicator: UnderlineTabIndicator(
                borderSide: BorderSide(color: AppColors.amber, width: 3),
              ),
              labelColor: AppColors.amber,
              unselectedLabelColor: Colors.grey,
            ),
          ),
          // Content
          Expanded(
            child: _loading
                ? const Center(
                    child: CircularProgressIndicator(color: AppColors.amber),
                  )
                : _error.isNotEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Text(
                              '⚠️ Error',
                              style: TextStyle(
                                color: Colors.red,
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              _error,
                              textAlign: TextAlign.center,
                              style: const TextStyle(
                                color: Colors.grey,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 20),
                            ElevatedButton.icon(
                              icon: const Icon(Icons.refresh),
                              label: const Text('Retry'),
                              onPressed: _loadData,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.amber,
                              ),
                            ),
                          ],
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildLeadsTab(),
                          _buildQuotesTab(),
                          _buildPaymentsTab(),
                        ],
                      ),
          ),
          // Refresh Button
          Container(
            padding: const EdgeInsets.all(12),
            child: ElevatedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh'),
              onPressed: _loadData,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.amber,
                foregroundColor: Colors.black,
                minimumSize: const Size.fromHeight(44),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _openVoiceEnquiry() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => VoiceInputScreen(
          serverUrl: widget.serverUrl,
          apiKey: widget.apiKey,
          screenContext: 'construction',
        ),
      ),
    ).then((_) => _loadData()); // refresh after returning
  }

  void _goToQuoteTab({Map<String, dynamic>? fromLead}) {
    _tabController.animateTo(1);
    if (fromLead != null) {
      _showCreateQuoteSheet(fromLead);
    }
  }

  void _showCreateQuoteSheet(Map<String, dynamic> lead) {
    final materialsCtrl = TextEditingController(text: '0');
    final hoursCtrl = TextEditingController(text: '2');
    final markupCtrl = TextEditingController(text: '20');

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 16, right: 16, top: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Quote for ${lead['client_name']}',
              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(lead['job_type'] ?? '', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 16),
            _QuoteField(controller: materialsCtrl, label: 'Materials cost (\$)'),
            const SizedBox(height: 8),
            _QuoteField(controller: hoursCtrl, label: 'Labour hours'),
            const SizedBox(height: 8),
            _QuoteField(controller: markupCtrl, label: 'Markup %'),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.amber,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () async {
                  Navigator.pop(ctx);
                  try {
                    await _apiService.createQuote(
                      leadId: lead['id'] as int,
                      clientName: lead['client_name'] as String? ?? '',
                      jobType: lead['job_type'] as String? ?? '',
                      materialsCost: double.tryParse(materialsCtrl.text) ?? 0,
                      laborCost: (double.tryParse(hoursCtrl.text) ?? 2) * 150,
                      markupPercent: double.tryParse(markupCtrl.text) ?? 20,
                    );
                    _loadData();
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red),
                      );
                    }
                  }
                },
                child: const Text('Create Quote', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showRecordPaymentSheet(Map<String, dynamic> quote) {
    final amountCtrl = TextEditingController(
      text: (quote['total_amount'] ?? '').toString(),
    );

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: 16, right: 16, top: 20,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Record Payment — ${quote['client_name']}',
              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _QuoteField(controller: amountCtrl, label: 'Amount received (\$)'),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.green,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                onPressed: () async {
                  Navigator.pop(ctx);
                  try {
                    await _apiService.recordPayment(
                      quoteId: quote['id'] as int,
                      amount: double.tryParse(amountCtrl.text) ?? 0,
                    );
                    _tabController.animateTo(2);
                    _loadData();
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Error: $e'), backgroundColor: AppColors.red),
                      );
                    }
                  }
                },
                child: const Text('Record Payment', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLeadsTab() {
    return Stack(
      children: [
        _leads.isEmpty
            ? Center(child: Text('No leads yet.\nTap mic to log a new enquiry.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[400])))
            : RefreshIndicator(
                onRefresh: _loadData,
                color: AppColors.amber,
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(12, 12, 12, 80),
                  itemCount: _leads.length,
                  itemBuilder: (context, index) {
                    final lead = _leads[index];
                    return _LeadCard(
                      lead: lead,
                      onCreateQuote: () => _goToQuoteTab(fromLead: lead as Map<String, dynamic>),
                    );
                  },
                ),
              ),
        Positioned(
          bottom: 16,
          right: 16,
          child: FloatingActionButton.extended(
            onPressed: _openVoiceEnquiry,
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            icon: const Icon(Icons.mic),
            label: const Text('New Enquiry', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  Widget _buildQuotesTab() {
    if (_quotes.isEmpty) {
      return Center(child: Text('No quotes yet', style: TextStyle(color: Colors.grey[400])));
    }
    return RefreshIndicator(
      onRefresh: _loadData,
      color: AppColors.amber,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _quotes.length,
        itemBuilder: (context, index) {
          final quote = _quotes[index];
          return _QuoteCard(
            quote: quote,
            statusColor: _getStatusColor(quote['status'] ?? 'draft'),
            onRecordPayment: () => _showRecordPaymentSheet(quote as Map<String, dynamic>),
          );
        },
      ),
    );
  }

  Widget _buildPaymentsTab() {
    if (_payments.isEmpty) {
      return Center(
        child: Text(
          'No payments yet',
          style: TextStyle(color: Colors.grey[400]),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      color: AppColors.amber,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _payments.length,
        itemBuilder: (context, index) {
          final payment = _payments[index];
          return _PaymentCard(payment: payment);
        },
      ),
    );
  }
}

class _PipelineCounter extends StatelessWidget {
  final String label;
  final int count;
  final Color color;

  const _PipelineCounter({
    required this.label,
    required this.count,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          '$count',
          style: TextStyle(
            color: color,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: Colors.grey,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

class _QuoteField extends StatelessWidget {
  final TextEditingController controller;
  final String label;
  const _QuoteField({required this.controller, required this.label});

  @override
  Widget build(BuildContext context) => TextField(
    controller: controller,
    keyboardType: TextInputType.number,
    style: const TextStyle(color: Colors.white),
    decoration: InputDecoration(
      labelText: label,
      labelStyle: const TextStyle(color: AppColors.textMuted),
      filled: true,
      fillColor: AppColors.card,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
    ),
  );
}

class _LeadCard extends StatelessWidget {
  final dynamic lead;
  final VoidCallback? onCreateQuote;

  const _LeadCard({required this.lead, this.onCreateQuote});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  lead['client_name'] ?? 'Unknown',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  lead['urgency']?.toString().toUpperCase() ?? 'LOW',
                  style: const TextStyle(
                    color: Colors.amber,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            lead['job_type'] ?? 'Unknown Job',
            style: TextStyle(
              color: Colors.grey[400],
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                lead['location'] ?? 'Unknown',
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
              Text(
                '\$${lead['estimated_budget'] ?? 0}',
                style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ],
          ),
          if (onCreateQuote != null) ...[
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: onCreateQuote,
                icon: const Icon(Icons.request_quote_outlined, size: 15, color: AppColors.amber),
                label: const Text('Create Quote →', style: TextStyle(color: AppColors.amber, fontSize: 12)),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _QuoteCard extends StatelessWidget {
  final dynamic quote;
  final Color statusColor;
  final VoidCallback? onRecordPayment;

  const _QuoteCard({required this.quote, required this.statusColor, this.onRecordPayment});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      quote['client_name'] ?? 'Unknown',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      quote['job_type'] ?? 'Unknown Job',
                      style: TextStyle(
                        color: Colors.grey[400],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '\$${quote['total_amount'] ?? 0}',
                    style: const TextStyle(
                      color: Colors.green,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      (quote['status'] ?? 'draft').toUpperCase(),
                      style: TextStyle(
                        color: statusColor,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Materials: \$${quote['materials_cost'] ?? 0}',
                style: TextStyle(color: Colors.grey[400], fontSize: 11),
              ),
              Text(
                'Labor: \$${(quote['labor_cost'] ?? 0)} (${quote['markup_percent'] ?? 0}%)',
                style: TextStyle(color: Colors.grey[400], fontSize: 11),
              ),
            ],
          ),
          if (onRecordPayment != null && (quote['status'] ?? '') != 'paid') ...[
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: onRecordPayment,
                icon: const Icon(Icons.payments_outlined, size: 15, color: AppColors.green),
                label: const Text('Record Payment →', style: TextStyle(color: AppColors.green, fontSize: 12)),
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PaymentCard extends StatelessWidget {
  final dynamic payment;

  const _PaymentCard({required this.payment});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  payment['client_name'] ?? 'Unknown',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.green.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text(
                  'PAID',
                  style: TextStyle(
                    color: Colors.green,
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Amount: \$${payment['amount'] ?? 0}',
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            'Received: ${payment['received_date'] ?? 'N/A'}',
            style: TextStyle(
              color: Colors.grey[400],
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}
