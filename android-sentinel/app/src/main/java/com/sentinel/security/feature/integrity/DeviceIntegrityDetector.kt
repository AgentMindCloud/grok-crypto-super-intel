package com.sentinel.security.feature.integrity

import android.app.KeyguardManager
import android.content.Context
import android.os.Build
import android.provider.Settings
import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity
import com.sentinel.security.core.scan.Detector
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import javax.inject.Inject

/**
 * Device-integrity checks (Tier A, no root). Heuristic root/tamper detection plus a couple of
 * hardening signals (no screen lock, ADB left on). Root detection is an arms race, so these are
 * flagged as heuristic (confirmed = false) rather than definitive — Play Integrity / hardware
 * key-attestation would strengthen this and arrive with the Shizuku/network phase.
 */
class DeviceIntegrityDetector @Inject constructor(
    @ApplicationContext private val context: Context,
) : Detector {

    override val title: String = "Device integrity check"
    override val pillars: Set<Pillar> = setOf(Pillar.DEVICE)

    override suspend fun detect(): List<Finding> = withContext(Dispatchers.Default) {
        val findings = mutableListOf<Finding>()

        if (looksRooted()) {
            findings += Finding(
                id = "integrity:root",
                pillar = Pillar.DEVICE,
                severity = Severity.HIGH,
                title = "Device appears to be rooted",
                explanation = "Root indicators were found. Root removes the sandbox that protects you from spyware — only keep it if you understand the tradeoff. (Heuristic: determined root can hide.)",
                whatItCanSee = "Root access lets any granted app read every other app's private data.",
                confirmed = false,
            )
        }

        if (!isDeviceSecure()) {
            findings += Finding(
                id = "integrity:nolock",
                pillar = Pillar.DEVICE,
                severity = Severity.WARN,
                title = "No screen lock set",
                explanation = "Anyone with physical access can open your phone. Set a PIN, password or biometric lock.",
            )
        }

        if (isAdbEnabled()) {
            findings += Finding(
                id = "integrity:adb",
                pillar = Pillar.DEVICE,
                severity = Severity.INFO,
                title = "USB/wireless debugging is on",
                explanation = "ADB debugging is enabled. Turn it off when you're not using it — it widens the attack surface.",
            )
        }

        findings
    }

    private fun looksRooted(): Boolean {
        if (Build.TAGS?.contains("test-keys") == true) return true
        val suPaths = listOf(
            "/system/bin/su", "/system/xbin/su", "/sbin/su", "/su/bin/su",
            "/system/app/Superuser.apk", "/data/local/xbin/su", "/data/local/bin/su",
            "/data/local/su", "/system/bin/failsafe/su", "/system/sd/xbin/su",
        )
        if (suPaths.any { runCatching { File(it).exists() }.getOrDefault(false) }) return true
        val rootPackages = listOf(
            "com.topjohnwu.magisk", "eu.chainfire.supersu", "com.koushikdutta.superuser",
            "com.noshufou.android.su", "com.kingouser.com", "com.kingroot.kinguser",
        )
        val pm = context.packageManager
        return rootPackages.any { pkg ->
            runCatching {
                pm.getPackageInfo(pkg, 0); true
            }.getOrDefault(false)
        }
    }

    private fun isDeviceSecure(): Boolean = runCatching {
        val km = context.getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        km.isDeviceSecure
    }.getOrDefault(true)

    private fun isAdbEnabled(): Boolean = runCatching {
        Settings.Global.getInt(context.contentResolver, Settings.Global.ADB_ENABLED, 0) == 1
    }.getOrDefault(false)
}
