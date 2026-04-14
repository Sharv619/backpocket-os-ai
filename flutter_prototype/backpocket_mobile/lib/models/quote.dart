class Quote {
  final int id;
  final int leadId;
  final double materialsCost;
  final double laborHours;
  final int markupPercent;
  final String status;
  final DateTime createdAt;

  Quote({
    required this.id,
    required this.leadId,
    required this.materialsCost,
    required this.laborHours,
    required this.markupPercent,
    required this.status,
    required this.createdAt,
  });

  double get laborCost => laborHours * 85;
  double get subtotal => materialsCost + laborCost;
  double get total => subtotal * (1 + markupPercent / 100);

  factory Quote.fromJson(Map<String, dynamic> json) {
    return Quote(
      id: json['id'] as int,
      leadId: json['lead_id'] as int,
      materialsCost: (json['materials_cost'] as num?)?.toDouble() ?? 0,
      laborHours: (json['labor_hours'] as num?)?.toDouble() ?? 0,
      markupPercent: json['markup_percent'] as int? ?? 20,
      status: json['status'] as String? ?? 'pending',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'lead_id': leadId,
    'materials_cost': materialsCost,
    'labor_hours': laborHours,
    'markup_percent': markupPercent,
    'status': status,
    'created_at': createdAt.toIso8601String(),
  };
}
