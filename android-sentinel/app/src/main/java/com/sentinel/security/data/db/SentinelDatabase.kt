package com.sentinel.security.data.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [ScanEntity::class, FindingEntity::class, EventLogEntity::class],
    version = 1,
    exportSchema = false,
)
abstract class SentinelDatabase : RoomDatabase() {
    abstract fun scanDao(): ScanDao
    abstract fun eventLogDao(): EventLogDao

    companion object {
        const val NAME = "sentinel.db"
    }
}
