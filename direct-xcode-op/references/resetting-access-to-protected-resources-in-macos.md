<!--
{
  "documentType" : "article",
  "framework" : "Xcode",
  "identifier" : "/documentation/Xcode/resetting-access-to-protected-resources-in-macOS",
  "metadataVersion" : "0.1.0",
  "role" : "article",
  "title" : "Resetting access to protected resources in macOS"
}
-->

# Resetting access to protected resources in macOS

Use Terminal to remove your app’s authorization access to protected resources during testing.

## Overview

The first time your app attempts to access a protected resource such as Reminders or the microphone,
the system prompts the person for permission. After the person grants or denies your app’s request for
access, the system remembers their choice. For more information, see <doc://com.apple.documentation/documentation/UIKit/requesting-access-to-protected-resources>.

During development, you might need the system to prompt the person for permission again — to test your
app’s onboarding experience, verify that your purpose strings appear correctly in every language you support,
or reproduce a bug that only occurs before the person grants access. To make the system prompt the person again,
use the `tccutil reset` command in Terminal. The `tccutil reset` command requires a service, each protected
resource has a service name. By default, the command affects only your current user account. To reset access
for all user accounts on your Mac, run the command with `sudo`. To learn more about `tccutil`, enter `man tccutil` in Terminal.

## Reset access

To reset access to a specific protected resource for every app, enter `tccutil reset` with the service
name:

```shell
% tccutil reset <service>
```

For example, the following command resets access to Calendar for every app:

```shell
% tccutil reset Calendar
```

The next time any app attempts to access Calendar, the system prompts the person for permission.

To reset access to a specific protected resource — in this case Calendar — for a single app, add the app’s bundle ID to the command:

```shell
% tccutil reset Calendar com.example.company
```

To reset access to all resources at once, pass `All` as the service name:

```shell
% tccutil reset All
```

The next time any app tries to access any protected resource, the system prompts the person for permission.

To reset access to all resources for a single app, add the app’s bundle ID:

```shell
% tccutil reset All com.example.company
```

## Look up a service name

The `<service>` argument accepts the following values. When applicable, each entry includes the privacy
usage description key to add to your app’s `Info.plist`.

- `All`: To reset access to every protected resource listed below.
- `Accessibility`: To reset access to Accessibility features.
- `AddressBook`: To reset access to Contacts. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSContactsUsageDescription>.
- `AppleEvents`: To reset access for sending Apple Events. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSAppleEventsUsageDescription>.
- `AudioCapture`: To reset access for capturing system audio. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSAudioCaptureUsageDescription>.
- `BluetoothAlways`: To reset access to Bluetooth. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSBluetoothAlwaysUsageDescription>.
- `Calendar`: To reset access to Calendar. Privacy usage description keys: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSCalendarsWriteOnlyAccessUsageDescription> and <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSCalendarsFullAccessUsageDescription>.
- `Camera`: To reset access to the camera. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSCameraUsageDescription>.
- `DeveloperTool`: To reset access to Developer Tools, which lets apps run code that is unsigned or noncompliant with the system’s security policy.
- `EnergyKitGuidance`: To reset access to EnergyKit for energy usage guidance and monitoring.
- `ExternalCameraMedia`: To reset access to external camera devices and their media content.
- `FileProviderDomain`: To reset access to files that a file provider manages. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSFileProviderDomainUsageDescription>.
- `FileProviderPresence`: To reset access for a file provider to determine which files the person is accessing. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSFileProviderPresenceUsageDescription>.
- `FocusStatus`: To reset access to a person’s focus status. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSFocusStatusUsageDescription>.
- `GameCenterFriends`: To reset access to the Game Center friends list. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSGKFriendListUsageDescription>.
- `HomeKit`: To reset access to HomeKit. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSHomeKitUsageDescription>.
- `ListenEvent`: To reset access to Input Monitoring.
- `MediaLibrary`: To reset access to the Apple Music library. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSAppleMusicUsageDescription>.
- `Microphone`: To reset access to the microphone. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSMicrophoneUsageDescription>.
- `Motion`: To reset access to the device’s motion data. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSMotionUsageDescription>.
- `Photos`: To reset access to Photos. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSPhotoLibraryUsageDescription>.
- `PhotosAdd`: To reset access for adding photos to the Photos library. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSPhotoLibraryAddUsageDescription>.
- `PostEvent`: To reset access for sending keystrokes.
- `Reminders`: To reset access to Reminders. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSRemindersFullAccessUsageDescription>.
- `RemoteDesktop`: To reset access to Remote Desktop.
- `ScreenCapture`: To reset access to Screen Recording.
- `Siri`: To reset access to Siri. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSSiriUsageDescription>.
- `SpeechRecognition`: To reset access to Speech Recognition. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSSpeechRecognitionUsageDescription>.
- `SystemPolicyAllFiles`: To reset access to all files (Full Disk Access).
- `SystemPolicyAppBundles`: To reset access to app bundles. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSAppBundlesUsageDescription>.
- `SystemPolicyAppData`: To reset access to files in other apps’ sandbox containers. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSAppDataUsageDescription>.
- `SystemPolicyDesktopFolder`: To reset access to files in the person’s Desktop folder. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSDesktopFolderUsageDescription>.
- `SystemPolicyDocumentsFolder`: To reset access to files in the person’s Documents folder. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSDocumentsFolderUsageDescription>.
- `SystemPolicyDownloadsFolder`: To reset access to files in the person’s Downloads folder. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSDownloadsFolderUsageDescription>.
- `SystemPolicyNetworkVolumes`: To reset access to files on a network volume. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSNetworkVolumesUsageDescription>.
- `SystemPolicyRemovableVolumes`: To reset access to files on a removable volume. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSRemovableVolumesUsageDescription>.
- `SystemPolicySysAdminFiles`: To reset access to system configuration files. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSSystemAdministrationUsageDescription>.
- `UserTracking`: To reset access to tracking data for the person or device. Privacy usage description key: <doc://com.apple.documentation/documentation/BundleResources/Information-Property-List/NSUserTrackingUsageDescription>.
- `VirtualMachineNetworking`: To reset access to networking for virtual machines.
- `VoiceBanking`: To reset access to Personal Voice and voice banking.
- `WebBrowserPublicKeyCredential`: To reset access to public key credentials (passkeys and WebAuthn) in web browsers.

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)