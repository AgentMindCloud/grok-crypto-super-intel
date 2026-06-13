package com.sentinel.security.feature.usageanomaly

import android.app.usage.NetworkStats
import android.app.usage.NetworkStatsManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.os.Build
import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity
import com.sentinel.security.core.permissions.SpecialAccess
import com.sentinel.security.core.permissions.SpecialAccessManager
import com.sentinel.security.core.scan.Detector
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Flags apps that hold surveillance permissions and move a notable amount of network data — a soft
 * signal for exfiltration. Requires Usage access (PACKAGE_USAGE_STATS); if not granted it emits a
 * single informational nudge rather than silently claiming the area is clean.
 */
class UsageAnomalyDetector @Inject constructor(
    @ApplicationContext private val context: Context,
    private val accessManager: SpecialAccessManager,
) : Detector {

    override val title: String = "Data & usage anomaly check"
    override val pillars: Set<Pillar> = setOf(Pillar.NETWORK)

    override suspend fun detect(): List<Finding> = withContext(Dispatchers.Default) {
        if (!accessManager.isGranted(SpecialAccess.USAGE_ACCESS)) {
            return@withContext listOf(
                Finding(
                    id = "usage:nogrant",
                    pillar = Pillar.NETWORK,
                    severity = Severity.INFO,
                    title = "Grant Usage access for data-anomaly checks",
                    explanation = "With Usage access, Sentinel can spot apps that quietly move a lot of data — a common exfiltration sign.",
                    confirmed = false,
                ),
            )
        }

        val perUid = runCatching { perUidBytes() }.getOrDefault(emptyMap())
        if (perUid.isEmpty()) return@withContext emptyList()

        val pm = context.packageManager
        val findings = mutableListOf<Finding>()
        // Look only at the heaviest few non-system apps that also hold surveillance permissions.
        perUid.entries.sortedByDescending { it.value }.take(12).forEach { (uid, bytes) ->
            if (bytes < THRESHOLD_BYTES) return@forEach
            val pkgs = pm.getPackagesForUid(uid) ?: return@forEach
            val pkg = pkgs.firstOrNull() ?: return@forEach
            val appInfo = runCatching { pm.getApplicationInfo(pkg, 0) }.getOrNull() ?: return@forEach
            val isSystem = appInfo.flags and ApplicationInfo.FLAG_SYSTEM != 0
            if (isSystem) return@forEach
            if (!holdsSurveillancePerm(pm, pkg)) return@forEach
            val label = runCatching { pm.getApplicationLabel(appInfo).toString() }.getOrDefault(pkg)
            findings += Finding(
                id = "usage:$pkg",
                pillar = Pillar.NETWORK,
                severity = Severity.INFO,
                title = "“$label” moved ${formatMb(bytes)} of data",
                explanation = "This app holds surveillance-capable permissions and transferred a notable amount of data recently. Confirm it's expected.",
                packageName = pkg,
                confirmed = false,
            )
        }
        findings
    }

    private fun perUidBytes(): Map<Int, Long> {
        val nsm = context.getSystemService(Context.NETWORK_STATS_SERVICE) as NetworkStatsManager
        val end = System.currentTimeMillis()
        val start = end - 7L * 24 * 60 * 60 * 1000
        val out = HashMap<Int, Long>()
        @Suppress("DEPRECATION")
        for (type in intArrayOf(ConnectivityManager.TYPE_WIFI, ConnectivityManager.TYPE_MOBILE)) {
            val stats = runCatching { nsm.querySummary(type, null, start, end) } .getOrNull() ?: continue
            val bucket = NetworkStats.Bucket()
            while (stats.hasNextBucket()) {
                stats.getNextBucket(bucket)
                out[bucket.uid] = (out[bucket.uid] ?: 0L) + bucket.rxBytes + bucket.txBytes
            }
            stats.close()
        }
        return out
    }

    private fun holdsSurveillancePerm(pm: PackageManager, pkg: String): Boolean {
        val info = runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.getPackageInfo(pkg, PackageManager.PackageInfoFlags.of(PackageManager.GET_PERMISSIONS.toLong()))
            } else {
                @Suppress("DEPRECATION")
                pm.getPackageInfo(pkg, PackageManager.GET_PERMISSIONS)
            }
        }.getOrNull() ?: return false
        val perms = info.requestedPermissions ?: return false
        return perms.any { it in SURVEILLANCE_PERMS }
    }

    private fun formatMb(bytes: Long): String = "%.1f MB".format(bytes / 1_000_000.0)

    private companion object {
        const val THRESHOLD_BYTES = 50L * 1_000_000 // 50 MB / week
        val SURVEILLANCE_PERMS = setOf(
            "android.permission.RECORD_AUDIO",
            "android.permission.CAMERA",
            "android.permission.ACCESS_FINE_LOCATION",
            "android.permission.READ_SMS",
            "android.permission.READ_CONTACTS",
            "android.permission.READ_CALL_LOG",
        )
    }
}
