import 'dart:convert';
import 'package:http/http.dart' as http;

const String _baseUrl = 'http://localhost:8000/v1';

class ApiService {
  final String token;
  const ApiService(this.token);

  Map<String, String> get _headers => {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      };

  // Récupère les factures d'une mission
  Future<Map<String, dynamic>> getInvoice(String invoiceId) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/invoices/$invoiceId'),
      headers: _headers,
    );
    _check(res);
    return jsonDecode(res.body);
  }

  // Génère le lien de paiement signé
  Future<Map<String, dynamic>> getPayLink(String invoiceId) async {
    final res = await http.post(
      Uri.parse('$_baseUrl/invoices/$invoiceId/pay-link'),
      headers: _headers,
    );
    _check(res);
    return jsonDecode(res.body);
  }

  // Historique des missions payées du freelance connecté
  Future<List<dynamic>> getHistory() async {
    final res = await http.get(
      Uri.parse('$_baseUrl/me/history'),
      headers: _headers,
    );
    _check(res);
    return jsonDecode(res.body);
  }

  // Preuve blockchain d'une facture
  Future<Map<String, dynamic>> getProof(String invoiceId) async {
    final res = await http.get(
      Uri.parse('$_baseUrl/invoices/$invoiceId/proof'),
      headers: _headers,
    );
    _check(res);
    return jsonDecode(res.body);
  }

  void _check(http.Response res) {
    if (res.statusCode >= 400) {
      throw Exception('Erreur API ${res.statusCode}: ${res.body}');
    }
  }
}
