# Change Location on Tinder for Android

A step-by-step guide to changing your location on Tinder using an Android device.

---

## Overview

Tinder uses your device's GPS to determine your location and show you nearby matches. By using Android's **Mock Location** feature (available in Developer Options), you can set a fake GPS location without physically moving, allowing Tinder to detect a different location.

> **Note:** This guide is for educational purposes. Spoofing your location may violate Tinder's Terms of Service. Use responsibly.

---

## Prerequisites

- Android device (Android 6.0 or later)
- A mock GPS app (e.g., [Fake GPS Location](https://play.google.com/store/apps/details?id=com.lexa.fakegps) from the Google Play Store)
- Developer Options enabled on your device

---

## Step 1 – Enable Developer Options

1. Open the **Settings** app on your Android device.
2. Scroll down and tap **About phone**.
3. Find **Build number** (it may be under "Software information" on some devices).
4. Tap **Build number** seven (7) times in a row. You will see a message: _"You are now a developer!"_
5. Go back to the main **Settings** screen. **Developer options** will now appear in the menu (usually near the bottom, sometimes inside **System**).

---

## Step 2 – Install a Mock GPS App

1. Open the **Google Play Store**.
2. Search for a mock GPS app such as **Fake GPS Location** or **Mock Locations**.
3. Download and install the app.

---

## Step 3 – Set the Mock Location App in Developer Options

1. Open **Settings** → **Developer options**.
2. Scroll down to find **Select mock location app**.
3. Tap it and select the fake GPS app you just installed (e.g., **Fake GPS Location**).

---

## Step 4 – Set Your Fake Location

1. Open the **Fake GPS** app.
2. Use the map or search bar to navigate to the city/location you want Tinder to see.
3. Tap the **Play** button (▶) to start spoofing your location. The app will confirm that it is active.

---

## Step 5 – Update Your Location on Tinder

1. Open **Tinder**.
2. Tinder reads your GPS location when you open the app or update your location. It should now pick up the fake location you set.
3. To manually trigger a location refresh:
   - Go to **Profile** → **Settings**.
   - Scroll to **Location** and tap it.
   - Select **While Using the App** to allow Tinder to access your location.
4. Your Tinder matches will now be based on the spoofed location.

---

## Step 6 – Stop the Fake Location (When Done)

1. Return to the **Fake GPS** app.
2. Tap the **Stop** button (■) to stop location spoofing.
3. Your device will revert to its real GPS location.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Tinder still shows my real location | Force-close Tinder and reopen it after starting the fake GPS. |
| "Mock location app not found" in Developer options | Make sure the fake GPS app is fully installed and try rebooting your device. |
| Mock location option is greyed out | Ensure Developer options are enabled and you have selected a mock location app. |
| The fake GPS app requires root | Use a non-root mock GPS app from the Play Store; most modern ones do not require root. |

---

## Notes

- **Tinder Gold / Passport**: If you have a Tinder Gold or Platinum subscription, you can change your location natively within Tinder using the **Passport** feature without needing a mock location app.
- **Location accuracy**: Some apps may show your location slightly off. Try adjusting the pin on the map for more precision.
- **Battery**: Mock GPS apps run in the background and may consume additional battery.

---

## References

- [Android Developer Options – Official Documentation](https://developer.android.com/studio/debug/dev-options)
- [Tinder Help – Location Settings](https://www.help.tinder.com/hc/en-us/articles/115003359906)
