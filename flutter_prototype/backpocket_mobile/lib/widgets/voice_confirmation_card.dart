import 'package:flutter/material.dart';
import '../models/voice_command_response.dart';

class VoiceConfirmationCard extends StatelessWidget {
  final VoiceCommandResponse response;
  final VoidCallback onConfirm;
  final VoidCallback onCancel;
  final VoidCallback? onDismiss;

  const VoiceConfirmationCard({
    super.key,
    required this.response,
    required this.onConfirm,
    required this.onCancel,
    this.onDismiss,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF211708),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: const Color(0xFFFBBF24).withAlpha(51)),
      ),
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  response.needsConfirmation
                      ? Icons.help_outline_rounded
                      : Icons.info_outline_rounded,
                  color: const Color(0xFFFBBF24),
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  _title(),
                  style: const TextStyle(
                    color: Color(0xFFFBBF24),
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
                const Spacer(),
                if (onDismiss != null)
                  GestureDetector(
                    onTap: onDismiss,
                    child: const Icon(Icons.close, color: Color(0x99FFFFFF), size: 18),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              response.speechResponse,
              style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
            ),
            if (response.result.isNotEmpty && !response.result.containsKey('error')) ...[
              const SizedBox(height: 8),
              _buildParamsSummary(),
            ],
            const SizedBox(height: 16),
            if (response.needsConfirmation) _buildConfirmButtons(),
            if (response.followUpPrompt != null && !response.needsConfirmation) ...[
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1208),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0x22FFFFFF)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.mic, color: Color(0xFFF97316), size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        response.followUpPrompt!,
                        style: const TextStyle(color: Color(0x99FFFFFF), fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  String _title() {
    if (response.needsConfirmation) return 'Confirm';
    if (response.action == 'collect') return 'Need more info';
    if (response.action == 'clarify') return 'Clarify';
    return 'Voice Result';
  }

  Widget _buildParamsSummary() {
    final entries = response.result.entries
        .where((e) => !e.key.startsWith('_') && e.key != 'error')
        .take(5);

    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: entries.map((e) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: const Color(0xFF1A1208),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            '${_formatKey(e.key)}: ${e.value}',
            style: const TextStyle(color: Color(0x99FFFFFF), fontSize: 11),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildConfirmButtons() {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton(
            onPressed: onCancel,
            style: OutlinedButton.styleFrom(
              foregroundColor: const Color(0x99FFFFFF),
              side: const BorderSide(color: Color(0x22FFFFFF)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
            child: const Text('Cancel'),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton(
            onPressed: onConfirm,
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFF97316),
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
            child: const Text('Confirm', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ),
      ],
    );
  }

  String _formatKey(String key) {
    return key.replaceAll('_', ' ').split(' ').map((w) {
      if (w.isEmpty) return w;
      return w[0].toUpperCase() + w.substring(1);
    }).join(' ');
  }
}
