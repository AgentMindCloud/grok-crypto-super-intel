package com.sentinel.security

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class SentinelApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = getSystemService(NotificationManager::class.java) ?: return
        val channels = listOf(
            NotificationChannel(
                CHANNEL_THREATS,
                "Threat alerts",
                NotificationManager.IMPORTANCE_HIGH,
            ).apply { description = "Stalkerware, trackers and intrusion alerts" },
            NotificationChannel(
                CHANNEL_MONITOR,
                "Background monitoring",
                NotificationManager.IMPORTANCE_LOW,
            ).apply { description = "Ongoing tracker / intrusion / firewall monitors" },
            NotificationChannel(
                CHANNEL_DIGEST,
                "Weekly digest",
                NotificationManager.IMPORTANCE_DEFAULT,
            ).apply { description = "Weekly security summary" },
        )
        nm.createNotificationChannels(channels)
    }

    companion object {
        const val CHANNEL_THREATS = "threats"
        const val CHANNEL_MONITOR = "monitor"
        const val CHANNEL_DIGEST = "digest"
    }
}
