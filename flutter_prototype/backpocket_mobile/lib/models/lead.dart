class Lead {
  final int id;
  final String clientName;
  final String email;
  final String jobType;
  final String location;
  final String urgency;
  final int estimatedBudget;
  final String status;
  final DateTime createdAt;

  Lead({
    required this.id,
    required this.clientName,
    required this.email,
    required this.jobType,
    required this.location,
    required this.urgency,
    required this.estimatedBudget,
    required this.status,
    required this.createdAt,
  });

  factory Lead.fromJson(Map<String, dynamic> json) {
    return Lead(
      id: json['id'] as int,
      clientName: json['client_name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      jobType: json['job_type'] as String? ?? '',
      location: json['location'] as String? ?? '',
      urgency: json['urgency'] as String? ?? '',
      estimatedBudget: json['estimated_budget'] as int? ?? 0,
      status: json['status'] as String? ?? 'new',
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'client_name': clientName,
    'email': email,
    'job_type': jobType,
    'location': location,
    'urgency': urgency,
    'estimated_budget': estimatedBudget,
    'status': status,
    'created_at': createdAt.toIso8601String(),
  };
}
