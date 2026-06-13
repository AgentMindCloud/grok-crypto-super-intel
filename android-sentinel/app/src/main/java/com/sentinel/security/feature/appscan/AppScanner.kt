package com.sentinel.security.feature.appscan

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageInfo
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity
import com.sentinel.security.core.scan.Detector
import com.sentinel.security.feature.iocengine.IocRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.security.MessageDigest
import javax.inject.Inject

/**
 * The core anti-stalkerware detector. Enumerates installed apps and flags:
 *  - known stalkerware (IOC package / signing-cert match),
 *  - apps that *behave* like stalkerware (Accessibility + Device Admin + hidden/sideloaded +
 *    surveillance permissions) — the strongest non-root signal, requiring no IOC list,
 *  - individual high-power grants (screen-reading Accessibility, notification access, device admin).
 *
 * Everything here is OS-backed fact (confirmed = true). Detection only; remediation is guided.
 */
class AppScanner @Inject constructor(
    @ApplicationContext private val context: Context,
    private val ioc: IocRepository,
) : Detector {

    override val title: String = "Apps & stalkerware scan"
    override val pillars: Set<Pillar> = setOf(Pillar.APPS, Pillar.PERMISSIONS)

    private val surveillancePerms = setOf(
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_CALL_LOG",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
        "android.permission.READ_CONTACTS",
        "android.permission.SYSTEM_ALERT_WINDOW",
    )

    override suspend fun detect(): List<Finding> = withContext(Dispatchers.Default) {
        val pm = context.packageManager
        val packages = installedPackages(pm)

        val accessibilityPkgs = enabledComponentsPackages(Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
        val notifListenerPkgs = enabledComponentsPackages("enabled_notification_listeners")
        val adminPkgs = activeAdminPackages()

        val findings = mutableListOf<Finding>()

        for (info in packages) {
            val app = info.applicationInfo ?: continue
            val pkg = info.packageName
            if (pkg == context.packageName) continue
            val isSystem = app.flags and ApplicationInfo.FLAG_SYSTEM != 0 ||
                app.flags and ApplicationInfo.FLAG_UPDATED_SYSTEM_APP != 0
            val label = runCatching { pm.getApplicationLabel(app).toString() }.getOrDefault(pkg)

            val hasAccessibility = pkg in accessibilityPkgs
            val isNotifListener = pkg in notifListenerPkgs
            val isAdmin = pkg in adminPkgs
            val hidden = pm.getLaunchIntentForPackage(pkg) == null
            val installer = installerOf(pm, pkg)
            val sideloaded = !isSystem && !isFromAppStore(installer)
            val requested = info.requestedPermissions?.toSet().orEmpty()
            val surveillance = requested.intersect(surveillancePerms)

            // 1) Known-IOC match (package or signing cert) — strongest, label it explicitly.
            val iocMatch = ioc.matchPackage(pkg)
                ?: signingCertSha256(pm, pkg)?.let { ioc.matchCert(it) }
            if (iocMatch != null && !isSystem) {
                findings += Finding(
                    id = "ioc:$pkg",
                    pillar = Pillar.APPS,
                    severity = if (iocMatch.category == "stalkerware") Severity.CRITICAL else Severity.HIGH,
                    title = "“$label” matches known monitoring software",
                    explanation = "This app matches the indicator “${iocMatch.label}” from the open stalkerware database. Review carefully before acting — see safe-removal guidance.",
                    whatItCanSee = "Apps like this typically capture messages, calls, location and screen activity.",
                    packageName = pkg,
                    matchLabel = iocMatch.label,
                )
                continue
            }

            // 2) Behavioural stalkerware signature (no IOC needed).
            if (!isSystem && hasAccessibility && (isAdmin || hidden) && surveillance.isNotEmpty()) {
                findings += Finding(
                    id = "behavior:$pkg",
                    pillar = Pillar.APPS,
                    severity = Severity.HIGH,
                    title = "“$label” behaves like stalkerware",
                    explanation = buildString {
                        append("This app can read your screen")
                        if (isAdmin) append(", controls device-admin policies")
                        if (hidden) append(", has no app icon")
                        if (sideloaded) append(", was installed outside an app store")
                        append(" and holds surveillance permissions. That combination is a classic stalkerware pattern.")
                    },
                    whatItCanSee = surveillanceSummary(surveillance),
                    packageName = pkg,
                )
                continue
            }

            // 3) Individual high-power grants worth surfacing.
            if (!isSystem && hasAccessibility) {
                findings += Finding(
                    id = "a11y:$pkg",
                    pillar = Pillar.PERMISSIONS,
                    severity = Severity.WARN,
                    title = "“$label” can read your screen",
                    explanation = "This app has an Accessibility service enabled, letting it observe and act on everything on screen. Only allow this for apps that genuinely need it.",
                    whatItCanSee = "On-screen text, taps and content across all apps.",
                    packageName = pkg,
                )
            }
            if (!isSystem && isNotifListener) {
                findings += Finding(
                    id = "notif:$pkg",
                    pillar = Pillar.PERMISSIONS,
                    severity = Severity.WARN,
                    title = "“$label” can read your notifications",
                    explanation = "This app has notification access and can read incoming notifications (messages, codes). Revoke it if unexpected.",
                    whatItCanSee = "Contents of your notifications, including message previews and OTP codes.",
                    packageName = pkg,
                )
            }
            if (!isSystem && isAdmin) {
                findings += Finding(
                    id = "admin:$pkg",
                    pillar = Pillar.PERMISSIONS,
                    severity = Severity.INFO,
                    title = "“$label” is a device administrator",
                    explanation = "This app holds device-admin powers (e.g. lock or wipe). Confirm you trust it.",
                    packageName = pkg,
                )
            }
        }

        findings
    }

    private fun installedPackages(pm: PackageManager): List<PackageInfo> {
        val flags = PackageManager.GET_PERMISSIONS
        return runCatching {
            @Suppress("DEPRECATION")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.getInstalledPackages(PackageManager.PackageInfoFlags.of(flags.toLong()))
            } else {
                pm.getInstalledPackages(flags)
            }
        }.getOrDefault(emptyList())
    }

    private fun installerOf(pm: PackageManager, pkg: String): String? = runCatching {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            pm.getInstallSourceInfo(pkg).installingPackageName
        } else {
            @Suppress("DEPRECATION")
            pm.getInstallerPackageName(pkg)
        }
    }.getOrNull()

    private fun isFromAppStore(installer: String?): Boolean = installer in APP_STORES

    private fun activeAdminPackages(): Set<String> = runCatching {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        dpm.activeAdmins?.map { it.packageName }?.toSet().orEmpty()
    }.getOrDefault(emptySet())

    private fun enabledComponentsPackages(secureKey: String): Set<String> {
        val value = Settings.Secure.getString(context.contentResolver, secureKey) ?: return emptySet()
        return value.split(":")
            .mapNotNull { it.substringBefore("/", "").takeIf(String::isNotBlank) }
            .toSet()
    }

    private fun signingCertSha256(pm: PackageManager, pkg: String): String? = runCatching {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            val info = pm.getPackageInfo(pkg, PackageManager.GET_SIGNING_CERTIFICATES)
            val signers = info.signingInfo?.apkContentsSigners ?: return null
            signers.firstOrNull()?.toByteArray()?.let(::sha256)
        } else {
            @Suppress("DEPRECATION")
            val info = pm.getPackageInfo(pkg, PackageManager.GET_SIGNATURES)
            @Suppress("DEPRECATION")
            info.signatures?.firstOrNull()?.toByteArray()?.let(::sha256)
        }
    }.getOrNull()

    private fun sha256(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }

    private fun surveillanceSummary(perms: Set<String>): String {
        val parts = mutableListOf<String>()
        if ("android.permission.RECORD_AUDIO" in perms) parts += "microphone"
        if ("android.permission.CAMERA" in perms) parts += "camera"
        if (perms.any { it.contains("SMS") }) parts += "text messages"
        if ("android.permission.READ_CALL_LOG" in perms) parts += "call logs"
        if (perms.any { it.contains("LOCATION") }) parts += "location"
        if ("android.permission.READ_CONTACTS" in perms) parts += "contacts"
        return if (parts.isEmpty()) "sensitive data" else "your " + parts.joinToString(", ")
    }

    private companion object {
        val APP_STORES = setOf(
            "com.android.vending",          // Google Play
            "com.google.android.feedback",
            "com.amazon.venezia",           // Amazon Appstore
            "com.sec.android.app.samsungapps", // Galaxy Store
            "com.huawei.appmarket",
            "org.fdroid.fdroid",            // F-Droid
        )
    }
}
