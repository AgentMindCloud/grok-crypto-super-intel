package com.sentinel.security.feature.breachmon

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sentinel.security.ui.components.SectionCard
import com.sentinel.security.ui.theme.SeverityCritical
import com.sentinel.security.ui.theme.SeverityOk

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BreachCheckScreen(onBack: () -> Unit, viewModel: BreachCheckViewModel = hiltViewModel()) {
    val result by viewModel.result.collectAsStateWithLifecycle()
    var password by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Password breach check") },
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
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            SectionCard {
                Text("Private by design", fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
                Text(
                    "Checks Have I Been Pwned. Only the first 5 characters of your password's hash are sent — the password itself never leaves your phone.",
                    fontSize = 13.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            OutlinedTextField(
                value = password,
                onValueChange = { password = it; viewModel.reset() },
                label = { Text("Password to check") },
                visualTransformation = PasswordVisualTransformation(),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            Button(
                onClick = { viewModel.check(password) },
                enabled = password.isNotEmpty() && result !is BreachResult.Loading,
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Check") }

            when (val r = result) {
                BreachResult.Idle -> {}
                BreachResult.Loading -> CircularProgressIndicator()
                BreachResult.Safe -> SectionCard {
                    Text("Not found in known breaches", color = SeverityOk, fontWeight = FontWeight.SemiBold)
                    Text("Still — never reuse passwords, and prefer a password manager.", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                is BreachResult.Found -> SectionCard {
                    Text("Seen in ${r.count} breaches", color = SeverityCritical, fontWeight = FontWeight.Bold)
                    Text("Stop using this password anywhere and change it now.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                }
                is BreachResult.Error -> SectionCard {
                    Text("Couldn't check: ${r.message}", color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }
}
