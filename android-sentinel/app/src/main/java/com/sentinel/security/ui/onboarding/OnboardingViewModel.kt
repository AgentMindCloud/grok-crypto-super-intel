package com.sentinel.security.ui.onboarding

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sentinel.security.core.permissions.SpecialAccess
import com.sentinel.security.core.permissions.SpecialAccessManager
import com.sentinel.security.core.scan.ScanResult
import com.sentinel.security.core.scan.ScanRunner
import com.sentinel.security.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AccessState(val access: SpecialAccess, val granted: Boolean)

data class OnboardingUiState(
    val ethicsAccepted: Boolean = false,
    val scanning: Boolean = false,
    val baseline: ScanResult? = null,
    val access: List<AccessState> = emptyList(),
)

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val settings: SettingsRepository,
    private val scanRunner: ScanRunner,
    private val accessManager: SpecialAccessManager,
) : ViewModel() {

    private val _state = MutableStateFlow(OnboardingUiState(access = readAccess()))
    val state: StateFlow<OnboardingUiState> = _state.asStateFlow()

    fun acceptEthics() {
        _state.update { it.copy(ethicsAccepted = true) }
        viewModelScope.launch { settings.setEthicsAccepted(true) }
    }

    fun runBaselineScan() {
        if (_state.value.scanning) return
        _state.update { it.copy(scanning = true) }
        viewModelScope.launch {
            val result = scanRunner.runFullScan()
            _state.update { it.copy(scanning = false, baseline = result) }
        }
    }

    /** Re-reads grant state — call when the screen resumes after a Settings round-trip. */
    fun refreshAccess() {
        _state.update { it.copy(access = readAccess()) }
    }

    fun settingsIntent(access: SpecialAccess) = accessManager.settingsIntent(access)

    fun finish() {
        viewModelScope.launch { settings.setOnboardingComplete(true) }
    }

    private fun readAccess(): List<AccessState> =
        SpecialAccess.entries.map { AccessState(it, accessManager.isGranted(it)) }
}
