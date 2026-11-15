import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Écran P3 — Liste des factures du freelance connecté
class InvoicesScreen extends StatefulWidget {
  const InvoicesScreen({super.key});

  @override
  State<InvoicesScreen> createState() => _InvoicesScreenState();
}

class _InvoicesScreenState extends State<InvoicesScreen> {
  // TODO: récupérer le token depuis le provider d'auth (P1)
  final _api = const ApiService('TOKEN_PLACEHOLDER');
  List<dynamic> _invoices = [];
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
      final history = await _api.getHistory();
      setState(() {
        _invoices = history
            .where((e) => e['invoice'] != null)
            .map((e) => e['invoice'])
            .toList();
      });
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mes Factures'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'Historique',
            onPressed: () => Navigator.pushNamed(context, '/history'),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ErrorView(message: _error!, onRetry: _load)
              : _invoices.isEmpty
                  ? const Center(child: Text('Aucune facture pour l\'instant.'))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        itemCount: _invoices.length,
                        itemBuilder: (_, i) => _InvoiceCard(
                          invoice: _invoices[i],
                          api: _api,
                        ),
                      ),
                    ),
    );
  }
}

class _InvoiceCard extends StatelessWidget {
  final Map<String, dynamic> invoice;
  final ApiService api;

  const _InvoiceCard({required this.invoice, required this.api});

  @override
  Widget build(BuildContext context) {
    final number = invoice['number'] ?? '—';
    final amount = invoice['amount']?.toString() ?? '—';
    final used = invoice['token_used'] == true;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: const Icon(Icons.receipt_long, color: Color(0xFF1A73E8)),
        title: Text(number, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text('$amount MAD'),
        trailing: used
            ? const Chip(label: Text('Payée'))
            : ElevatedButton(
                onPressed: () => _showPayLink(context, invoice['id']),
                child: const Text('Lien de paiement'),
              ),
      ),
    );
  }

  Future<void> _showPayLink(BuildContext context, String invoiceId) async {
    try {
      final result = await api.getPayLink(invoiceId);
      if (!context.mounted) return;
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Lien de paiement'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SelectableText(result['pay_url'] ?? ''),
              const SizedBox(height: 8),
              Text(
                'Expire le : ${result['expires_at'] ?? ''}',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
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
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur : $e')),
      );
    }
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorView({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 8),
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: onRetry, child: const Text('Réessayer')),
        ],
      ),
    );
  }
}
