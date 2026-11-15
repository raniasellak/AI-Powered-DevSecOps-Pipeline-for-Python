import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Écran P3 — Page de paiement par lien signé
/// Accessible via /pay?token=xxx (lien reçu par email)
class PayLinkScreen extends StatefulWidget {
  const PayLinkScreen({super.key});

  @override
  State<PayLinkScreen> createState() => _PayLinkScreenState();
}

class _PayLinkScreenState extends State<PayLinkScreen> {
  // Pas besoin d'auth — le token est dans l'URL
  final _api = const ApiService('');
  Map<String, dynamic>? _invoice;
  bool _loading = false;
  String? _error;
  bool _paid = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Récupère le token depuis les arguments de route
    final token = ModalRoute.of(context)?.settings.arguments as String?;
    if (token != null && _invoice == null) {
      _loadInvoice(token);
    }
  }

  Future<void> _loadInvoice(String token) async {
    setState(() { _loading = true; _error = null; });
    try {
      // GET /pay/{token} — consomme le lien et retourne la facture
      final res = await _api.getInvoice('pay/$token');
      setState(() => _invoice = res);
    } catch (e) {
      setState(() => _error = _friendlyError(e.toString()));
    } finally {
      setState(() => _loading = false);
    }
  }

  String _friendlyError(String raw) {
    if (raw.contains('expiré')) return 'Ce lien de paiement a expiré.';
    if (raw.contains('utilisé')) return 'Ce lien a déjà été utilisé.';
    if (raw.contains('invalide')) return 'Lien invalide.';
    return 'Une erreur est survenue.';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Paiement de facture')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _ExpiredView(message: _error!)
              : _paid
                  ? const _SuccessView()
                  : _invoice != null
                      ? _PayView(
                          invoice: _invoice!,
                          onPay: () => setState(() => _paid = true),
                        )
                      : const Center(child: Text('Chargement...')),
    );
  }
}

class _PayView extends StatelessWidget {
  final Map<String, dynamic> invoice;
  final VoidCallback onPay;
  const _PayView({required this.invoice, required this.onPay});

  @override
  Widget build(BuildContext context) {
    final number = invoice['number'] ?? '—';
    final ht = double.tryParse(invoice['amount'].toString()) ?? 0;
    final taxRate = double.tryParse(invoice['tax_rate'].toString()) ?? 0.20;
    final tva = ht * taxRate;
    final ttc = ht + tva;

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.receipt_long, size: 48, color: Color(0xFF1A73E8)),
          const SizedBox(height: 16),
          Text('Facture $number',
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 24),
          _Row('Montant HT', '${ht.toStringAsFixed(2)} MAD'),
          _Row('TVA (${(taxRate * 100).toInt()} %)', '${tva.toStringAsFixed(2)} MAD'),
          const Divider(height: 32),
          _Row('Total TTC', '${ttc.toStringAsFixed(2)} MAD', bold: true),
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: onPay,
              icon: const Icon(Icons.lock),
              label: const Text('Payer maintenant (sandbox)'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ),
          const SizedBox(height: 12),
          const Center(
            child: Text(
              'Paiement sécurisé 3-D Secure · Sandbox',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;
  const _Row(this.label, this.value, {this.bold = false});

  @override
  Widget build(BuildContext context) {
    final style = bold
        ? const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)
        : const TextStyle(fontSize: 15);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(label, style: style), Text(value, style: style)],
      ),
    );
  }
}

class _SuccessView extends StatelessWidget {
  const _SuccessView();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.check_circle, size: 80, color: Colors.green),
          SizedBox(height: 16),
          Text('Paiement effectué',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text('Un reçu a été envoyé par email.', style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }
}

class _ExpiredView extends StatelessWidget {
  final String message;
  const _ExpiredView({required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.link_off, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(message,
              style: const TextStyle(fontSize: 18),
              textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
