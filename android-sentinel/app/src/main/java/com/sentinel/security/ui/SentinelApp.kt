package com.sentinel.security.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sentinel.security.ui.onboarding.OnboardingFlow

/**
 * Root composable. Decides between the onboarding flow and the main app based on persisted
 * onboarding state, showing a brief loading state while DataStore resolves.
 */
@Composable
fun SentinelApp() {
    val gate: AppGateViewModel = hiltViewModel()
    val settings by gate.settings.collectAsStateWithLifecycle()

    when {
        settings == null -> {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        }

        !settings!!.onboardingComplete -> {
            OnboardingFlow()
        }

        else -> {
            MainNav()
        }
    }
}
