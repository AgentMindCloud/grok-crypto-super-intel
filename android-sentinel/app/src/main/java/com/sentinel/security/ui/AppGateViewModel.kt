package com.sentinel.security.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sentinel.security.data.SentinelSettings
import com.sentinel.security.data.SettingsRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class AppGateViewModel @Inject constructor(
    settingsRepository: SettingsRepository,
) : ViewModel() {
    // null = still loading from DataStore; non-null = resolved settings.
    val settings: StateFlow<SentinelSettings?> = settingsRepository.settings
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)
}
