import 'package:flutter/material.dart';

import 'api/auth_api.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'theme.dart';

void main() {
  runApp(InvoicePayApp(api: AuthApi()));
}

enum _Page { login, register, home }

class InvoicePayApp extends StatefulWidget {
  const InvoicePayApp({super.key, required this.api});

  final AuthApi api;

  @override
  State<InvoicePayApp> createState() => _InvoicePayAppState();
}

class _InvoicePayAppState extends State<InvoicePayApp> {
  _Page _page = _Page.login;
  String? _notice;

  void _show(_Page page, {String? notice}) {
    setState(() {
      _page = page;
      _notice = notice;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'InvoicePay',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: switch (_page) {
        _Page.login => LoginScreen(
          api: widget.api,
          notice: _notice,
          onLoggedIn: () => _show(_Page.home),
          onGoToRegister: () => _show(_Page.register),
        ),
        _Page.register => RegisterScreen(
          api: widget.api,
          onRegistered: () => _show(
            _Page.login,
            notice: 'Compte créé. Vous pouvez vous connecter.',
          ),
          onGoToLogin: () => _show(_Page.login),
        ),
        _Page.home => HomeScreen(
          api: widget.api,
          onLoggedOut: () => _show(_Page.login),
          onSessionExpired: () => _show(
            _Page.login,
            notice: 'Session expirée. Reconnectez-vous.',
          ),
        ),
      },
    );
  }
}
