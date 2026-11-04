import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:invoicepay/api/auth_api.dart';
import 'package:invoicepay/main.dart';

const _validPassword = 'MotDePasse123!';

Future<void> _pumpApp(WidgetTester tester, http.Client client) async {
  tester.view.physicalSize = const Size(1280, 1100);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(InvoicePayApp(api: AuthApi(client: client)));
}

http.Response _json(Object body, int status) => http.Response(
  jsonEncode(body),
  status,
  headers: {'content-type': 'application/json'},
);

void main() {
  testWidgets('la connexion vide affiche les erreurs sans appeler l\'API', (
    tester,
  ) async {
    var calls = 0;
    await _pumpApp(
      tester,
      MockClient((_) async {
        calls++;
        return _json({}, 200);
      }),
    );

    await tester.tap(find.widgetWithText(FilledButton, 'Se connecter'));
    await tester.pumpAndSettle();

    expect(find.text('Saisissez votre adresse email.'), findsOneWidget);
    expect(find.text('Saisissez votre mot de passe.'), findsOneWidget);
    expect(calls, 0);
  });

  testWidgets('des identifiants refuses affichent le message de l\'API', (
    tester,
  ) async {
    await _pumpApp(
      tester,
      MockClient((_) async => _json({'detail': 'Identifiants invalides.'}, 401)),
    );

    await tester.enterText(find.byType(TextFormField).at(0), 'a@test.com');
    await tester.enterText(find.byType(TextFormField).at(1), 'mauvais');
    await tester.tap(find.widgetWithText(FilledButton, 'Se connecter'));
    await tester.pumpAndSettle();

    expect(find.text('Identifiants invalides.'), findsOneWidget);
    expect(find.text('Vous êtes connecté'), findsNothing);
  });

  testWidgets('une connexion reussie affiche le profil puis se deconnecte', (
    tester,
  ) async {
    http.Request? meRequest;
    await _pumpApp(
      tester,
      MockClient((request) async {
        switch (request.url.path) {
          case '/auth/login':
            return _json({
              'access_token': 'jeton-acces',
              'refresh_token': 'jeton-refresh',
              'token_type': 'bearer',
            }, 200);
          case '/auth/me':
            meRequest = request;
            return _json({
              'email': 'a@test.com',
              'role': 'freelance',
              'is_email_verified': false,
            }, 200);
          case '/auth/logout':
            return http.Response('', 204);
        }
        return http.Response('', 404);
      }),
    );

    await tester.enterText(find.byType(TextFormField).at(0), 'a@test.com');
    await tester.enterText(find.byType(TextFormField).at(1), _validPassword);
    await tester.tap(find.widgetWithText(FilledButton, 'Se connecter'));
    await tester.pumpAndSettle();

    expect(find.text('Vous êtes connecté'), findsOneWidget);
    expect(find.text('a@test.com'), findsOneWidget);
    expect(meRequest!.headers['Authorization'], 'Bearer jeton-acces');

    await tester.tap(find.text('Se déconnecter'));
    await tester.pumpAndSettle();

    expect(find.text('Bon retour'), findsOneWidget);
  });

  testWidgets('l\'inscription refuse un mot de passe trop court', (tester) async {
    var calls = 0;
    await _pumpApp(
      tester,
      MockClient((_) async {
        calls++;
        return _json({}, 201);
      }),
    );

    await tester.tap(find.text('Créer un compte'));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField).at(0), 'a@test.com');
    await tester.enterText(find.byType(TextFormField).at(1), 'court');
    await tester.enterText(find.byType(TextFormField).at(2), 'court');
    await tester.tap(find.widgetWithText(FilledButton, 'Créer mon compte'));
    await tester.pumpAndSettle();

    expect(find.text('Au moins 12 caractères.'), findsOneWidget);
    expect(calls, 0);
  });

  testWidgets('une inscription reussie envoie le role et revient au login', (
    tester,
  ) async {
    Map<String, dynamic>? sent;
    await _pumpApp(
      tester,
      MockClient((request) async {
        sent = jsonDecode(request.body) as Map<String, dynamic>;
        return _json({}, 201);
      }),
    );

    await tester.tap(find.text('Créer un compte'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Entreprise'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).at(0), 'a@test.com');
    await tester.enterText(find.byType(TextFormField).at(1), _validPassword);
    await tester.enterText(find.byType(TextFormField).at(2), _validPassword);
    await tester.tap(find.widgetWithText(FilledButton, 'Créer mon compte'));
    await tester.pumpAndSettle();

    expect(sent!['role'], 'entreprise');
    expect(find.text('Compte créé. Vous pouvez vous connecter.'), findsOneWidget);
  });
}
