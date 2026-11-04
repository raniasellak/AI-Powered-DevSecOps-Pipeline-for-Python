import 'package:flutter/material.dart';

class AppColors {
  static const navy = Color(0xFF0B1F3A);
  static const navyLight = Color(0xFF16345C);
  static const accent = Color(0xFF14B8A6);
  static const accentDark = Color(0xFF0F766E);
  static const background = Color(0xFFF5F7FA);
  static const border = Color(0xFFD9DFE7);
  static const textMuted = Color(0xFF5B6B7F);
  static const error = Color(0xFFB3261E);
  static const errorBackground = Color(0xFFFDECEA);
  static const success = Color(0xFF0F766E);
  static const successBackground = Color(0xFFE3F7F3);
}

ThemeData buildTheme() {
  final border = OutlineInputBorder(
    borderRadius: BorderRadius.circular(10),
    borderSide: const BorderSide(color: AppColors.border),
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.accentDark,
      primary: AppColors.accentDark,
      error: AppColors.error,
    ),
    scaffoldBackgroundColor: AppColors.background,
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
      border: border,
      enabledBorder: border,
      focusedBorder: border.copyWith(
        borderSide: const BorderSide(color: AppColors.accentDark, width: 1.6),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.navy,
        foregroundColor: Colors.white,
        minimumSize: const Size.fromHeight(52),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      ),
    ),
  );
}
