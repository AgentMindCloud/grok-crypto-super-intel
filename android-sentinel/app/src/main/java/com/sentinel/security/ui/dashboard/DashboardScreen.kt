package com.sentinel.security.ui.dashboard

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ListAlt
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.score.PillarScore
import com.sentinel.security.ui.components.RiskRing
import com.sentinel.security.ui.components.SectionCard
import com.sentinel.security.ui.components.SeverityBadge
import com.sentinel.security.ui.components.severityColor
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    onOpenLog: () -> Unit,
    onOpenSettings: () -> Unit,
    viewModel: DashboardViewModel = hiltViewModel(),
) {
    val ui by viewModel.uiState.collectAsStateWithLifecycle()
    val progress by viewModel.progress.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Sentinel") },
                actions = {
                    IconButton(onClick = onOpenLog) {
                        Icon(Icons.AutoMirrored.Filled.ListAlt, "Event log")
                    }
                    IconButton(onClick = onOpenSettings) {
                        Icon(Icons.Filled.Settings, "Settings")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Spacer(Modifier.height(8.dp))

            // Score ring / empty state
            if (ui.score != null) {
                RiskRing(
                    score = ui.score!!.overall,
                    bandLabel = ui.score!!.band.label,
                    subtitle = ui.lastScanEpochMs?.let { "Scanned ${relativeTime(it)}" },
                )
            } else {
                Box(Modifier.size(220.dp), contentAlignment = Alignment.Center) {
                    Text(
                        "Run your first scan",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 16.sp,
                    )
                }
            }

            // Run full scan + live stage timeline
            Button(
                onClick = viewModel::runScan,
                enabled = !progress.running,
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (progress.running) {
                    CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                    Spacer(Modifier.width(10.dp))
                    Text("Scanning…")
                } else {
                    Icon(Icons.Filled.Search, null)
                    Spacer(Modifier.width(8.dp))
                    Text("Run full forensic scan")
                }
            }

            if (progress.running) {
                StageTimeline(progress)
            }

            // Headline finding (threat state) or healthy summary
            val score = ui.score
            if (score != null) {
                val headline = score.headline(ui.findings)
                if (headline != null) {
                    HeadlineFinding(headline)
                } else if (ui.hasScanned) {
                    SectionCard {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.CheckCircle, null, tint = MaterialTheme.colorScheme.primary)
                            Spacer(Modifier.width(10.dp))
                            Text(
                                "No high-risk findings. Checked ${score.pillars.size} areas across ${ui.findings.size} signals.",
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                        }
                    }
                }

                // Pillar breakdown
                SectionCard {
                    Text("Posture by area", fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
                    score.pillars.forEach { PillarRow(it) }
                }

                // All findings
                if (ui.findings.isNotEmpty()) {
                    SectionCard {
                        Text("Findings (${ui.findings.size})", fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
                        ui.findings.forEach { FindingRow(it) }
                    }
                }
            }

            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun StageTimeline(progress: ScanProgress) {
    SectionCard {
        progress.allStages.forEach { stage ->
            val done = stage in progress.completedStages
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    if (done) Icons.Filled.CheckCircle else Icons.Filled.RadioButtonUnchecked,
                    null,
                    tint = if (done) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(18.dp),
                )
                Spacer(Modifier.width(10.dp))
                Text(stage, color = MaterialTheme.colorScheme.onSurface, fontSize = 14.sp)
            }
        }
    }
}

@Composable
private fun HeadlineFinding(finding: Finding) {
    SectionCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SeverityBadge(finding.severity)
            Spacer(Modifier.width(8.dp))
            if (!finding.confirmed) {
                Text("heuristic", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        Text(finding.title, fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.onSurface)
        Text(finding.explanation, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
        finding.whatItCanSee?.let {
            Text("What it can see: $it", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun PillarRow(pillar: PillarScore) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(pillar.pillar.displayName, color = MaterialTheme.colorScheme.onSurface, fontSize = 14.sp)
        Row(verticalAlignment = Alignment.CenterVertically) {
            SeverityBadge(pillar.worstSeverity)
            Spacer(Modifier.width(10.dp))
            Text("${pillar.score}", color = severityColorForScore(pillar.score), fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun FindingRow(finding: Finding) {
    Column(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier
                    .size(8.dp)
                    .padding(end = 0.dp),
            ) {
                Icon(
                    Icons.Filled.RadioButtonUnchecked,
                    null,
                    tint = severityColor(finding.severity),
                    modifier = Modifier.size(8.dp),
                )
            }
            Spacer(Modifier.width(10.dp))
            Text(finding.title, color = MaterialTheme.colorScheme.onSurface, fontSize = 14.sp, modifier = Modifier.weight(1f))
            SeverityBadge(finding.severity)
        }
        Text(finding.explanation, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(start = 18.dp))
    }
}

@Composable
private fun severityColorForScore(score: Int) = when {
    score >= 75 -> MaterialTheme.colorScheme.primary
    score >= 55 -> com.sentinel.security.ui.theme.SeverityWarn
    score >= 30 -> com.sentinel.security.ui.theme.SeverityHigh
    else -> com.sentinel.security.ui.theme.SeverityCritical
}

private fun relativeTime(epochMs: Long): String {
    val diff = System.currentTimeMillis() - epochMs
    return when {
        diff < 60_000 -> "just now"
        diff < 3_600_000 -> "${diff / 60_000} min ago"
        diff < 86_400_000 -> "${diff / 3_600_000} h ago"
        else -> DateFormat.getDateInstance(DateFormat.MEDIUM).format(Date(epochMs))
    }
}
