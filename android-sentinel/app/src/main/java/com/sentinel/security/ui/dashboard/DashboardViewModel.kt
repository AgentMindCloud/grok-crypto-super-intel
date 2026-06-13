package com.sentinel.security.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.score.SpyRiskScore
import com.sentinel.security.core.score.SpyRiskScoreEngine
import com.sentinel.security.core.scan.ScanRunner
import com.sentinel.security.data.db.ScanDao
import com.sentinel.security.data.db.parsePillars
import com.sentinel.security.data.db.toDomain
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val score: SpyRiskScore? = null,
    val findings: List<Finding> = emptyList(),
    val lastScanEpochMs: Long? = null,
    val hasScanned: Boolean = false,
)

data class ScanProgress(
    val running: Boolean = false,
    val completedStages: List<String> = emptyList(),
    val allStages: List<String> = emptyList(),
)

@OptIn(ExperimentalCoroutinesApi::class)
@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val scanDao: ScanDao,
    private val scanRunner: ScanRunner,
) : ViewModel() {

    val uiState: StateFlow<DashboardUiState> =
        scanDao.latestScan().flatMapLatest { scan ->
            if (scan == null) {
                flowOf(DashboardUiState(hasScanned = false))
            } else {
                scanDao.findingsForScan(scan.id).combine(flowOf(scan)) { findingEntities, s ->
                    val findings = findingEntities.map { it.toDomain() }
                    val score = SpyRiskScoreEngine.compute(findings, parsePillars(s.pillarsChecked))
                    DashboardUiState(
                        score = score,
                        findings = findings.sortedByDescending { it.severity.rank },
                        lastScanEpochMs = s.finishedAtEpochMs,
                        hasScanned = true,
                    )
                }
            }
        }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), DashboardUiState())

    private val _progress = MutableStateFlow(ScanProgress(allStages = scanRunner.stages()))
    val progress: StateFlow<ScanProgress> = _progress.asStateFlow()

    fun runScan() {
        if (_progress.value.running) return
        _progress.update { ScanProgress(running = true, completedStages = emptyList(), allStages = scanRunner.stages()) }
        viewModelScope.launch {
            scanRunner.runFullScan { stage ->
                _progress.update { it.copy(completedStages = it.completedStages + stage.title) }
            }
            _progress.update { it.copy(running = false) }
        }
    }
}
