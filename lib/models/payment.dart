class Payment {
  final String id;
  final String amount;
  final String status;
  final DateTime date;
  final String transactionId;

  Payment({
    this.id,
    this.amount,
    this.status,
    this.date,
    this.transactionId,
  });

  @override
  String toString() => 'Payment(id: $id, amount: $amount, status: $status)'.
}