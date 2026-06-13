package com.sentinel.security.feature.breachmon

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Checks a password against Have I Been Pwned's Pwned Passwords range API using k-anonymity:
 * only the first 5 hex chars of the SHA-1 hash are ever sent; the full hash/password never leaves
 * the device. Free, no API key. Returns how many breaches the password appears in (0 = not found).
 */
@Singleton
class PwnedPasswordsClient @Inject constructor() {

    suspend fun timesPwned(password: String): Result<Int> = withContext(Dispatchers.IO) {
        runCatching {
            val sha1 = sha1Hex(password).uppercase()
            val prefix = sha1.substring(0, 5)
            val suffix = sha1.substring(5)
            val url = URL("https://api.pwnedpasswords.com/range/$prefix")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 10_000
                readTimeout = 10_000
                setRequestProperty("Add-Padding", "true")
                setRequestProperty("User-Agent", "Sentinel-Android")
            }
            try {
                if (conn.responseCode != 200) error("HIBP returned ${conn.responseCode}")
                conn.inputStream.bufferedReader().useLines { lines ->
                    lines.forEach { line ->
                        val idx = line.indexOf(':')
                        if (idx > 0) {
                            val s = line.substring(0, idx)
                            if (s.equals(suffix, ignoreCase = true)) {
                                return@runCatching line.substring(idx + 1).trim().toIntOrNull() ?: 0
                            }
                        }
                    }
                }
                0
            } finally {
                conn.disconnect()
            }
        }
    }

    private fun sha1Hex(input: String): String =
        MessageDigest.getInstance("SHA-1").digest(input.toByteArray())
            .joinToString("") { "%02x".format(it) }
}
