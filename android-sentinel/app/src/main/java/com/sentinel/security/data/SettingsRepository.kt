package com.sentinel.security.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "sentinel_settings")

/** Ongoing-monitor power profile; the honest battery/reliability tradeoff slider. */
enum class MonitorMode { BATTERY_SAVER, BALANCED, THOROUGH }

data class SentinelSettings(
    val ethicsAccepted: Boolean = false,
    val onboardingComplete: Boolean = false,
    val monitorMode: MonitorMode = MonitorMode.BALANCED,
    val discreetMode: Boolean = false,
    val alertEmail: String? = null,
)

@Singleton
class SettingsRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    val settings: Flow<SentinelSettings> = context.dataStore.data.map { p ->
        SentinelSettings(
            ethicsAccepted = p[ETHICS_ACCEPTED] ?: false,
            onboardingComplete = p[ONBOARDING_COMPLETE] ?: false,
            monitorMode = (p[MONITOR_MODE])?.let { runCatching { MonitorMode.valueOf(it) }.getOrNull() }
                ?: MonitorMode.BALANCED,
            discreetMode = p[DISCREET_MODE] ?: false,
            alertEmail = p[ALERT_EMAIL],
        )
    }

    suspend fun setEthicsAccepted(accepted: Boolean) =
        context.dataStore.edit { it[ETHICS_ACCEPTED] = accepted }

    suspend fun setOnboardingComplete(complete: Boolean) =
        context.dataStore.edit { it[ONBOARDING_COMPLETE] = complete }

    suspend fun setMonitorMode(mode: MonitorMode) =
        context.dataStore.edit { it[MONITOR_MODE] = mode.name }

    suspend fun setDiscreetMode(enabled: Boolean) =
        context.dataStore.edit { it[DISCREET_MODE] = enabled }

    suspend fun setAlertEmail(email: String?) =
        context.dataStore.edit { prefs ->
            if (email.isNullOrBlank()) prefs.remove(ALERT_EMAIL) else prefs[ALERT_EMAIL] = email
        }

    private companion object {
        val ETHICS_ACCEPTED = booleanPreferencesKey("ethics_accepted")
        val ONBOARDING_COMPLETE = booleanPreferencesKey("onboarding_complete")
        val MONITOR_MODE = stringPreferencesKey("monitor_mode")
        val DISCREET_MODE = booleanPreferencesKey("discreet_mode")
        val ALERT_EMAIL = stringPreferencesKey("alert_email")
    }
}
