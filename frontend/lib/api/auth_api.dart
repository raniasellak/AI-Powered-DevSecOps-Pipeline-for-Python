import 'dart:convert';

import 'package:http/http.dart' as http;

/// Adresse de l'API, modifiable au lancement : --dart-define=API_URL=...
const apiUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://localhost:8000',
);

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;
}

class UserProfile {
  UserProfile({
    required this.email,
    required this.role,
    required this.isEmailVerified,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
    email: json['email'] as String,
    role: json['role'] as String,
    isEmailVerified: json['is_email_verified'] as bool,
  );

  final String email;
  final String role;
  final bool isEmailVerified;
}

/// Les jetons restent en memoire uniquement : jamais dans localStorage,
/// lisible par tout script de la page en cas de XSS.
class AuthApi {
  AuthApi({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;
  String? _accessToken;
  String? _refreshToken;

  Future<void> register({
    required String email,
    required String password,
    required String role,
  }) async {
    final response = await _send(
      () => _client.post(
        Uri.parse('$apiUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'email': email, 'password': password, 'role': role}),
      ),
    );
    if (response.statusCode != 201) {
      throw _errorFrom(response);
    }
  }

  Future<void> login({required String email, required String password}) async {
    // /auth/login attend un formulaire OAuth2, pas du JSON
    final response = await _send(
      () => _client.post(
        Uri.parse('$apiUrl/auth/login'),
        body: {'username': email, 'password': password},
      ),
    );
    if (response.statusCode != 200) {
      throw _errorFrom(response);
    }
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    _accessToken = data['access_token'] as String;
    _refreshToken = data['refresh_token'] as String;
  }

  Future<UserProfile> me() async {
    final response = await _send(
      () => _client.get(
        Uri.parse('$apiUrl/auth/me'),
        headers: {'Authorization': 'Bearer $_accessToken'},
      ),
    );
    if (response.statusCode != 200) {
      throw _errorFrom(response);
    }
    return UserProfile.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<void> logout() async {
    final refreshToken = _refreshToken;
    _accessToken = null;
    _refreshToken = null;
    if (refreshToken == null) {
      return;
    }
    await _send(
      () => _client.post(
        Uri.parse('$apiUrl/auth/logout'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': refreshToken}),
      ),
    );
  }

  Future<http.Response> _send(Future<http.Response> Function() request) async {
    try {
      return await request().timeout(const Duration(seconds: 15));
    } on Exception {
      throw ApiException('Serveur injoignable. Réessayez dans un instant.');
    }
  }

  ApiException _errorFrom(http.Response response) {
    final status = response.statusCode;
    if (status == 422) {
      return ApiException(
        'Vérifiez les informations saisies.',
        statusCode: status,
      );
    }
    if (status == 429) {
      return ApiException(
        'Trop de tentatives. Réessayez plus tard.',
        statusCode: status,
      );
    }
    // Les messages 4xx de l'API sont volontairement generiques
    if (status >= 400 && status < 500) {
      try {
        final detail = (jsonDecode(response.body) as Map)['detail'];
        if (detail is String) {
          return ApiException(detail, statusCode: status);
        }
      } on FormatException {
        // reponse non JSON : message par defaut ci-dessous
      }
    }
    return ApiException(
      'Une erreur est survenue. Réessayez.',
      statusCode: status,
    );
  }
}
