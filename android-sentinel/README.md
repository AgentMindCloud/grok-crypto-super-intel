# Sentinel — personal Android anti-surveillance app

A defensive, **personal-use** security app for your own Android phone: detects stalkerware,
risky app access, device tampering and (in later phases) hidden trackers, network snooping and
physical bugs — and helps you harden the device. Native Kotlin + Jetpack Compose, sideloaded.

> **Ethics:** Sentinel is strictly for a device you own and use. It has no covert mode and never
> silently changes or removes other apps. Using monitoring tools on someone else's device without
> consent is illegal in many places — and is exactly the harm Sentinel exists to fight.

## Get it on your phone — no computer needed

Everything builds in the cloud (GitHub Actions); your phone only downloads and installs.

1. **One-time signing setup (from the GitHub mobile app):** Actions → **Android — Generate
   signing key** → *Run workflow*. Open the run's summary and copy the four values into
   **Settings → Secrets and variables → Actions**: `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`,
   `KEY_ALIAS`, `KEY_PASSWORD`. (Skip this and builds are debug-signed — fine to start.)
2. **Build:** Actions → **Android — Build Sentinel APK** → *Run workflow* (or it runs
   automatically on every push). It publishes the APK to a **GitHub Release**.
3. **Install:** open the Release on your phone, download the APK, allow "install unknown apps",
   tap install. Updates install over the top (stable signing key = no data loss).

## What works today (Phase 0–1)

- **One-tap forensic scan** with a self-ticking stage timeline.
- **Spy Risk Score** — a weighted "worst-of-pillars" posture ring (one red area can't hide behind
  green ones), with a per-pillar breakdown.
- **Anti-stalkerware app scan** (Tier A, no root): flags known indicators (Echap dataset, CC-BY)
  and apps that *behave* like stalkerware (Accessibility + Device Admin + hidden/sideloaded +
  surveillance permissions), plus screen-reading, notification-access and device-admin grants.
- **Guided onboarding** with a hard ethics gate and a no-permission baseline scan first, then a
  just-in-time permission unlock checklist (each pairs "why" with "what we still can't see").
- **Tamper-evident event log** (hash-chained) you can verify in-app.
- **Honest settings**: monitoring-intensity (battery tradeoff) slider, discreet mode, and a plain
  list of what Sentinel can and can't do.

## Roadmap (see `designs` / the plan)

Phase 2: per-app firewall (VpnService) + connection report-card, hardware-attestation tamper
check (Auditor-lite), LAN scan, canary honeyfiles, breach monitoring. Phase 3: BLE tracker radar,
mercenary-spyware forensic scan (bugreport/STIX2), signal/EM/audio "aid" tools. Phase 4: optional
Shizuku enforcement tier. Phase 5: companion-hardware (SDR) add-ons.

## Build locally (optional, needs Android SDK)

```
./gradlew :app:assembleDebug      # compile + build a debug APK
./gradlew :app:testReleaseUnitTest
```

## Honest limitations

Can't observe/block other apps' mic/camera/clipboard/screenshots without a Shizuku/root add-on;
a clean scan is not proof of a clean device; signal/EM/lens tools are aids, not proof; reports are
not court-grade. Detection-first by design.
