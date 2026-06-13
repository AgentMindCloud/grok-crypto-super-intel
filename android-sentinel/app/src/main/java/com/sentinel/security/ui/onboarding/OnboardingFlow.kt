package com.sentinel.security.ui.onboarding

import android.content.Intent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sentinel.security.core.permissions.SpecialAccess
import com.sentinel.security.ui.components.RiskRing
import com.sentinel.security.ui.components.SectionCard

private enum class Step { WELCOME, ETHICS, BASELINE, UNLOCK }

@Composable
fun OnboardingFlow(viewModel: OnboardingViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var step by remember { mutableStateOf(Step.WELCOME) }

    // Keep permission states fresh after Settings round-trips.
    LifecycleEventEffect(Lifecycle.Event.ON_RESUME) { viewModel.refreshAccess() }

    when (step) {
        Step.WELCOME -> WelcomeStep(onNext = { step = Step.ETHICS })
        Step.ETHICS -> EthicsStep(
            accepted = state.ethicsAccepted,
            onAccept = viewModel::acceptEthics,
            onNext = {
                step = Step.BASELINE
                viewModel.runBaselineScan()
            },
        )
        Step.BASELINE -> BaselineStep(state = state, onNext = { step = Step.UNLOCK })
        Step.UNLOCK -> UnlockStep(
            state = state,
            onGrantSettings = { access -> viewModel.settingsIntent(access) },
            onRefresh = viewModel::refreshAccess,
            onFinish = viewModel::finish,
        )
    }
}

@Composable
private fun StepScaffold(
    title: String,
    subtitle: String?,
    bottomBar: @Composable () -> Unit,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(title, fontSize = 28.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            if (subtitle != null) {
                Text(subtitle, fontSize = 15.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Spacer(Modifier.height(8.dp))
            content()
        }
        Spacer(Modifier.height(12.dp))
        bottomBar()
    }
}

@Composable
private fun WelcomeStep(onNext: () -> Unit) {
    StepScaffold(
        title = "Sentinel",
        subtitle = "A personal anti-surveillance toolkit for your own phone.",
        bottomBar = { Button(onClick = onNext, modifier = Modifier.fillMaxWidth()) { Text("Get started") } },
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(Icons.Filled.Shield, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.width(36.dp).height(36.dp))
            Spacer(Modifier.width(12.dp))
            Text("Detects stalkerware, hidden trackers, snooping and tampering — and helps you harden the phone.", color = MaterialTheme.colorScheme.onSurface)
        }
        SectionCard {
            Text("Our promises", fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
            Bullet("Your data stays on this device. Scans run locally.")
            Bullet("No hidden/covert mode. Sentinel is visible and honest about what it can and can't see.")
            Bullet("Detection first — we never silently change other apps or tip off an installer.")
        }
    }
}

@Composable
private fun EthicsStep(accepted: Boolean, onAccept: () -> Unit, onNext: () -> Unit) {
    StepScaffold(
        title = "This is your phone",
        subtitle = "Sentinel is strictly for protecting a device you own and use.",
        bottomBar = {
            Button(onClick = onNext, enabled = accepted, modifier = Modifier.fillMaxWidth()) {
                Text("I agree — continue")
            }
        },
    ) {
        SectionCard {
            Text(
                "The same capabilities that detect spying could be abused to spy on someone else. Using monitoring tools on another person's device without their knowledge is illegal in many places and is exactly the harm Sentinel exists to fight.",
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
            Checkbox(checked = accepted, onCheckedChange = { if (it) onAccept() })
            Text(
                "This is my own device and I will not use Sentinel to monitor anyone else.",
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@Composable
private fun BaselineStep(state: OnboardingUiState, onNext: () -> Unit) {
    StepScaffold(
        title = "Quick look",
        subtitle = "First, a baseline scan that needs no permissions at all.",
        bottomBar = {
            Button(onClick = onNext, enabled = state.baseline != null, modifier = Modifier.fillMaxWidth()) {
                Text("Continue")
            }
        },
    ) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
            if (state.scanning || state.baseline == null) {
                Spacer(Modifier.height(24.dp))
                CircularProgressIndicator()
                Spacer(Modifier.height(16.dp))
                Text("Scanning installed apps and access grants…", color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                val result = state.baseline
                RiskRing(score = result.score.overall, bandLabel = result.score.band.label)
                Spacer(Modifier.height(12.dp))
                Text(
                    if (result.findings.isEmpty()) {
                        "No obvious issues in this first pass."
                    } else {
                        "${result.findings.size} thing(s) worth a closer look."
                    },
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    "Unlock a few permissions next to go much deeper.",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontSize = 13.sp,
                )
            }
        }
    }
}

@Composable
private fun UnlockStep(
    state: OnboardingUiState,
    onGrantSettings: (SpecialAccess) -> Intent,
    onRefresh: () -> Unit,
    onFinish: () -> Unit,
) {
    val context = LocalContext.current
    val grantedCount = state.access.count { it.granted }

    StepScaffold(
        title = "Unlock deeper checks",
        subtitle = "Grant what you're comfortable with — each one is optional and independent. $grantedCount/${state.access.size} enabled.",
        bottomBar = {
            Button(onClick = onFinish, modifier = Modifier.fillMaxWidth()) {
                Text(if (grantedCount == 0) "Skip for now — go to dashboard" else "Done — go to dashboard")
            }
        },
    ) {
        // Runtime permission launcher (notifications, location).
        val permLauncher = rememberLauncherForActivityResult(
            ActivityResultContracts.RequestPermission(),
        ) { onRefresh() }

        state.access.forEach { item ->
            AccessCard(
                title = item.access.title,
                why = item.access.why,
                cantSee = item.access.cantSee,
                granted = item.granted,
                onGrant = {
                    if (item.access.runtime && item.access.runtimePermission != null) {
                        permLauncher.launch(item.access.runtimePermission)
                    } else {
                        context.startActivity(onGrantSettings(item.access))
                    }
                },
            )
        }
        TextButton(onClick = onRefresh) { Text("Refresh status") }
    }
}

@Composable
private fun AccessCard(
    title: String,
    why: String,
    cantSee: String,
    granted: Boolean,
    onGrant: () -> Unit,
) {
    SectionCard {
        Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text(title, fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface, modifier = Modifier.weight(1f))
            if (granted) {
                Icon(Icons.Filled.CheckCircle, "Granted", tint = MaterialTheme.colorScheme.primary)
            }
        }
        Text(why, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
        Text("What we still can't see: $cantSee", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        if (!granted) {
            OutlinedButton(onClick = onGrant) { Text("Grant") }
        }
    }
}

@Composable
private fun Bullet(text: String) {
    Row {
        Text("•  ", color = MaterialTheme.colorScheme.primary)
        Text(text, color = MaterialTheme.colorScheme.onSurface, fontSize = 14.sp)
    }
}
