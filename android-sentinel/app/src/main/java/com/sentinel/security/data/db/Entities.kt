package com.sentinel.security.data.db

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(tableName = "scans")
data class ScanEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val startedAtEpochMs: Long,
    val finishedAtEpochMs: Long,
    val overallScore: Int,
    val band: String,
    val findingCount: Int,
    /** Comma-separated pillar names that were actually evaluated in this scan. */
    val pillarsChecked: String,
)

@Entity(
    tableName = "findings",
    indices = [Index("scanId")],
)
data class FindingEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val scanId: Long,
    val findingKey: String,
    val pillar: String,
    val severity: String,
    val title: String,
    val explanation: String,
    val whatItCanSee: String?,
    val packageName: String?,
    val confirmed: Boolean,
    val matchLabel: String?,
    val detectedAtEpochMs: Long,
)

/**
 * Tamper-evident event log. Each row stores the hash of the previous row, forming a chain, so a
 * silently altered/deleted entry breaks verification — useful for evidence export.
 */
@Entity(tableName = "event_log")
data class EventLogEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val timestampEpochMs: Long,
    val type: String,
    val message: String,
    val prevHash: String,
    val hash: String,
)
