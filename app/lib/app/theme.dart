// Deliberate visual identity, not Flutter defaults.
// Direction: "bioluminescent lab" -- near-black deep-teal surfaces (a camera
// app lives in the dark) with a single luminous cyan accent reserved for the
// one thing that matters: the scan action. Everything else stays quiet.
import 'package:flutter/material.dart';

const scanGlow = Color(0xFF35E0C8);   // the accent. Used sparingly.
const inkDeep = Color(0xFF0A1214);    // app background
const inkRaised = Color(0xFF121D20);  // cards, fields
const mistText = Color(0xFFDCE7E5);   // primary text

ThemeData buildTheme() {
  final base = ThemeData.dark(useMaterial3: true);
  return base.copyWith(
    scaffoldBackgroundColor: inkDeep,
    colorScheme: base.colorScheme.copyWith(
      primary: scanGlow,
      surface: inkRaised,
      onSurface: mistText,
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: inkRaised,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide.none,
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: scanGlow,
        foregroundColor: inkDeep,
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
      ),
    ),
  );
}
