class PendingEmail {
  final String refId;
  final String sender;
  final String subject;
  final int tier;
  final String tierLabel;
  final String preview;
  final double ageHours;

  PendingEmail({
    required this.refId,
    required this.sender,
    required this.subject,
    required this.tier,
    required this.tierLabel,
    required this.preview,
    required this.ageHours,
  });

  factory PendingEmail.fromJson(Map<String, dynamic> json) {
    return PendingEmail(
      refId: json['ref_id'] as String? ?? '',
      sender: json['sender'] as String? ?? '',
      subject: json['subject'] as String? ?? '',
      tier: json['tier'] as int? ?? 3,
      tierLabel: json['tier_label'] as String? ?? 'MEDIUM',
      preview: json['preview'] as String? ?? '',
      ageHours: (json['age_hours'] as num?)?.toDouble() ?? 0,
    );
  }
}
