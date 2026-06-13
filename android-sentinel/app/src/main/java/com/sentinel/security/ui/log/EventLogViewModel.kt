package com.sentinel.security.ui.log

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sentinel.security.data.EventLogRepository
import com.sentinel.security.data.db.EventLogEntity
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class EventLogViewModel @Inject constructor(
    private val eventLog: EventLogRepository,
) : ViewModel() {

    val events: StateFlow<List<EventLogEntity>> = eventLog.recent()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private val _chainValid = MutableStateFlow<Boolean?>(null)
    val chainValid: StateFlow<Boolean?> = _chainValid.asStateFlow()

    fun verify() {
        viewModelScope.launch { _chainValid.value = eventLog.verifyChain() }
    }
}
