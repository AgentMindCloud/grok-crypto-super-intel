package com.sentinel.security.core.model

/**
 * Security posture pillars. The dashboard shows a per-pillar breakdown and the overall Spy Risk
 * Score is a weighted "worst-of" across these, so one red pillar cannot hide behind green ones.
 */
enum class Pillar(val displayName: String, val weight: Float) {
    APPS("Apps & Stalkerware", 1.4f),
    PERMISSIONS("Permissions & Access", 1.2f),
    NETWORK("Network & Signals", 1.0f),
    DEVICE("Device Integrity", 1.2f),
    PHYSICAL("Physical & Trackers", 0.9f),
    EXPOSURE("Data Exposure", 0.8f);
}
