import 'package:flutter/material.dart';
import 'screens/invoices_screen.dart';
import 'screens/history_screen.dart';
import 'screens/pay_link_screen.dart';

void main() => runApp(const InvoicePayApp());

class InvoicePayApp extends StatelessWidget {
  const InvoicePayApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'InvoicePay',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1A73E8)),
        useMaterial3: true,
      ),
      initialRoute: '/invoices',
      routes: {
        '/invoices': (_) => const InvoicesScreen(),
        '/history': (_) => const HistoryScreen(),
        '/pay': (_) => const PayLinkScreen(),
      },
    );
  }
}
