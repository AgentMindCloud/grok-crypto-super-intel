package com.sentinel.security.data.db

import com.sentinel.security.core.model.Finding
import com.sentinel.security.core.model.Pillar
import com.sentinel.security.core.model.Severity

fun FindingEntity.toDomain(): Finding = Finding(
    id = findingKey,
    pillar = runCatching { Pillar.valueOf(pillar) }.getOrDefault(Pillar.APPS),
    severity = runCatching { Severity.valueOf(severity) }.getOrDefault(Severity.INFO),
    title = title,
    explanation = explanation,
    whatItCanSee = whatItCanSee,
    packageName = packageName,
    confirmed = confirmed,
    matchLabel = matchLabel,
    detectedAtEpochMs = detectedAtEpochMs,
)

fun parsePillars(csv: String): Set<Pillar> =
    csv.split(",")
        .mapNotNull { name -> runCatching { Pillar.valueOf(name.trim()) }.getOrNull() }
        .toSet()
