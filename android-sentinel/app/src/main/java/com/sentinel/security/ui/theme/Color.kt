package com.sentinel.security.ui.theme

import androidx.compose.ui.graphics.Color

// Dark-native palette. Severity colors are chosen to stay distinguishable for the common
// color-vision deficiencies (teal/amber/red-magenta rather than pure green/yellow/red), and the
// UI never relies on color alone — every status also carries an icon + label.
val SentinelBackground = Color(0xFF0B0F14)
val SentinelSurface = Color(0xFF121821)
val SentinelSurfaceVariant = Color(0xFF1B2430)
val SentinelOnSurface = Color(0xFFE6EDF3)
val SentinelOnSurfaceMuted = Color(0xFF93A1B1)
val SentinelPrimary = Color(0xFF34D399)
val SentinelOnPrimary = Color(0xFF062018)
val SentinelOutline = Color(0xFF2C3A49)

// Severity scale (also exposed as an enum in the domain layer).
val SeverityOk = Color(0xFF34D399)       // teal-green
val SeverityInfo = Color(0xFF60A5FA)     // blue
val SeverityWarn = Color(0xFFF59E0B)     // amber
val SeverityHigh = Color(0xFFFB7185)     // rose
val SeverityCritical = Color(0xFFEF4444) // red
