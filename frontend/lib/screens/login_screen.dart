import 'package:flutter/material.dart';

import '../api/auth_api.dart';
import '../theme.dart';
import '../widgets/auth_layout.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({
    super.key,
    required this.api,
    required this.onLoggedIn,
    required this.onGoToRegister,
    this.notice,
  });

  final AuthApi api;
  final VoidCallback onLoggedIn;
  final VoidCallback onGoToRegister;
  final String? notice;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_isLoading || !_formKey.currentState!.validate()) {
      return;
    }
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      await widget.api.login(
        email: _email.text.trim(),
        password: _password.text,
      );
      widget.onLoggedIn();
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthLayout(
      title: 'Bon retour',
      subtitle: 'Connectez-vous pour retrouver vos missions et vos factures.',
      child: Form(
        key: _formKey,
        child: AutofillGroup(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (widget.notice != null && _error == null)
                MessageBanner(message: widget.notice!, isError: false),
              if (_error != null) MessageBanner(message: _error!),
              const FieldLabel('Adresse email'),
              TextFormField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.username],
                autocorrect: false,
                validator: validateEmail,
                onFieldSubmitted: (_) => _submit(),
                decoration: const InputDecoration(
                  hintText: 'vous@exemple.com',
                  prefixIcon: Icon(Icons.mail_outline, size: 20),
                ),
              ),
              const SizedBox(height: 18),
              const FieldLabel('Mot de passe'),
              PasswordField(
                controller: _password,
                autofillHint: AutofillHints.password,
                onSubmitted: _submit,
                validator: (value) => (value == null || value.isEmpty)
                    ? 'Saisissez votre mot de passe.'
                    : null,
              ),
              const SizedBox(height: 26),
              SubmitButton(
                label: 'Se connecter',
                isLoading: _isLoading,
                onPressed: _submit,
              ),
              const SizedBox(height: 20),
              Wrap(
                alignment: WrapAlignment.center,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  const Text(
                    'Pas encore de compte ?',
                    style: TextStyle(color: AppColors.textMuted),
                  ),
                  TextButton(
                    onPressed: widget.onGoToRegister,
                    child: const Text('Créer un compte'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
