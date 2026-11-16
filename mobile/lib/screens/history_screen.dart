import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Écran P3 — Historique des missions payées (dossier vérifiable)
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _api = const ApiService('TOKEN_PLACEHOLDER');
  List<dynamic> _entries = [];
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final data = await _api.getHistory();
      setState(() => _entries = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Historique des missions')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!))
              : _entries.isEmpty
                  ? const Center(child: Text('Aucune mission payée pour l\'instant.'))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        itemCount: _entries.length,
                        itemBuilder: (_, i) => _HistoryCard(entry: _entries[i], api: _api),
                      ),
                    ),
    );
  }
}

class _HistoryCard extends StatelessWidget {
  final Map<String, dynamic> entry;
  final ApiService api;
  const _HistoryCard({required this.entry, required this.api});

  @override
  Widget build(BuildContext context) {
    final mission = entry['mission'] as Map<String, dynamic>? ?? {};
    final invoice = entry['invoice'] as Map<String, dynamic>?;
    final proof = entry['blockchain_proof'] as Map<String, dynamic>?;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ExpansionTile(
        leading: const Icon(Icons.verified, color: Colors.green),
        title: Text(
          mission['title'] ?? '—',
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text('${mission['amount'] ?? '—'} MAD · ${_formatDate(mission['paid_at'])}'),
        children: [
          if (invoice != null)
            ListTile(
              leading: const Icon(Icons.receipt),
              title: Text('Facture ${invoice['number'] ?? ''}'),
              subtitle: Text('Hash : ${invoice['content_hash']?.substring(0, 16) ?? '—'}...'),
            ),
          if (proof != null)
            ListTile(
              leading: const Icon(Icons.link, color: Color(0xFF1A73E8)),
              title: const Text('Preuve blockchain'),
              subtitle: Text('TX : ${proof['tx_hash']?.substring(0, 16) ?? '—'}...'),
              onTap: () => _showProof(context, proof),
            ),
          if (proof == null)
            const ListTile(
              leading: Icon(Icons.hourglass_empty),
              title: Text('Preuve blockchain en attente'),
            ),
        ],
      ),
    );
  }

  void _showProof(BuildContext context, Map<String, dynamic> proof) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Preuve blockchain'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Hash facture :', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            SelectableText(proof['content_hash'] ?? '—',
                style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
            const SizedBox(height: 12),
            const Text('TX Hash :', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            SelectableText(proof['tx_hash'] ?? '—',
                style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
            const SizedBox(height: 12),
            Text('Ancré le : ${_formatDate(proof['anchored_at'])}',
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Fermer'),
          ),
        ],
      ),
    );
  }

  String _formatDate(String? iso) {
    if (iso == null) return '—';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year}';
    } catch (_) {
      return iso;
    }
  }
}
