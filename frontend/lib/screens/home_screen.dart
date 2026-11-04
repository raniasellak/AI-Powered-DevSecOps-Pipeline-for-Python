import 'package:flutter/material.dart';

import '../api/auth_api.dart';
import '../theme.dart';
import '../widgets/auth_layout.dart';

const _roleLabels = {
  'freelance': 'Freelance',
  'entreprise': 'Entreprise',
  'admin': 'Administrateur',
};

class HomeScreen extends StatefulWidget {
  const HomeScreen({
    super.key,
    required this.api,
    required this.onLoggedOut,
    required this.onSessionExpired,
  });

  final AuthApi api;
  final VoidCallback onLoggedOut;
  final VoidCallback onSessionExpired;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  UserProfile? _profile;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _error = null);
    try {
      final profile = await widget.api.me();
      if (mounted) {
        setState(() => _profile = profile);
      }
    } on ApiException catch (e) {
      if (e.statusCode == 401) {
        widget.onSessionExpired();
      } else if (mounted) {
        setState(() => _error = e.message);
      }
    }
  }

  Future<void> _logout() async {
    try {
      await widget.api.logout();
    } on ApiException {
      // Les jetons locaux sont deja effaces : on revient quand meme au login
    }
    widget.onLoggedOut();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        shape: const Border(bottom: BorderSide(color: AppColors.border)),
        titleSpacing: 24,
        title: const BrandLogo(),
        actions: [
          TextButton.icon(
            onPressed: _logout,
            icon: const Icon(Icons.logout, size: 18),
            label: const Text('Se déconnecter'),
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: _buildContent(),
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {
    if (_error != null) {
      return Column(
        children: [
          MessageBanner(message: _error!),
          OutlinedButton(
            onPressed: _loadProfile,
            child: const Text('Réessayer'),
          ),
        ],
      );
    }
    final profile = _profile;
    if (profile == null) {
      return const CircularProgressIndicator();
    }
    return Container(
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: AppColors.successBackground,
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(
              Icons.verified_user_outlined,
              color: AppColors.accentDark,
              size: 26,
            ),
          ),
          const SizedBox(height: 18),
          const Text(
            'Vous êtes connecté',
            style: TextStyle(
              color: AppColors.navy,
              fontSize: 24,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Votre session est active. Les prochains modules arriveront ici.',
            style: TextStyle(color: AppColors.textMuted, fontSize: 15),
          ),
          const SizedBox(height: 22),
          const Divider(color: AppColors.border, height: 1),
          _InfoRow(label: 'Email', value: profile.email),
          _InfoRow(
            label: 'Profil',
            value: _roleLabels[profile.role] ?? profile.role,
          ),
          _InfoRow(
            label: 'Email vérifié',
            value: profile.isEmailVerified ? 'Oui' : 'Pas encore',
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 14),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: AppColors.navy,
                fontSize: 14,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
