package com.sentinel.security.feature.breachmon

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface BreachResult {
    data object Idle : BreachResult
    data object Loading : BreachResult
    data class Found(val count: Int) : BreachResult
    data object Safe : BreachResult
    data class Error(val message: String) : BreachResult
}

@HiltViewModel
class BreachCheckViewModel @Inject constructor(
    private val client: PwnedPasswordsClient,
) : ViewModel() {

    private val _result = MutableStateFlow<BreachResult>(BreachResult.Idle)
    val result: StateFlow<BreachResult> = _result.asStateFlow()

    fun check(password: String) {
        if (password.isEmpty()) return
        _result.update { BreachResult.Loading }
        viewModelScope.launch {
            client.timesPwned(password).fold(
                onSuccess = { count ->
                    _result.value = if (count > 0) BreachResult.Found(count) else BreachResult.Safe
                },
                onFailure = { _result.value = BreachResult.Error(it.message ?: "Network error") },
            )
        }
    }

    fun reset() { _result.value = BreachResult.Idle }
}
