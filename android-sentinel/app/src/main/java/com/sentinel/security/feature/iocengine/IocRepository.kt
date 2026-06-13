package com.sentinel.security.feature.iocengine

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

@Serializable
data class IocPackage(
    val `package`: String,
    val label: String,
    val category: String = "stalkerware",
)

@Serializable
data class IocCert(
    val sha256: String,
    val label: String,
)

@Serializable
data class IocDataset(
    val schemaVersion: Int = 1,
    val source: String = "",
    val license: String = "",
    val note: String = "",
    val packages: List<IocPackage> = emptyList(),
    val signingCertSha256: List<IocCert> = emptyList(),
)

data class IocMatch(val label: String, val category: String)

/**
 * Loads the bundled stalkerware indicator set (Echap, CC-BY-4.0). Designed so the dataset can be
 * replaced/augmented by a downloaded feed later; matching is by package name and signing-cert
 * SHA-256. Behavioural detection lives in the scanner and does not need this list.
 */
@Singleton
class IocRepository @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val json = Json { ignoreUnknownKeys = true }

    @Volatile
    private var cached: IocDataset? = null

    fun dataset(): IocDataset {
        cached?.let { return it }
        return synchronized(this) {
            cached ?: load().also { cached = it }
        }
    }

    private fun load(): IocDataset = runCatching {
        context.assets.open("ioc/stalkerware_indicators.json").use { stream ->
            json.decodeFromString<IocDataset>(stream.readBytes().decodeToString())
        }
    }.getOrDefault(IocDataset())

    fun matchPackage(packageName: String): IocMatch? =
        dataset().packages.firstOrNull { it.`package`.equals(packageName, ignoreCase = true) }
            ?.let { IocMatch(it.label, it.category) }

    fun matchCert(sha256: String): IocMatch? =
        dataset().signingCertSha256.firstOrNull { it.sha256.equals(sha256, ignoreCase = true) }
            ?.let { IocMatch(it.label, "stalkerware") }
}
