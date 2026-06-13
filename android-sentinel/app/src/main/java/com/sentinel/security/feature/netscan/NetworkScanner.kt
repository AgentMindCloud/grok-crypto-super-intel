package com.sentinel.security.feature.netscan

import android.content.Context
import android.net.ConnectivityManager
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import java.net.Inet4Address
import java.net.InetAddress
import javax.inject.Inject
import javax.inject.Singleton

data class DiscoveredDevice(
    val ip: String,
    val hostname: String?,
    val isSelf: Boolean,
    val isGateway: Boolean,
)

sealed interface NetworkScanOutcome {
    data class Success(val subnet: String, val devices: List<DiscoveredDevice>) : NetworkScanOutcome
    data class Failure(val reason: String) : NetworkScanOutcome
}

/**
 * Active LAN discovery. Android blocks /proc/net/arp on 10+, so we derive our subnet from
 * [ConnectivityManager] link properties and probe each host with ICMP/[InetAddress.isReachable],
 * then reverse-resolve hostnames. This finds devices that respond; it can't see silent hosts.
 */
@Singleton
class NetworkScanner @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    suspend fun scan(): NetworkScanOutcome = withContext(Dispatchers.IO) {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = cm.activeNetwork ?: return@withContext NetworkScanOutcome.Failure("No active network")
        val lp = cm.getLinkProperties(network) ?: return@withContext NetworkScanOutcome.Failure("No link info")

        val ownAddr = lp.linkAddresses
            .map { it.address }
            .filterIsInstance<Inet4Address>()
            .firstOrNull { !it.isLoopbackAddress }
            ?: return@withContext NetworkScanOutcome.Failure("No IPv4 address (Wi-Fi off?)")

        val ownIp = ownAddr.hostAddress ?: return@withContext NetworkScanOutcome.Failure("No IP")
        val gatewayIp = lp.routes.firstOrNull { it.isDefaultRoute }?.gateway
            ?.let { (it as? Inet4Address)?.hostAddress }

        val base = ownIp.substringBeforeLast('.') // assume /24
        val devices = coroutineScope {
            (1..254).map { host ->
                async {
                    val ip = "$base.$host"
                    val reachable = runCatching {
                        InetAddress.getByName(ip).isReachable(350)
                    }.getOrDefault(false)
                    if (!reachable) return@async null
                    val hostname = runCatching {
                        InetAddress.getByName(ip).canonicalHostName.takeIf { it != ip }
                    }.getOrNull()
                    DiscoveredDevice(
                        ip = ip,
                        hostname = hostname,
                        isSelf = ip == ownIp,
                        isGateway = ip == gatewayIp,
                    )
                }
            }.awaitAll().filterNotNull()
        }.sortedBy { it.ip.substringAfterLast('.').toIntOrNull() ?: 0 }

        NetworkScanOutcome.Success(subnet = "$base.0/24", devices = devices)
    }
}
