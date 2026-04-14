class Payment {
  final int id;
  final int quoteId;
  final double amount;
  final DateTime paidAt;

  Payment({
    required this.id,
    required this.quoteId,
    required this.amount,
    required this.paidAt,
  });

  factory Payment.fromJson(Map<String, dynamic> json) {
    return Payment(
      id: json['id'] as int,
      quoteId: json['quote_id'] as int,
      amount: (json['amount'] as num?)?.toDouble() ?? 0,
      paidAt: json['paid_at'] != null
          ? DateTime.parse(json['paid_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'quote_id': quoteId,
    'amount': amount,
    'paid_at': paidAt.toIso8601String(),
  };
}
