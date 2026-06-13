package com.sentinel.security.core.permissions

/**
 * The special accesses Sentinel can ask for, each independently grantable. Every card pairs a
 * plain "why" with an honest "what we still can't see", per the onboarding design. [runtime] marks
 * dangerous runtime permissions (requested via the permission launcher); the rest are special
 * accesses toggled in system Settings.
 */
enum class SpecialAccess(
    val title: String,
    val why: String,
    val cantSee: String,
    val runtime: Boolean = false,
    /** Manifest permission for [runtime] accesses; null for Settings-toggle accesses. */
    val runtimePermission: String? = null,
) {
    NOTIFICATIONS(
        title = "Show notifications",
        why = "So Sentinel can alert you the moment something looks wrong — a tracker following you, a new admin app, or a tripped honeyfile.",
        cantSee = "Granting this lets us notify you; it gives us no access to your other apps' notifications.",
        runtime = true,
        runtimePermission = "android.permission.POST_NOTIFICATIONS",
    ),
    USAGE_ACCESS(
        title = "Usage access",
        why = "Lets Sentinel spot battery, data and background-activity anomalies — a common stalkerware tell.",
        cantSee = "We see coarse per-app usage and data totals only — never the content of anything you do.",
    ),
    LOCATION(
        title = "Location (precise)",
        why = "Required by Android to scan Wi-Fi and confirm whether a Bluetooth tracker is actually following you across places.",
        cantSee = "We correlate tracker sightings to places on-device; your location never leaves the phone.",
        runtime = true,
        runtimePermission = "android.permission.ACCESS_FINE_LOCATION",
    ),
    NOTIFICATION_LISTENER(
        title = "Notification access",
        why = "Lets Sentinel audit which apps can read your notifications — a capability stalkerware abuses.",
        cantSee = "We use it to list and flag notification-reading apps; we don't store your notification contents.",
    ),
    BATTERY_UNRESTRICTED(
        title = "Run unrestricted in background",
        why = "Stops aggressive battery savers from silently killing the tracker and intrusion monitors.",
        cantSee = "This only affects Sentinel's own background reliability.",
    );
}
