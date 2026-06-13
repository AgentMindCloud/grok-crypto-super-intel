package com.sentinel.security.core.scan

import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity
import com.sentinel.security.core.score.SpyRiskScore
import com.sentinel.security.core.score.SpyRiskScoreEngine
import com.sentinel.security.data.EventLogRepository
import com.sentinel.security.data.EventType
import com.sentinel.security.data.db.FindingEntity
import com.sentinel.security.data.db.ScanDao
import com.sentinel.security.data.db.ScanEntity
import javax.inject.Inject
import javax.inject.Singleton

data class ScanResult(
    val scanId: Long,
    val score: SpyRiskScore,
    val findings: List<Finding>,
)

/** Stage progress for the self-ticking scan timeline in the UI. */
data class ScanStage(val title: String, val done: Boolean)

@Singleton
class ScanRunner @Inject constructor(
    private val detectors: Set<@JvmSuppressWildcards Detector>,
    private val scanDao: ScanDao,
    private val eventLog: EventLogRepository,
) {
    /** Detector titles, for rendering the scan timeline before running. */
    fun stages(): List<String> = detectors.map { it.title }

    suspend fun runFullScan(onStage: (ScanStage) -> Unit = {}): ScanResult {
        val started = System.currentTimeMillis()
        val pillarsChecked = mutableSetOf<Pillar>()
        val findings = mutableListOf<Finding>()

        for (detector in detectors) {
            val result = runCatching { detector.detect() }.getOrDefault(emptyList())
            findings += result
            pillarsChecked += detector.pillars
            onStage(ScanStage(detector.title, done = true))
        }

        val score = SpyRiskScoreEngine.compute(findings, pillarsChecked)
        val finished = System.currentTimeMillis()

        val scan = ScanEntity(
            startedAtEpochMs = started,
            finishedAtEpochMs = finished,
            overallScore = score.overall,
            band = score.band.name,
            findingCount = findings.size,
            pillarsChecked = pillarsChecked.joinToString(",") { it.name },
        )
        val scanId = scanDao.saveScan(scan) { id -> findings.map { it.toEntity(id) } }

        eventLog.log(
            EventType.SCAN_COMPLETED,
            "Full scan: score ${score.overall} (${score.band.label}), ${findings.size} findings",
        )
        val worst = findings.maxByOrNull { it.severity.rank }
        if (worst != null && worst.severity.rank >= Severity.HIGH.rank) {
            eventLog.log(EventType.THREAT_FOUND, "${worst.severity.label}: ${worst.title}")
        }

        return ScanResult(scanId, score, findings)
    }

    private fun Finding.toEntity(scanId: Long) = FindingEntity(
        scanId = scanId,
        findingKey = id,
        pillar = pillar.name,
        severity = severity.name,
        title = title,
        explanation = explanation,
        whatItCanSee = whatItCanSee,
        packageName = packageName,
        confirmed = confirmed,
        matchLabel = matchLabel,
        detectedAtEpochMs = detectedAtEpochMs,
    )
}
