import 'package:flutter/material.dart';
import '../theme.dart';

const _stages = [
  (1, 'New Lead'),
  (2, 'Contacted'),
  (3, 'Site Visit'),
  (4, 'Quoting'),
  (5, 'Quote Sent'),
  (6, 'Negotiating'),
  (7, 'Accepted'),
  (8, 'In Progress'),
  (9, 'Complete'),
];

class WorkflowStageTracker extends StatelessWidget {
  final int currentStage;
  final void Function(int stage)? onStageTap;
  final bool compact;

  const WorkflowStageTracker({
    super.key,
    required this.currentStage,
    this.onStageTap,
    this.compact = false,
  });

  Color _stageColor(int stage) {
    if (stage < currentStage) return AppColors.amber.withAlpha(180);
    if (stage == currentStage) return AppColors.amber;
    return AppColors.border;
  }

  @override
  Widget build(BuildContext context) {
    if (compact) return _buildCompact();
    return _buildFull();
  }

  Widget _buildCompact() {
    return Row(
      children: [
        Text(
          'Stage $currentStage',
          style: const TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.bold),
        ),
        const SizedBox(width: 6),
        Text(
          _stages[currentStage - 1].$2,
          style: const TextStyle(color: AppColors.textDim, fontSize: 12),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: currentStage / 9,
              backgroundColor: AppColors.border,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.amber),
              minHeight: 4,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildFull() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: List.generate(_stages.length, (i) {
              final (stageNum, label) = _stages[i];
              final isLast = i == _stages.length - 1;
              final isDone = stageNum < currentStage;
              final isCurrent = stageNum == currentStage;

              return Row(
                children: [
                  GestureDetector(
                    onTap: onStageTap != null ? () => onStageTap!(stageNum) : null,
                    child: Column(
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: isCurrent ? 28 : 22,
                          height: isCurrent ? 28 : 22,
                          decoration: BoxDecoration(
                            color: _stageColor(stageNum),
                            shape: BoxShape.circle,
                            border: isCurrent
                                ? Border.all(color: AppColors.amber, width: 2)
                                : null,
                          ),
                          child: Center(
                            child: isDone
                                ? const Icon(Icons.check, size: 12, color: AppColors.brown)
                                : Text(
                                    '$stageNum',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: isCurrent ? AppColors.brown : AppColors.textMuted,
                                    ),
                                  ),
                          ),
                        ),
                        const SizedBox(height: 4),
                        SizedBox(
                          width: 56,
                          child: Text(
                            label,
                            textAlign: TextAlign.center,
                            style: TextStyle(
                              fontSize: 9,
                              color: isCurrent ? AppColors.cream : AppColors.textMuted,
                              fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (!isLast)
                    Container(
                      width: 20,
                      height: 2,
                      margin: const EdgeInsets.only(bottom: 20),
                      color: isDone ? AppColors.amber.withAlpha(180) : AppColors.border,
                    ),
                ],
              );
            }),
          ),
        ),
      ],
    );
  }
}
