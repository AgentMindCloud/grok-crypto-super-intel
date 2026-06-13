package com.sentinel.security.feature.netscan

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sentinel.security.ui.components.SectionCard

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun NetworkScanScreen(onBack: () -> Unit, viewModel: NetworkScanViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Network scan") },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                "Finds devices that respond on your Wi-Fi. Devices that stay silent won't appear, and this is a snapshot — review anything you don't recognise.",
                fontSize = 13.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Button(
                onClick = viewModel::scan,
                enabled = !state.scanning,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (state.scanning) {
                    CircularProgressIndicator(modifier = Modifier.width(18.dp), strokeWidth = 2.dp)
                    Spacer(Modifier.width(10.dp))
                    Text("Scanning subnet…")
                } else {
                    Text("Scan my network")
                }
            }

            when (val outcome = state.outcome) {
                null -> {}
                is NetworkScanOutcome.Failure -> SectionCard {
                    Text("Couldn't scan: ${outcome.reason}", color = MaterialTheme.colorScheme.error)
                }
                is NetworkScanOutcome.Success -> {
                    Text(
                        "${outcome.devices.size} device(s) on ${outcome.subnet}",
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    outcome.devices.forEach { device ->
                        SectionCard {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(device.ip, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Medium)
                                when {
                                    device.isSelf -> Text("This phone", color = MaterialTheme.colorScheme.primary, fontSize = 12.sp)
                                    device.isGateway -> Text("Router", color = MaterialTheme.colorScheme.primary, fontSize = 12.sp)
                                    else -> {}
                                }
                            }
                            device.hostname?.let {
                                Text(it, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
            }
        }
    }
}
