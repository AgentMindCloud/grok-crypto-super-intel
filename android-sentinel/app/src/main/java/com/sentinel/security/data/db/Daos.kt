package com.sentinel.security.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Transaction
import kotlinx.coroutines.flow.Flow

@Dao
interface ScanDao {
    @Insert
    suspend fun insertScan(scan: ScanEntity): Long

    @Insert
    suspend fun insertFindings(findings: List<FindingEntity>)

    @Transaction
    suspend fun saveScan(scan: ScanEntity, findings: (Long) -> List<FindingEntity>): Long {
        val id = insertScan(scan)
        insertFindings(findings(id))
        return id
    }

    @Query("SELECT * FROM scans ORDER BY finishedAtEpochMs DESC LIMIT 1")
    fun latestScan(): Flow<ScanEntity?>

    @Query("SELECT * FROM scans ORDER BY finishedAtEpochMs DESC LIMIT :limit")
    fun recentScans(limit: Int = 30): Flow<List<ScanEntity>>

    @Query("SELECT * FROM findings WHERE scanId = :scanId ORDER BY severity DESC")
    fun findingsForScan(scanId: Long): Flow<List<FindingEntity>>

    @Query("SELECT * FROM findings WHERE scanId = :scanId")
    suspend fun findingsForScanOnce(scanId: Long): List<FindingEntity>
}

@Dao
interface EventLogDao {
    @Insert
    suspend fun insert(event: EventLogEntity): Long

    @Query("SELECT * FROM event_log ORDER BY id DESC LIMIT 1")
    suspend fun last(): EventLogEntity?

    @Query("SELECT * FROM event_log ORDER BY id ASC")
    suspend fun all(): List<EventLogEntity>

    @Query("SELECT * FROM event_log ORDER BY id DESC LIMIT :limit")
    fun recent(limit: Int = 100): Flow<List<EventLogEntity>>
}
