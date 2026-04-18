import 'package:flutter/material.dart';
import '../theme.dart';

class VoiceHelpScreen extends StatelessWidget {
  const VoiceHelpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.amber),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Voice Commands',
          style: TextStyle(color: AppColors.cream, fontWeight: FontWeight.bold),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildSection('Dashboard', Icons.dashboard_outlined, [
            '"What\'s going on today?" — Full business summary',
            '"How many emails?" — Pending email count',
            '"What\'s my pipeline?" — Revenue numbers',
          ]),
          _buildSection('Inbox', Icons.inbox_outlined, [
            '"Show me urgent emails" — Filter by tier',
            '"Approve the email to [name]" — Send draft',
            '"Read me [name]\'s email" — Read aloud',
            '"Make it more casual" — Revise draft',
          ]),
          _buildSection('Construction', Icons.build_outlined, [
            '"New lead: [name], [job], [suburb], [budget]" — Create lead',
            '"Create a quote for the [suburb] job" — Multi-turn quote',
            '"They accepted the [suburb] quote" — Update status',
            '"Record \$[amount] payment from [name]" — Log payment',
            '"What\'s the damage?" — Pipeline total',
            '"Draft a follow-up for the [suburb] quote" — AI follow-up',
          ]),
          _buildSection('Documents', Icons.description_outlined, [
            '"Show me my documents" — List docs',
            '"Scan a document" — Open camera',
            '"What does this receipt say?" — AI analysis',
          ]),
          _buildSection('Marketing', Icons.campaign_outlined, [
            '"Post about the [suburb] [job]" — Draft Google post',
            '"How\'s my local SEO?" — Marketing insights',
          ]),
          _buildSection('Instructions', Icons.rule_outlined, [
            '"New rule: [text]" — Add instruction',
            '"What rules do I have?" — List all',
            '"Delete the [keyword] one" — Remove',
          ]),
          _buildSection('Anytime', Icons.mic_rounded, [
            '"Go to [screen]" — Navigate',
            '"Hey Pip, [anything]" — Ask AI assistant',
            '"Undo that" — Revert last action (60s)',
            '"Help" — Show this screen',
          ]),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.amber.withAlpha(51)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text(
                  'Tradie Slang',
                  style: TextStyle(color: AppColors.amber, fontWeight: FontWeight.bold, fontSize: 14),
                ),
                SizedBox(height: 8),
                Text(
                  '"Chuck a quote together" = Create quote\n'
                  '"Give it the tick" = Approve\n'
                  '"Knock it back" = Reject\n'
                  '"What\'s the damage" = Pipeline total\n'
                  '"Bang out an invoice" = Generate invoice\n'
                  '"Fire off that email" = Send\n'
                  '"Suss out" = Analyze/review\n'
                  '"That bloke in [suburb]" = Fuzzy match by location',
                  style: TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.6),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSection(String title, IconData icon, List<String> commands) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: ExpansionTile(
        leading: Icon(icon, color: AppColors.amber, size: 20),
        title: Text(
          title,
          style: const TextStyle(color: AppColors.cream, fontWeight: FontWeight.w600, fontSize: 14),
        ),
        iconColor: AppColors.textDim,
        collapsedIconColor: AppColors.textDim,
        childrenPadding: const EdgeInsets.only(left: 16, right: 16, bottom: 12),
        children: commands.map((cmd) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Icon(Icons.arrow_right, color: AppColors.textMuted, size: 14),
                ),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    cmd,
                    style: const TextStyle(color: AppColors.textDim, fontSize: 13, height: 1.4),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}
