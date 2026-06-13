package com.sentinel.security.data

import com.sentinel.security.data.db.EventLogDao
import com.sentinel.security.data.db.EventLogEntity
import kotlinx.coroutines.flow.Flow
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Appends events to a hash-chained log. Each entry's hash covers the previous hash plus its own
 * fields, so any silent edit or deletion breaks [verifyChain] — giving exported reports a
 * "chain-of-custody feel" (not court-grade, but tamper-evident).
 */
@Singleton
class EventLogRepository @Inject constructor(
    private val dao: EventLogDao,
) {
    suspend fun log(type: EventType, message: String) {
        val prev = dao.last()
        val prevHash = prev?.hash ?: GENESIS
        val ts = System.currentTimeMillis()
        val hash = hash(prevHash, ts, type.name, message)
        dao.insert(
            EventLogEntity(
                timestampEpochMs = ts,
                type = type.name,
                message = message,
                prevHash = prevHash,
                hash = hash,
            ),
        )
    }

    fun recent(limit: Int = 100): Flow<List<EventLogEntity>> = dao.recent(limit)

    /** Recomputes the chain and returns true if every link is intact. */
    suspend fun verifyChain(): Boolean {
        var prevHash = GENESIS
        for (e in dao.all()) {
            if (e.prevHash != prevHash) return false
            val expected = hash(e.prevHash, e.timestampEpochMs, e.type, e.message)
            if (e.hash != expected) return false
            prevHash = e.hash
        }
        return true
    }

    private fun hash(prevHash: String, ts: Long, type: String, message: String): String {
        val md = MessageDigest.getInstance("SHA-256")
        val bytes = md.digest("$prevHash|$ts|$type|$message".toByteArray())
        return bytes.joinToString("") { "%02x".format(it) }
    }

    companion object {
        private const val GENESIS = "0000000000000000000000000000000000000000000000000000000000000000"
    }
}

enum class EventType {
    SCAN_COMPLETED,
    THREAT_FOUND,
    HARDENING_APPLIED,
    HONEYFILE_TRIPPED,
    TRACKER_FOLLOWING,
    INTRUSION_ALARM,
    PANIC_TRIGGERED,
    SETTINGS_CHANGED,
}
