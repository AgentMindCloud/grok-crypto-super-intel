package com.sentinel.security.feature.netscan

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class NetworkScanUiState(
    val scanning: Boolean = false,
    val outcome: NetworkScanOutcome? = null,
)

@HiltViewModel
class NetworkScanViewModel @Inject constructor(
    private val scanner: NetworkScanner,
) : ViewModel() {

    private val _state = MutableStateFlow(NetworkScanUiState())
    val state: StateFlow<NetworkScanUiState> = _state.asStateFlow()

    fun scan() {
        if (_state.value.scanning) return
        _state.value = NetworkScanUiState(scanning = true)
        viewModelScope.launch {
            val outcome = scanner.scan()
            _state.value = NetworkScanUiState(scanning = false, outcome = outcome)
        }
    }
}
