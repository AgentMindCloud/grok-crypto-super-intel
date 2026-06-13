package com.sentinel.security.core.model

/**
 * A single result surfaced by a detector. [confirmed] distinguishes OS-backed facts (e.g. "this
 * app holds an Accessibility grant") from [confirmed]=false heuristic signals (e.g. "magnetometer
 * spike") so the UI can visually separate proof from aids, per the design's honesty rule.
 */
data class Finding(
    val id: String,
    val pillar: Pillar,
    val severity: Severity,
    val title: String,
    /** Plain-language explanation a non-technical owner can act on. */
    val explanation: String,
    /** What this means / what the matched thing can see, in plain words. */
    val whatItCanSee: String? = null,
    /** Package name when the finding concerns a specific app. */
    val packageName: String? = null,
    /** True = OS-backed fact; false = heuristic aid (label accordingly in UI). */
    val confirmed: Boolean = true,
    /** Optional named match, e.g. an IOC label like "mSpy". */
    val matchLabel: String? = null,
    val detectedAtEpochMs: Long = System.currentTimeMillis(),
)
