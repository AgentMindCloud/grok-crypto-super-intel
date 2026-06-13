package com.sentinel.security.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sentinel.security.data.MonitorMode
import com.sentinel.security.data.SentinelSettings
import com.sentinel.security.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val repository: SettingsRepository,
) : ViewModel() {

    val settings: StateFlow<SentinelSettings> = repository.settings
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), SentinelSettings())

    fun setMonitorMode(mode: MonitorMode) = viewModelScope.launch { repository.setMonitorMode(mode) }
    fun setDiscreetMode(enabled: Boolean) = viewModelScope.launch { repository.setDiscreetMode(enabled) }
    fun setAlertEmail(email: String?) = viewModelScope.launch { repository.setAlertEmail(email) }
}
