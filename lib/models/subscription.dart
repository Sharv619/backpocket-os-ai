class Subscription {
  final String id;
  final String status;
  final String plan;
  final String statusMessage;
  final DateTime createdAt;
  final DateTime updatedAt;

  Subscription({
    this.id,
    this.status,
    this.plan,
    this.statusMessage,
    this.createdAt,
    this.updatedAt,
  });

  @override
  String toString() => 'Subscription(id: $id, status: $status, plan: $plan)'.
}