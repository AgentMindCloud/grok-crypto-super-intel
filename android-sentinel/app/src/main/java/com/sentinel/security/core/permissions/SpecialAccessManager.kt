package com.sentinel.security.core.permissions

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.os.Process
import android.provider.Settings
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Reads grant state for each [SpecialAccess] and builds the intent that takes the user to the
 * exact Settings screen to grant it. Pure read + intent construction; never mutates state.
 */
@Singleton
class SpecialAccessManager @Inject constructor(
    @ApplicationContext private val context: Context,
) {

    fun isGranted(access: SpecialAccess): Boolean = when (access) {
        SpecialAccess.NOTIFICATIONS ->
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                ContextCompat.checkSelfPermission(
                    context,
                    "android.permission.POST_NOTIFICATIONS",
                ) == android.content.pm.PackageManager.PERMISSION_GRANTED
            } else {
                NotificationManagerCompat.from(context).areNotificationsEnabled()
            }

        SpecialAccess.USAGE_ACCESS -> hasUsageAccess()

        SpecialAccess.LOCATION ->
            ContextCompat.checkSelfPermission(
                context,
                "android.permission.ACCESS_FINE_LOCATION",
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED

        SpecialAccess.NOTIFICATION_LISTENER -> hasNotificationListenerAccess()

        SpecialAccess.BATTERY_UNRESTRICTED -> {
            val pm = context.getSystemService(Context.POWER_SERVICE) as PowerManager
            pm.isIgnoringBatteryOptimizations(context.packageName)
        }
    }

    /** Settings intent to grant the access. Runtime permissions are handled by the UI launcher. */
    fun settingsIntent(access: SpecialAccess): Intent = when (access) {
        SpecialAccess.NOTIFICATIONS ->
            Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, context.packageName)

        SpecialAccess.USAGE_ACCESS ->
            Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)

        SpecialAccess.LOCATION ->
            appDetailsIntent()

        SpecialAccess.NOTIFICATION_LISTENER ->
            Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)

        @Suppress("BatteryLife")
        SpecialAccess.BATTERY_UNRESTRICTED ->
            Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
                .setData(Uri.parse("package:${context.packageName}"))
    }

    private fun appDetailsIntent(): Intent =
        Intent(
            Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
            Uri.fromParts("package", context.packageName, null),
        )

    private fun hasUsageAccess(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            appOps.unsafeCheckOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                context.packageName,
            )
        } else {
            @Suppress("DEPRECATION")
            appOps.checkOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                context.packageName,
            )
        }
        return mode == AppOpsManager.MODE_ALLOWED
    }

    private fun hasNotificationListenerAccess(): Boolean {
        val enabled = Settings.Secure.getString(
            context.contentResolver,
            "enabled_notification_listeners",
        ) ?: return false
        return enabled.split(":").any { it.contains(context.packageName) }
    }
}
