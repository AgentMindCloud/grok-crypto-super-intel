package com.sentinel.security.core.scan

import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar

/** A self-contained check that contributes findings to one or more pillars. */
interface Detector {
    val title: String

    /** Pillars this detector evaluates (so the score knows what was actually checked). */
    val pillars: Set<Pillar>

    /** Runs the check. Should never throw; return findings (possibly empty). */
    suspend fun detect(): List<Finding>
}
