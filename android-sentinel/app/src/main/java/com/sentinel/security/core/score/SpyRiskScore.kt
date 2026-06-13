package com.sentinel.security.core.score

import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity

/** Posture band for the dashboard ring (word + traffic-light, never color alone). */
enum class PostureBand(val label: String) {
    SECURE("Secure"),
    GUARDED("Guarded"),
    ELEVATED("Elevated"),
    AT_RISK("At risk"),
    CRITICAL("Critical");
}

data class PillarScore(
    val pillar: Pillar,
    val score: Int,           // 0..100, higher = safer
    val worstSeverity: Severity,
    val findingCount: Int,
)

data class SpyRiskScore(
    val overall: Int,         // 0..100, higher = safer
    val band: PostureBand,
    val pillars: List<PillarScore>,
    val checkedSomething: Boolean,
) {
    /** The single most important finding to surface, if any. */
    fun headline(findings: List<Finding>): Finding? =
        findings.maxByOrNull { it.severity.rank }?.takeIf { it.severity.rank >= Severity.WARN.rank }
}

/**
 * Computes the Spy Risk Score from the current findings.
 *
 * Design: each pillar starts at 100 and loses points per finding ([Severity.scorePenalty]),
 * with the worst single finding dominating (so many trivial infos don't sink a pillar, but one
 * critical does). The overall score is a *weighted minimum-biased* blend: we bias toward the
 * worst pillars by averaging each pillar's score with the global minimum, weighted by pillar
 * weight. This is transparent and explainable in the "how this is calculated" sheet.
 */
object SpyRiskScoreEngine {

    fun compute(findings: List<Finding>, pillarsChecked: Set<Pillar>): SpyRiskScore {
        val pillarScores = Pillar.entries.map { pillar ->
            val pf = findings.filter { it.pillar == pillar }
            val worst = pf.maxByOrNull { it.severity.rank }?.severity ?: Severity.OK
            // Worst finding dominates; additional findings add a damped tail.
            val worstPenalty = worst.scorePenalty
            val tail = pf.sortedByDescending { it.severity.rank }
                .drop(1)
                .sumOf { it.severity.scorePenalty } / 3
            val raw = 100 - worstPenalty - tail
            PillarScore(
                pillar = pillar,
                score = raw.coerceIn(0, 100),
                worstSeverity = worst,
                findingCount = pf.size,
            )
        }

        val considered = pillarScores.filter { it.pillar in pillarsChecked }
        val overall = if (considered.isEmpty()) {
            100
        } else {
            val globalMin = considered.minOf { it.score }
            val weightSum = considered.sumOf { it.pillar.weight.toDouble() }
            val weighted = considered.sumOf { ps ->
                // Bias each pillar halfway toward the global minimum so the worst pillar pulls
                // the overall down and cannot be masked by greens.
                val biased = (ps.score + globalMin) / 2.0
                biased * ps.pillar.weight
            }
            (weighted / weightSum).toInt().coerceIn(0, 100)
        }

        return SpyRiskScore(
            overall = overall,
            band = bandFor(overall),
            pillars = pillarScores,
            checkedSomething = pillarsChecked.isNotEmpty(),
        )
    }

    private fun bandFor(score: Int): PostureBand = when {
        score >= 90 -> PostureBand.SECURE
        score >= 75 -> PostureBand.GUARDED
        score >= 55 -> PostureBand.ELEVATED
        score >= 30 -> PostureBand.AT_RISK
        else -> PostureBand.CRITICAL
    }
}
