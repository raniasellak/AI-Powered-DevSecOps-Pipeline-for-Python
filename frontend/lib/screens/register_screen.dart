import 'package:flutter/material.dart';

import '../api/auth_api.dart';
import '../theme.dart';
import '../widgets/auth_layout.dart';

const _minPasswordLength = 12;

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({
    super.key,
    required this.api,
    required this.onRegistered,
    required this.onGoToLogin,
  });

  final AuthApi api;
  final VoidCallback onRegistered;
  final VoidCallback onGoToLogin;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  String _role = 'freelance';
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _confirm.dispose();
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
      await widget.api.register(
        email: _email.text.trim(),
        password: _password.text,
        role: _role,
      );
      widget.onRegistered();
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
    final length = _password.text.length;
    final progress = (length / _minPasswordLength).clamp(0.0, 1.0);
    final isLongEnough = length >= _minPasswordLength;

    return AuthLayout(
      title: 'Créer un compte',
      subtitle: 'Quelques informations suffisent pour commencer.',
      child: Form(
        key: _formKey,
        child: AutofillGroup(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_error != null) MessageBanner(message: _error!),
              const FieldLabel('Je suis'),
              SegmentedButton<String>(
                showSelectedIcon: false,
                segments: const [
                  ButtonSegment(
                    value: 'freelance',
                    label: Text('Freelance'),
                    icon: Icon(Icons.person_outline, size: 18),
                  ),
                  ButtonSegment(
                    value: 'entreprise',
                    label: Text('Entreprise'),
                    icon: Icon(Icons.apartment_outlined, size: 18),
                  ),
                ],
                selected: {_role},
                onSelectionChanged: (selection) =>
                    setState(() => _role = selection.first),
              ),
              const SizedBox(height: 18),
              const FieldLabel('Adresse email'),
              TextFormField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                autocorrect: false,
                validator: validateEmail,
                decoration: const InputDecoration(
                  hintText: 'vous@exemple.com',
                  prefixIcon: Icon(Icons.mail_outline, size: 20),
                ),
              ),
              const SizedBox(height: 18),
              const FieldLabel('Mot de passe'),
              PasswordField(
                controller: _password,
                autofillHint: AutofillHints.newPassword,
                onChanged: (_) => setState(() {}),
                validator: (value) =>
                    (value == null || value.length < _minPasswordLength)
                    ? 'Au moins $_minPasswordLength caractères.'
                    : null,
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: progress,
                  minHeight: 5,
                  backgroundColor: AppColors.border,
                  color: isLongEnough ? AppColors.accent : AppColors.navyLight,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                isLongEnough
                    ? 'Longueur suffisante.'
                    : '$length / $_minPasswordLength caractères minimum',
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 12.5,
                ),
              ),
              const SizedBox(height: 18),
              const FieldLabel('Confirmer le mot de passe'),
              PasswordField(
                controller: _confirm,
                autofillHint: AutofillHints.newPassword,
                onSubmitted: _submit,
                validator: (value) => value != _password.text
                    ? 'Les mots de passe ne correspondent pas.'
                    : null,
              ),
              const SizedBox(height: 26),
              SubmitButton(
                label: 'Créer mon compte',
                isLoading: _isLoading,
                onPressed: _submit,
              ),
              const SizedBox(height: 20),
              Wrap(
                alignment: WrapAlignment.center,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  const Text(
                    'Déjà inscrit ?',
                    style: TextStyle(color: AppColors.textMuted),
                  ),
                  TextButton(
                    onPressed: widget.onGoToLogin,
                    child: const Text('Se connecter'),
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
