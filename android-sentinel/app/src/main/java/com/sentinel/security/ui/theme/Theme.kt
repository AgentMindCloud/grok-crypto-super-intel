package com.sentinel.security.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val SentinelDarkColors = darkColorScheme(
    primary = SentinelPrimary,
    onPrimary = SentinelOnPrimary,
    background = SentinelBackground,
    onBackground = SentinelOnSurface,
    surface = SentinelSurface,
    onSurface = SentinelOnSurface,
    surfaceVariant = SentinelSurfaceVariant,
    onSurfaceVariant = SentinelOnSurfaceMuted,
    outline = SentinelOutline,
    error = SeverityCritical,
)

// Sentinel is intentionally dark-first; we keep a light scheme for accessibility/system pref but
// the app is tuned for the dark palette above.
private val SentinelLightColors = lightColorScheme(
    primary = SentinelPrimary,
    onPrimary = SentinelOnPrimary,
    error = SeverityCritical,
)

@Composable
fun SentinelTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) SentinelDarkColors else SentinelLightColors,
        typography = SentinelTypography,
        content = content,
    )
}
