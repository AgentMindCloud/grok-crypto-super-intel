package com.sentinel.security

import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity
import com.sentinel.security.core.score.PostureBand
import com.sentinel.security.core.score.SpyRiskScoreEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SpyRiskScoreEngineTest {

    private fun finding(pillar: Pillar, severity: Severity) = Finding(
        id = "$pillar-$severity",
        pillar = pillar,
        severity = severity,
        title = "t",
        explanation = "e",
    )

    @Test
    fun noFindings_isSecure() {
        val score = SpyRiskScoreEngine.compute(emptyList(), setOf(Pillar.APPS))
        assertEquals(100, score.overall)
        assertEquals(PostureBand.SECURE, score.band)
    }

    @Test
    fun criticalFinding_dragsOverallDown() {
        val findings = listOf(finding(Pillar.APPS, Severity.CRITICAL))
        val score = SpyRiskScoreEngine.compute(findings, setOf(Pillar.APPS, Pillar.NETWORK))
        assertTrue("Critical should put us at risk", score.overall < 55)
    }

    @Test
    fun oneRedPillar_isNotMaskedByGreens() {
        // One critical apps finding; all other pillars clean. The bias-to-minimum must keep the
        // overall meaningfully below a naive average of the pillar scores.
        val findings = listOf(finding(Pillar.APPS, Severity.CRITICAL))
        val allPillars = Pillar.entries.toSet()
        val score = SpyRiskScoreEngine.compute(findings, allPillars)
        val naiveAverage = score.pillars.map { it.score }.average()
        assertTrue(
            "Overall (${score.overall}) should be pulled below the naive average ($naiveAverage)",
            score.overall < naiveAverage,
        )
    }

    @Test
    fun worstFindingDominatesPillar_tailIsDamped() {
        val many = List(10) { finding(Pillar.PERMISSIONS, Severity.INFO) }
        val score = SpyRiskScoreEngine.compute(many, setOf(Pillar.PERMISSIONS))
        val permissions = score.pillars.first { it.pillar == Pillar.PERMISSIONS }
        // Ten INFOs should not crater the pillar the way a single HIGH would.
        assertTrue("Many infos stay relatively safe", permissions.score > 70)
    }
}
