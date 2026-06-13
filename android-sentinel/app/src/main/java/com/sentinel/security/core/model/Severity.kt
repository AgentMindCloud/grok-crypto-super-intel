package com.sentinel.security.core.model

/**
 * Severity scale shared across every detector. Ordered from benign to worst; [rank] is used to
 * take the "worst of" across findings, and [scorePenalty] feeds the Spy Risk Score.
 */
enum class Severity(val rank: Int, val scorePenalty: Int, val label: String) {
    OK(0, 0, "OK"),
    INFO(1, 2, "Info"),
    WARN(2, 12, "Caution"),
    HIGH(3, 35, "High risk"),
    CRITICAL(4, 60, "Critical");

    companion object {
        /** The more severe of two values. */
        fun max(a: Severity, b: Severity): Severity = if (a.rank >= b.rank) a else b
    }
}
