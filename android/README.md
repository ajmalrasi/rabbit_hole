# Rabbit Hole — Android

The Android client for [Rabbit Hole](../README.md). It surfaces the daily curated
feed, full rabbit-hole explainers, topic browsing, search, and saved items — with
an offline-first cache so previously loaded content is available without a network.

## Stack

- **Kotlin** + **Jetpack Compose** (Material 3, custom editorial theme)
- **Target:** Android 16 (API 36.1) · **Min:** Android 8.0 (API 26)
- **Networking:** Retrofit + OkHttp + kotlinx.serialization
- **Local cache:** Room (feed, details, categories, search, favorites)
- **DI:** Hilt
- **Settings:** DataStore (configurable API base URL)

## Architecture

```
ui (Compose screens + ViewModels)
  └── data/repository (RabbitHoleRepository — network-first, cache fallback)
        ├── data/remote (Retrofit RabbitHoleApi, DTOs)
        └── data/local  (Room database, DAOs, entities)
```

Each repository call hits the API, writes results to Room, and transparently falls
back to the cached copy when the network is unavailable.

## Build & run

Requirements: Android Studio (Narwhal 3 Feature Drop / 2025.1.3 or newer) with the
Android 16 (API 36.1) SDK platform and build-tools `36.1.0` installed.

```bash
# from the android/ directory
./gradlew :app:assembleDebug          # build the debug APK
./gradlew installDebug                # install on a connected device/emulator
```

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`.

Or open the `android/` folder directly in Android Studio and run the `app`
configuration.

## API configuration

The default backend URL is `http://192.168.3.30:8000` (set via
`API_BASE_URL` in [`app/build.gradle.kts`](app/build.gradle.kts)). It can be
changed at runtime in the app's **Settings** tab — useful for pointing at a local
dev server (`http://10.0.2.2:8000` from the emulator). Cleartext HTTP is permitted
only for the LAN/dev hosts listed in
[`network_security_config.xml`](app/src/main/res/xml/network_security_config.xml).

## Endpoints consumed

| Screen | Endpoint |
| ------ | -------- |
| Feed | `GET /feed` |
| Detail | `GET /rabbit-hole/{id}` |
| Topics | `GET /categories` |
| Search | `GET /search?q=&semantic=` |
